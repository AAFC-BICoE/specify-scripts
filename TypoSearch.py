"""
Builds tree from geography or taxon table and searches for possible typos within and below a
specified rank. Possible typos are found by computing the Levenshtein Distance between every
name within the subtree and writing those that have a distance less than or equal to the specified
range to a report. If the taxon table is being searched, only names whose authors begin with the
same letter will be compared. Typo distance is case INSENSITIVE.
"""
import argparse
import datetime
import itertools
import pymysql
import Levenshtein
from anytree import PreOrderIter
from csvwriter import write_report
from specifytreebuilder import rank_dict, build_tree_without_nums, fetch_ranks

def check_author(author_letter_1, name1, author_letter_2, name2):
    # If first two letters of author is the same, the distance is returned
    if author_letter_1 == author_letter_2:
        return Levenshtein.distance(name1.lower(), name2.lower())
    return False

def find_taxon_typos(name1, name2, result_data, data, typo):
    # Handles the author first letter, creates and returns list of possible typos
    if (name1[2] is not None and name1[2] != "") and (name2[2] is not None and name2[2] != ""):
        if name1[2][0] == "(" or name1[2][0] == "[":
            distance = (check_author(name1[2][1], name1[0], name2[2][0], name2[0]))
        elif name2[2][0] == "(" or name2[2][0] == "[":
            distance = check_author(name1[2][0], name1[0], name2[2][1], name2[0])
        else:
            distance = check_author(name1[2][0], name1[0], name2[2][0], name2[0])
        if 0 < distance <= typo:
            result_data.append((data[1], name1[0], name2[0], name1[2],
                                name2[2], name1[1], name2[1], distance))
    elif (name1[2] is None and name2[2] is None) or (name1[2] == "" and name2[2] == ""):
        distance = check_author(name1[2], name1[0], name2[2], name2[0])
        if 0 < distance <= typo:
            result_data.append((data[1], name1[0], name2[0], name1[2],
                                name2[2], name1[1], name2[1], distance))
    return result_data

def search_tree_taxon(rank_records_dict, tree, rank, typo):
    # Iterates through taxon subtree, coordinates LD computation, returns possible typo list
    result_data = []
    rank_names = rank_records_dict[rank]
    for data in rank_names:
        for name1, name2 in itertools.combinations(
                ([node.name for node in PreOrderIter(tree[data[2]][2])]), 2):
            result_data = find_taxon_typos(name1, name2, result_data, data, typo)
    return result_data

def find_geography_typos(name_list, result_data, data, typo):
    # Computes LD and returns names if their LD is in the specified range
    for name1, name2 in name_list:
        distance = Levenshtein.distance(name1[0].lower(), name2[0].lower())
        if 0 < distance <= typo:
            result_data.append((data[1], name1[0], name2[0], name1[1], name2[1], distance))
    return result_data

def search_tree_geography(rank_records_dict, tree, database, rank, locality_toggle, typo):
    # Iterates through geography/locality subtree, coordinates LD computation, returns typo list
    db_locality_info = database.cursor()
    result_data = []
    rank_names = rank_records_dict[rank]
    for data in rank_names:
        if locality_toggle:
            locality_name = []
            for locality_node in ([node.name for node in PreOrderIter(tree[data[2]][2])]):
                db_locality_info.execute("SELECT LocalityName, LocalityID FROM locality "
                                         "WHERE GeographyID = %s" % locality_node[1])
                locality_name += ((locality[0], locality[1]) for locality in
                                  db_locality_info.fetchall() if
                                  (any(str.isdigit(c) for c in locality[0])) is False)
            name_list = itertools.combinations(locality_name, 2)
            result_data = find_geography_typos(name_list, result_data, data, typo)
        else:
            name_list = itertools.combinations(
                ([node.name for node in PreOrderIter((tree[data[2]][2]))]), 2)
            result_data = find_geography_typos(name_list, result_data, data, typo)
    return result_data

def taxon(database, table, rank_ids, rank, show, typo):
    # Builds taxon tree, coordinates report writing and typo search
    columns = "ParentID, FullName, TaxonID, Author"
    rank_dictionary = rank_dict(database, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, True)
    try:
        result_data = search_tree_taxon(rank_dictionary, tree, rank, typo)
    except KeyError:
        return print("Invalid rank")
    heading = ["Rank Name", "Name 1", "Name 2", "Author 1", "Author 2",
               "TaxonID 1", "TaxonID 2", "Levenshtein Distance"]
    return report(heading, result_data, show)

def geography(database, table, rank_ids, rank, locality_toggle, show, typo):
    # Builds geography/locality tree, coordinates report writing and typo search
    columns = "ParentID, FullName, GeographyID"
    rank_dictionary = rank_dict(database, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, False)
    try:
        result_data = search_tree_geography(rank_dictionary, tree, database,
                                            rank, locality_toggle, typo)
    except KeyError:
        return print("Invalid rank")
    headings = ["Rank Name", "Name 1", "Name 2", "GeographyID 1",
                "GeographyID 2", "Levenshtein Distance"]
    return report(headings, result_data, show)

def report(headings, result_data, show):
    # Writes report, prints possible typos to screen if specified
    file_name = "TypoReport[%s]" % (datetime.date.today())
    write_report(file_name, headings, result_data)
    if show:
        for row in result_data:
            print(row)
    print("Report saved as %s.csv" % file_name)

def main():
    # Creates command line arguments, coordinates functions
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username",
                        help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password",
                        help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="Name of MySQL specify database", required=True)
    parser.add_argument("-table", action="store", dest="table",
                        help="Name of table to search in", required=True)
    parser.add_argument("-rank", action="store", dest="rank",
                        help="Rank level to start searching in (INTEGER)", required=True)
    parser.add_argument("-typo_limit", action="store", dest="typo",
                        help="Maximum number of character DIFFERENCES between two names to be "
                             "considered a typo, EX: 'foo' and 'foos!' have a character difference "
                             "of 2 (INTEGER)", required=True)
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Displays duplicates found to screen")
    parser.add_argument("--locality", action="store_true", dest="locality",
                        help="Search locality table names")
    args = parser.parse_args()
    show = args.show
    table = args.table
    locality = args.locality
    rank = int(args.rank)
    typo = int(args.typo)
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    try:
        rank_ids = fetch_ranks(database, table)
    except pymysql.err.ProgrammingError:
        return print("%s is not a table in the schema" % table)
    if table == "taxon":
        return taxon(database, table, rank_ids, rank, show, typo)
    if table == "geography":
        locality_toggle = True if locality else False
        return  geography(database, table, rank_ids, rank, locality_toggle, show, typo)
    return print("Table %s not supported" % table)

if __name__ == "__main__":
    main()
