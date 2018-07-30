"""
Redmine Support #12463,#12202,#12464. #12204
Using command line arguments, builds a tree from a table (geography or taxon) and searches for duplicate names within
a passed in rank. A report of the duplicates is saved in a csv file with a time stamped name. If searching in the
taxon tree, only matching names with matching author first letters are flagged. If the optional argument 'locality' is
specified then a case insensitive search of locality names is preformed via geographyID. Note, rankID refers to the
level of subtree that will be searched within, ie if in the geography table, rankid=200 is the country subtree, tree
will be searched for duplicates within the same country.
"""
import pymysql
import argparse
import datetime
from anytree import PreOrderIter
from csvwriter import write_report
import itertools
from specifytreebuilder import rank_dict, build_tree_with_nums, build_tree_without_nums,fetch_ranks, check_author

# searches each country 'subtree' for matching names in the geography table, or the locality table if specified
def search_tree_country(db,rank_records_dict,tree, rank,locality_toggle):
    countries = rank_records_dict[rank]
    data = []
    db_locality_info = db.cursor()
    for country in countries:
        country_dict = {}
        for name in [node.name for node in PreOrderIter((tree[country[2]][2]))]:
            if locality_toggle:
                db_locality_info.execute("SELECT LocalityName,LocalityID FROM locality WHERE GeographyID=%s" % name[1])
                for locality in db_locality_info.fetchall():
                    if locality[0].lower() in country_dict:
                        country_dict[locality[0].lower()].append(locality[1])
                    else:
                        country_dict[locality[0].lower()] = [locality[1]]
            if name[0] in country_dict:
                country_dict[name[0]].append(name[1])
            else:
                country_dict[name[0]] = [name[1]]
        for key in country_dict:
            if len(country_dict[key]) > 1:
                data.append((country[1],key,str(country_dict[key])))
    return data

# searches for matching full names with the same first letter of author within the same rank
def search_tree_author(rank_records_dict,tree, rank):
    result_data = []
    rank_level = rank_records_dict[rank]
    for level in rank_level:
        level_dict = {}
        for name in [node.name for node in PreOrderIter(tree[level[2]][2])]:
            if (name[2] is None) or (name[2] == ""):
                level_dict = check_author(level_dict,name[0],None,name[1])
            else:
                level_dict = check_author(level_dict,name[0],name[2],name[1])
        result_data+=[(level[1],key[0],str([i[1] for i in level_dict[key]]), str([j[0] for j in level_dict[key]]))
                      for key in level_dict if len(level_dict[key]) > 1]
    return result_data

# writes report with timestamp
def report(headings,result_data,show):
    file_name = "DuplicateReport[%s]" % (datetime.date.today())
    write_report(file_name, headings, result_data)
    if show:
        for row in result_data:
            print(row)
    print("Report saved as %s.csv" % file_name)

# builds tree for taxon table and coordinates report writing
def taxon(db,table,rank_ids,rank,show):
    columns = "ParentID, FullName, TaxonID, Author"
    rank_dictionary = rank_dict(db, columns, table, rank_ids)
    tree = build_tree_without_nums(rank_dictionary, True)
    try:
        result_data = search_tree_author(rank_dictionary, tree, rank)
    except KeyError:
        return print("Invalid rank")
    headings = ["Rank Name", "Duplicate Full Name", "Authors", "TaxonIDs"]
    report(headings,result_data,show)

# builds tree for geography table, toggles the locality search and coordinates report writing
def geography(db,table,rank_ids,rank,show,toggle):
    columns = "ParentID, FullName, GeographyID"
    rank_dictionary = rank_dict(db, columns, table, rank_ids)
    tree = build_tree_with_nums(rank_dictionary,False)
    try:
        result_data = search_tree_country(db,rank_dictionary,tree,rank,toggle)
    except KeyError:
        return print("Invalid rank")
    headings = ["Country Name", "Duplicate Geography Full Name", "Geography IDs"]
    report(headings, result_data, show)

# creates arguments, connects to database and coordinates tree searches
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database",
                        required=True)
    parser.add_argument("-table", action= "store", dest="table", help="Name of table to search in", required=True)
    parser.add_argument("-rank", action= "store", dest= "rank", help="Rank level to start searching at", required=True)
    parser.add_argument("--show", action="store_true", dest="show", help="Print Locality ID's to be deleted to screen")
    parser.add_argument("--locality", action="store_true", dest= "locality", help= "Search on locality")
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
        rank_ids = fetch_ranks(db,table)
    except pymysql.err.ProgrammingError:
        return print("%s is not a table in the schema" % table)
    if table == "taxon":
         return taxon(db,table,rank_ids,rank,show)
    elif table == "geography":
        if locality:
            return geography(db,table,rank_ids,rank,show,True)
        return geography(db,table,rank_ids,rank,show,False)
    print("Table %s not supported"% table)

if __name__== "__main__":
    main()