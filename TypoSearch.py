# Builds a tree from a specified table (geography or taxon) from command line arguments and searches for possible
# Typos within and below a specified rank. Possible typos are found by taking the Levenshtein Distance between every
# Name within the rank and writing those that have a LD within the specified range to a report. If the table specified
# Has an author relationship, only names that have the same first letter of author will be compared. NOTE: rankID refers
# To the level of subtree that will be searched within, ie if in the geography table, rankID=200 is the level relating
# To countries, the tree will be searched for possible typos within the same country. NOTE: search is case INSENSITIVE,
import pymysql, argparse, datetime, itertools
from anytree import PreOrderIter
from csvwriter import write_report
from Levenshtein import distance
from specifytreebuilder import rank_dict, build_tree_without_nums, fetch_ranks

# If first two letters of the author matches, the LD is taken and returned, case INSENSITIVE
def check_author(author_letter_1, name1, author_letter_2,name2):
    if author_letter_1 == author_letter_2:
        return distance(name1.lower(),name2.lower())
    return False

# Handles first letters in author fields, adds to result list when possible typo is found
def find_taxon_typos(name1, name2, result_data,data, typo):
    if (name1[2] is not None and name1[2] != "") and (name2[2] is not None and name2[2] != ""):
        if name1[2][0] == "(" or name1[2][0] == "[":
            ld = (check_author(name1[2][1], name1[0], name2[2][0], name2[0]))
        elif name2[2][0] == "(" or name2[2][0] == "[":
            ld = check_author(name1[2][0], name1[0], name2[2][1], name2[0])
        else:
            ld = check_author(name1[2][0], name1[0], name2[2][0], name2[0])
        if 0 < ld <= typo:
            result_data.append((data[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], ld))
    elif (name1[2] is None and name2[2] is None) or (name1[2] == "" and name2[2] == ""):
        ld = check_author(name1[2], name1[0], name2[2], name2[0])
        if 0 < ld <= typo:
            result_data.append((data[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], ld))
    return result_data

# Searches the specified rank subtree of the taxon tree, coordinates LD function search, returns possible typo list
def search_tree_taxon(rank_records_dict,tree,rank, typo):
    result_data = []
    rank_names = rank_records_dict[rank]
    for data in rank_names:
        for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(tree[data[2]][2])]), 2):
            result_data = find_taxon_typos(name1,name2,result_data,data, typo)
    return result_data

# Takes Levenshtein Distance between two names and flags as possible typo if LD is in the specified range
def find_geography_typos(name_list, result_data,data, typo):
     for name1, name2 in name_list:
         ld = distance(name1[0].lower(), name2[0].lower())
         if 0 < ld <= typo:
             result_data.append((data[1], name1[0], name2[0], name1[1], name2[1], ld))
     return result_data

# Searches the specified rank subtree of the geography tree, connects to locality table if required, returns typo list
def search_tree_geography(rank_records_dict,tree, db, rank, locality_toggle, typo):
    db_locality_info = db.cursor()
    result_data=[]
    rank_names = rank_records_dict[rank]
    for data in rank_names:
        if locality_toggle:
            locality_name = []
            for locality_node in ([node.name for node in PreOrderIter(tree[data[2]][2])]):
                db_locality_info.execute("SELECT LocalityName, LocalityID FROM locality WHERE GeographyID = %s"
                                         % locality_node[1])
                locality_name += ((locality[0], locality[1]) for locality in db_locality_info.fetchall() if
                                  (any(str.isdigit(c) for c in locality[0])) is False)
            name_list = itertools.combinations(locality_name, 2)
            result_data = find_geography_typos(name_list,result_data,data, typo)
        else:
            name_list = itertools.combinations(([node.name for node in PreOrderIter((tree[data[2]][2]))]), 2)
            result_data = find_geography_typos(name_list, result_data,data, typo)
    return result_data

# Builds taxon tree, coordinates typo search in specified rank subtree, coordinates report writing
def taxon(db,table,rank_ids,rank,show, typo):
    columns = "ParentID, FullName, TaxonID, Author"
    rank_dictionary = rank_dict(db, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, True)
    try:
        result_data = search_tree_taxon(rank_dictionary, tree, rank, typo)
    except KeyError:
        return print("Invalid rank")
    heading=["Rank Name", "Name 1", "Name 2", "Author 1", "Author 2", "TaxonID 1", "TaxonID 2", "Levenshtein Distance"]
    report(heading,result_data,show)

# Builds geography tree, toggles locality search, coordinates typo search in specified rank, coordinates report writing
def geography(db,table,rank_ids,rank,locality_toggle, show, typo):
    columns = "ParentID, FullName, GeographyID"
    rank_dictionary = rank_dict(db, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, False)
    try:
        result_data = search_tree_geography(rank_dictionary,tree,db,rank, locality_toggle, typo)
    except KeyError:
        return print("Invalid rank")
    headings = ["Rank Name", "Name 1", "Name 2", "GeographyID 1", "GeographyID 2", "Levenshtein Distance"]
    report(headings, result_data, show)

# Writes report, prints possible typos to screen if show is specified
def report(headings,result_data,show):
    file_name = "TypoReport[%s]" % (datetime.date.today())
    write_report(file_name, headings, result_data)
    if show:
        for row in result_data:
            print(row)
    print("Report saved as %s.csv" % file_name)

# Creates command line arguments, coordinates functions
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database",
                        required=True)
    parser.add_argument("-table", action="store", dest="table", help="Name of table to search in", required=True)
    parser.add_argument("-rank", action="store", dest="rank", help="Rank level to start searching in (INTEGER)", required=True)
    parser.add_argument("-typo_limit", action = "store", dest = "typo",
                        help= "Maximum number of character DIFFERENCES between two names to be considered a typo, "
                              "EX: 'foo' and 'foos!' have a character difference of 2 (INTEGER)", required= True)
    parser.add_argument("--show", action="store_true", dest="show", help="Displays duplicates found to screen")
    parser.add_argument("--locality", action="store_true", dest="locality", help="Search locality table names")
    args = parser.parse_args()
    show = args.show
    table = args.table
    locality = args.locality
    rank = int(args.rank)
    typo = int(args.typo)
    try:
        db = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    try:
        rank_ids = fetch_ranks(db, table)
    except pymysql.err.ProgrammingError:
        return print("%s is not a table in the schema" % table)
    if table == "taxon":
        return taxon(db, table, rank_ids, rank, show, typo)
    elif table == "geography":
        locality_toggle = True if locality else False
        return  geography(db, table, rank_ids, rank, locality_toggle, show, typo)
    return print("Table %s not supported" % table)

if __name__ == "__main__":
    main()
