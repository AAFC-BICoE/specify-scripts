"""
Redmine Support #12203,#12463,#12464
Using command line arguments, builds a tree from a table (geography or taxon) and searches for possible typos in names
within a passed in rank by taking two names Levenshtein Distance. A report of the flagged names is saved in a csv file
with a time stamped name. If searching in the taxon tree, only matching names with matching author first letters are
flagged. If the optional argument 'locality' is specified then a case insensitive search of locality names is preformed
via geographyID. Names are flagged as possible typos if their Levenshtein distance is 1 or 2.
Note, rankID refers to the level of subtree that will be searched within, ie if in the geography table,
rankID=200 is the country subtree, tree will be searched for possible typos within the same country.
"""
import pymysql
import argparse
import datetime
import itertools
from anytree import PreOrderIter
from csvwriter import write_report
from Levenshtein import distance
from specifytreebuilder import rank_dict, build_tree_without_nums, fetch_ranks

# if first two letters of the author matches, the LD is taken and returned
def check_author(author1, name1, author2,name2):
    if author1 == author2:
        return distance(name1,name2)
    return False

# searches the taxon tree for rank subtree, handles authors, takes LD
def search_tree_taxon(rank_records_dict,tree,rank):
    result_data = []
    rank_names = rank_records_dict[rank]
    for data in rank_names:
        for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(tree[data[2]][2])]), 2):
            if (name1[2] is not None and name1[2] != "") and (name2[2] is not None and name2[2] != ""):
                if name1[2][0] == "(" or name1[2][0] == "[":
                    ld = (check_author(name1[2][1], name1[0], name2[2][0], name2[0]))
                elif name2[2][0] == "(" or name2[2][0] == "[":
                    ld = check_author(name1[2][0], name1[0], name2[2][1], name2[0])
                else:
                    ld = check_author(name1[2][0], name1[0], name2[2][0], name2[0])
                if 0 < ld <= 2:
                    result_data.append((data[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], ld))
            elif (name1[2] is None and name2[2] is None) or (name1[2] == "" and name2[2] == ""):
                ld = check_author(name1[2], name1[0], name2[2], name2[0])
                if 0 < ld <= 2:
                    result_data.append((data[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], ld))
    return result_data

# searches the geography tree for rank subtrees, connects with locality names (without numbers), takes LD
def search_tree_locality(rank_records_dict,tree,db,rank):
    db_locality_info = db.cursor()
    data=[]
    countries = rank_records_dict[rank]
    for country in countries:
        locality_name = []
        for locality_node in ([node.name for node in PreOrderIter(tree[country[2]][2])]):
            db_locality_info.execute("SELECT LocalityName,LocalityID FROM locality WHERE GeographyID=%s"%locality_node[1])
            locality_name +=((locality[0],locality[1]) for locality in db_locality_info.fetchall() if
                            (any(str.isdigit(c) for c in locality[0])) is False)
        for name1, name2 in itertools.combinations(locality_name, 2):
            ld = distance(name1[0].lower(), name2[0].lower())
            if 0 < ld  <=2:
                data.append((country[1],name1[0],name2[0], name1[1], name2[1], ld))
    return data

# searches the geography tree for rank subtrees, takes LD
def search_tree_geography(rank_records_dict,tree,rank):
    result_data=[]
    rank_names = rank_records_dict[rank]
    for data in rank_names:
        for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter((tree[data[2]][2]))]), 2):
            ld = distance(name1[0], name2[0])
            if 0 < ld <=2:
                result_data.append((data[1], name1[0], name2[0], name1[1], name2[1], ld))
    return result_data

# builds tree for taxon table, writes report
def taxon(db,table,rank_ids,rank,show):
    columns = "ParentID, FullName, TaxonID, Author"
    rank_dictionary = rank_dict(db, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, True)
    try:
        result_data = search_tree_taxon(rank_dictionary, tree, rank)
    except KeyError:
        return print("Invalid rank")
    heading=["Rank Name", "Name 1", "Name 2", "Author 1", "Author 2", "TaxonID 1", "TaxonID 2", "Levenshtein Distance"]
    report(heading,result_data,show)

# builds tree for geography table, toggles the locality search
def geography(db,table,rank_ids,rank,toggle):
    columns = "ParentID, FullName, GeographyID"
    rank_dictionary = rank_dict(db, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, False)
    try:
        if toggle:
            return search_tree_locality(rank_dictionary,tree,db,rank)
        return search_tree_geography(rank_dictionary,tree,rank)
    except KeyError:
        return print("Invalid rank")

# writes report with timestamp in file name
def report(headings,result_data,show):
    file_name = "TypoReport[%s]" % (datetime.date.today())
    write_report(file_name, headings, result_data)
    if show:
        for row in result_data:
            print(row)
    print("Report saved as %s.csv" % file_name)

# creates arguments for commandline, handles exceptions, coordinates functions
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database",
                        required=True)
    parser.add_argument("-table", action="store", dest="table", help="Name of table to search in", required=True)
    parser.add_argument("-rank", action="store", dest="rank", help="Rank level to start searching at", required=True)
    parser.add_argument("--show", action="store_true", dest="show", help="Print Locality ID's to be deleted to screen")
    parser.add_argument("--locality", action="store_true", dest="locality", help="Search locality table names")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    show = args.show
    table = args.table
    locality = args.locality
    rank = int(args.rank)
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    try:
        rank_ids = fetch_ranks(db, table)
    except pymysql.err.ProgrammingError:
        return print("%s is not a table in the schema" % table)
    if table == "taxon":

        return taxon(db, table, rank_ids, rank, show)
    elif table == "geography":
        headings = ["Rank Name", "Name 1", "Name 2", "GeographyID 1", "GeographyID 2", "Levenshtein Distance"]
        if locality:
            result_data = geography(db, table, rank_ids, rank, True)
            return report(headings, result_data, show)
        result_data= geography(db, table, rank_ids, rank, False)
        return report(headings, result_data, show)
    return print("Table %s not supported" % table)

if __name__ == "__main__":
    main()