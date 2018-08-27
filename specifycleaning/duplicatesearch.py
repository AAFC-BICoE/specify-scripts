"""
Builds tree from geography or taxon table and searches for duplicate names within a specified
subtree. A report of the duplicates is created. If searching by taxon, only duplicate names that
have te same author first letters are flagged. If the optional argument 'locality' is specified
then a search of locality names is performed via joining the geographyID.
NOTE: RankID refers to the level of subtree that will be searched within. Searches performed in
the taxon tree are case sensitive,searches performed in the geography tree are case insensitive.
"""
import argparse
import datetime
import pymysql
from anytree import PreOrderIter
from specifycleaning.csvwriter import write_report
from specifycleaning.specifytreebuilder import rank_dict, build_tree_with_nums, \
    build_tree_without_nums, fetch_ranks, check_author

def find_geography_duplicates(database, locality_toggle, node_dict, name):
    # Searches and updates geography/locality dictionary if duplicates are found
    db_locality_info = database.cursor()
    if locality_toggle:
        db_locality_info.execute("SELECT LocalityName, LocalityID FROM locality "
                                 "WHERE GeographyID = '%s'" % name[1])
        for locality in  db_locality_info.fetchall():
            if locality[0].lower() in node_dict:
                node_dict[locality[0].lower()].append(locality[1])
            else:
                node_dict[locality[0].lower()] = [locality[1]]
        return node_dict
    if name[0].lower() in node_dict:
        node_dict[name[0].lower()].append(name[1])
    else:
        node_dict[name[0].lower()] = [name[1]]
    return node_dict

def find_taxon_duplicates(name, level_dict):
    # Searches and updates taxon dictionary if duplicates are found
    if (name[2] is None) or (name[2] == ""):
        level_dict = check_author(level_dict, name[0], None, name[1])
    else:
        level_dict = check_author(level_dict, name[0], name[2], name[1])
    return level_dict

def search_tree_geography(database, rank_records_dict, tree, rank, locality_toggle):
    # Searches each 'subtree' in the geography/locality tree, returns duplicate data list
    rank_level = rank_records_dict[rank]
    data = []
    for nodelvl in rank_level:
        node_dict = {}
        for name in [node.name for node in PreOrderIter((tree[nodelvl[2]][2]))]:
            node_dict = find_geography_duplicates(database, locality_toggle, node_dict, name)
        for key in node_dict:
            if len(node_dict[key]) > 1:
                data.append((nodelvl[1], key, str(node_dict[key])))
    return data

def search_tree_taxon(rank_records_dict, tree, rank):
    # Searches each 'subtree' in the taxon tree, returns duplicate data list
    data = []
    rank_level = rank_records_dict[rank]
    for level in rank_level:
        level_dict = {}
        for name in [node.name for node in PreOrderIter(tree[level[2]][2])]:
            level_dict = find_taxon_duplicates(name, level_dict)
        for key in level_dict:
            if len(level_dict[key]) > 1:
                data.append(((level[1]), key[0],
                             str([i[1] for i in level_dict[key]]),
                             str([j[0] for j in level_dict[key]])))
    return data

def report(headings, result_data, show):
    # Writes report, prints data to screen if specified
    file_name = "DuplicateReport[%s]" % (datetime.date.today())
    write_report(file_name, headings, result_data)
    if show:
        for row in result_data:
            print(row)
    print("Report saved as %s.csv" % file_name)

def taxon(database, table, rank_ids, rank, show):
    # Builds taxon tree, coordinates report writing
    columns = "ParentID, FullName, TaxonID, Author"
    rank_dictionary = rank_dict(database, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, True)
    try:
        result_data = search_tree_taxon(rank_dictionary, tree, rank)
    except KeyError:
        return print("Invalid rank")
    return report(["Rank Name", "Duplicate Full Name", "Authors", "TaxonIDs"], result_data, show)

def geography(database, table, rank_ids, rank, show, toggle):
    # Builds geography tree, toggles locality join, coordinates report writing
    columns = "ParentID, FullName, GeographyID"
    rank_dictionary = rank_dict(database, columns, table, rank_ids)
    tree = build_tree_with_nums(rank_dictionary, False)
    try:
        result_data = search_tree_geography(database, rank_dictionary, tree, rank, toggle)
    except KeyError:
        return print("Invalid rank")
    return report(["Country Name", "Duplicate Full Name", "Geography IDs"], result_data, show)

def main():
    # Creates arguments, connects to database, coordinates function calls
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
                        help="Rank level to start searching at", required=True)
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Print Locality ID's to be deleted to screen")
    parser.add_argument("--locality", action="store_true", dest="locality",
                        help="Search on locality")
    args = parser.parse_args()
    show = args.show
    table = args.table
    locality = args.locality
    rank = int(args.rank)
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    try:
        rank_ids = fetch_ranks(database, table)
    except pymysql.err.ProgrammingError:
        return print("%s is not a table in the schema" % table)
    if table == "taxon":
        return taxon(database, table, rank_ids, rank, show)
    if table == "geography":
        if locality:
            return geography(database, table, rank_ids, rank, show, True)
        return geography(database, table, rank_ids, rank, show, False)
    return print("Table %s not supported" % table)

if __name__ == "__main__":
    main()
