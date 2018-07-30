"""
Redmine Support #12464
Creates a csv report of possible typos in locality full names that are in the same country. Creates a geography tree
of parentID/taxonID relationships using libraries 'anytree' and 'specifytreebuilder', then iterates through each country
subtree and takes the levenshtein distance between two locality names that don't contain numbers to avoid trivial typos
(ie. 'Zone1' and 'Zone2'). Names with a LD between 0 and 1 are flagged as possible typos and added to the report.
Note: search is case insensitive (so 'Canada' and 'canada' would have a LD of 0)
"""
import pymysql as MySQLdb
from anytree import PreOrderIter
from csvwriter import write_report
import itertools
from Levenshtein import distance
from specifytreebuilder import rank_dict, build_tree_without_nums

# searches each country 'subtree' for names with a LD of 1 or 2, filters out locality names that contain numbers
def search_tree(rank_records_dict,tree,db):
    db_locality_info = db.cursor()
    data=[]
    countries = rank_records_dict[200]
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

# calls on functions
def main():
    db = MySQLdb.connect("localhost", "brookec", "temppass", "specify")
    #db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for possible typos in locality full names within the same country")

    # creating a dictionary of records relating to their rank
    rank_dictionary = rank_dict(db, "ParentID, FullName, GeographyID", "geography")

    # builds the geography tree by searching relationships between existing geographyID's and new parentID's within the tree
    tree = build_tree_without_nums(rank_dictionary, False)

    # creates list of data that has been flagged as possible typos
    result_data = search_tree(rank_dictionary, tree, db)
    heading= ["Country FullName", "Name 1", "Name 2", "LocalityID 1", "LocalityID 2", "Levenshtein Distance"]
    file_name= "LocalityTypoReport"

    # writes the typo data passed in to a csv file
    write_report(file_name,heading,result_data)
    print("Report saved as %s.csv" %file_name)

if __name__ == "__main__":
    main()