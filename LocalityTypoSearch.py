"""
Redmine Support #12464
Creates a csv report of possible typos in locality full names that are in the same country. Creates a geography tree
of parentID/taxonID relationships using the library 'anytree', then iterates through each country subtree and takes the
levenshtein distance between two locality names that don't contain numbers to avoid trivial typos (ie. 'Zone1' and
'Zone2'). Names with a LD between 0 and 1 are flagged as possible typos and added to the report.
Note: search is case insensitive (so 'Canada' and 'canada' would have a LD of 0)
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import csv
import itertools
from Levenshtein import distance

# selects ranks within the geography schema
def fetch_ranks(db):
    db_rank_id = db.cursor()
    db_rank_id.execute("SELECT DISTINCT RankID FROM geography WHERE RankID >=200 ORDER BY RankID ASC")
    return db_rank_id.fetchall()

# selects all records with a certain rankID and puts them in a dictionary
def rank_dict(db):
    rank_records_dict = {}
    db_record_info = db.cursor()
    for iD in fetch_ranks(db):
        db_record_info.execute("SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = %s", (iD[0]))
        rank_records_dict[iD[0]] = db_record_info.fetchall()
    return rank_records_dict

# creates new node and new tree key, sets parent to the node that was created before
def add_node(name, gid, pid, previous_parent,tree):
    node = Node((name, gid), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

# builds the geography tree by searching relationships between existing geographyID's and new parentID's within the tree
def build_tree(rank_records_dict):
    tree = {}
    root = Node("root")
    for r in rank_records_dict:
        for record in rank_records_dict[r]:
            if record[0] not in tree:
                add_node(record[1], record[2], record[0], root, tree)
            else:
                b = tree[record[0]][2]
                add_node(record[1], record[2], record[0], b,tree)
    return tree

# searches each country 'subtree' for names with a LD of 1 or 2, filters out locality names that contain numbers
def search_tree(rank_records_dict,tree,db):
    db_locality_info = db.cursor()
    data=[]
    countries = rank_records_dict[200]
    for country in countries:
        locality_name = []
        for locality_node in ([node.name for node in PreOrderIter(tree[country[2]][2])]):
            db_locality_info.execute("SELECT LocalityName,LocalityID FROM locality WHERE GeographyID=%s" % locality_node[1])
            locality_name +=((locality[0],locality[1]) for locality in db_locality_info.fetchall() if
                            (any(str.isdigit(c) for c in locality[0])) is False)
        for name1, name2 in itertools.combinations(locality_name, 2):
            ld = distance(name1[0].lower(), name2[0].lower())
            if 0 < ld  <=2:
                print((country[1],name1[0],name2[0], name1[1], name2[1], ld))
                data.append((country[1],name1[0],name2[0], name1[1], name2[1], ld))
    return data

# writes the typo data passed in to a csv file named 'LocalityTypoReport.csv'
def write_report(data):
    with open("LocalityTypoReport.csv", "w") as file_writer:
        writer = csv.writer(file_writer)
        writer.writerow(["Country FullName", "Name 1", "Name 2", "LocalityID 1", "LocalityID 2", "Levenshtein Distance"])
        for row in data:
            writer.writerow(row)
    print("Report saved as 'LocalityTypoReport.csv'")

# calls on functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for possible typos in locality full names within the same country")
    rank_records_dict = rank_dict(db)
    tree = build_tree(rank_records_dict)
    result_data = search_tree(rank_records_dict, tree, db)
    write_report(result_data)

if __name__ == "__main__":
    main()