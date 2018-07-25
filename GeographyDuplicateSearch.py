"""
Redmine Support #12202
Creates a csv report of duplicate geography names within a country. Creates a tree of geographyID/parentID relationships
using geography ranks with library 'anytree' then iterates through each country subtree and compares each name,
duplicate full names are added to the report.
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import csv
import itertools

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
            if record[0] not in tree:
                add_node(record[1], record[2], record[0], root, tree)
            else:
                b = tree[record[0]][2]
                add_node(record[1], record[2], record[0], b,tree)
    return tree

# searches each country 'subtree' for matching names
def search_tree(rank_records_dict,tree):
    countries = rank_records_dict[200]
    data = []
    for country in countries:
        country_dict = {}
        for name in [node.name for node in PreOrderIter((tree[country[2]][2]))]:
            if name[0] in country_dict:
                country_dict[name[0]].append(name[1])
            else:
                country_dict[name[0]] = [name[1]]
        for key in country_dict:
            if len(country_dict[key]) > 1:
                data.append((country[1],key,str(country_dict[key])))
    return data

# writes the duplicate data passed in to a csv file named 'GeographyDuplicateReport.csv'
def write_report(data):
    with open("GeographyDuplicateReport.csv", "w") as file_writer:
        writer = csv.writer(file_writer)
        writer.writerow(["Country Name", "Duplicate Geography Full Name", "Geography IDs"])
        for row in data:
            writer.writerow(row)
    print("Report saved as 'GeographyDuplicateReport.csv'")

# calls on functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for duplicate geography full names in the same country ")
    rank_records_dict = rank_dict(db)
    tree = build_tree(rank_records_dict)
    result_data = search_tree(rank_records_dict, tree)
    write_report(result_data)

if __name__ == "__main__":
    main()