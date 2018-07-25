"""
Redmine Support #12203
Creates a csv report of possible typos in geography full names that are in the same country. Creates a geography tree
of parentID/taxonID relationships using the library 'anytree', then iterates through each country subtree and takes the
levenshtein distance between two names. Names with a LD = 1 are flagged as possible typos and added to the report.
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
def add_node(name, gid, pid, previous_parent, tree):
    node = Node((name, gid), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

# builds the geography tree by searching relationships between existing geographyID's and new parentID's within the tree
def build_tree(rank_records_dict):
    tree = {}
    root = Node("root")
    for r in rank_records_dict:
        for record in rank_records_dict[r]:
            if (any(str.isdigit(c) for c in record[1])) is False:
                if record[0] not in tree:
                    add_node(record[1], record[2], record[0], root, tree)
                else:
                    b = tree[record[0]][2]
                    add_node(record[1], record[2], record[0], b,tree)
    return tree

# searches each country 'subtree' and compares names, searching for names with a levenshtein distance of 1
def search_tree(rank_records_dict,tree):
    data=[]
    countries = rank_records_dict[200]
    for country in countries:
        for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter((tree[country[2]][2]))]), 2):
            ld = distance(name1[0], name2[0])
            if ld == 1:
                print((country[1], name1[0], name2[0], name1[1], name2[1], ld))
                data.append((country[1], name1[0], name2[0], name1[1], name2[1], ld))
    return data

# writes the duplicate data passed in to a csv file named 'GeographyTypoReport.csv'
def write_report(data):
    with open("GeographyTypoReport.csv", "w") as file_writer:
        writer = csv.writer(file_writer)
        writer.writerow(["Country", "FullName 1","FullName 2","GeographyID 1", "GeographyID 2", "Levenshtein Distance"])
        for row in data:
            writer.writerow(row)
    print("Report saved as 'GeographyTypoReport.csv'")

# calls on functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for possible typos in geography full names within the same country")
    rank_records_dict = rank_dict(db)
    tree = build_tree(rank_records_dict)
    result_data = search_tree(rank_records_dict, tree)
    write_report(result_data)

if __name__ == "__main__":
    main()