"""
Redmine Support #12204
Creates a csv report of possible duplicate full taxon names that are in the same family and have the same author first
letter. Creates a tree of taxon parent-children relationships by ranks and parentID's using the library 'anytree',
then iterates through each family subtree and creates a dictionary with keys as the family name and the author first
letter, and the values as the taxonID and full author name. Then searches through dictionary and adds key/value pairs
with more than one value to the report as possible duplicates.
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import csv
import itertools

# selects ranks within the taxon schema
def fetch_ranks(db):
    db_rank_id = db.cursor()
    db_rank_id.execute("SELECT DISTINCT RankID FROM taxon WHERE RankID >=140 ORDER BY RankID ASC")
    return db_rank_id.fetchall()

# creates new node and new tree key, sets parent to the node that was created before
def add_node(name, gid, pid, author,previous_parent,tree):
    node = Node((name, gid, author), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

# if an existing key is already in dictionary, appends value, or creates new key/value and adds to dictionary
def add_to_dict(dictionary,key,value):
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key]=[value]
    return dictionary

# calls on function to add to dict with parameters chosen according to what the author is for each record
def check_family_dict(family_dict, name, author, tid):
    return (add_to_dict(family_dict, (name,author), (tid,author)) if author is None else
        (add_to_dict(family_dict, (name,author[0]), (tid,author)) if (author[0] != '(') and (author != '[')
         else add_to_dict(family_dict,(name,author[1]), (tid,author))))

# selects all records with a certain rankID and puts them in a dictionary
def rank_dict(db):
    rank_records_dict = {}
    db_record_info = db.cursor()
    for iD in fetch_ranks(db):
        db_record_info.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s",(iD[0]))
        rank_records_dict[iD[0]] = db_record_info.fetchall()
    return rank_records_dict

# builds the taxon tree by searching relationships between existing taxonID's and new parentID's within the tree
def build_tree(rank_records_dict):
    tree = {}
    root = Node("root")
    for r in rank_records_dict:
        for record in rank_records_dict[r]:
            if record[0] not in tree:
                add_node(record[1], record[2], record[0], record[3], root,tree)
            else:
                b = tree[record[0]][2]
                add_node(record[1], record[2], record[0], record[3], b,tree)
    return tree

# searches by family for matching full names and coordinates checks for author, adds to report list when match is found
def search_tree(rank_records_dict,tree):
    result_data = []
    family_names = rank_records_dict[140]
    for family in family_names:
        family_dict = {}
        for name in [node.name for node in PreOrderIter(tree[family[2]][2])]:
            if (name[2] is None) or (name[2] == ""):
                family_dict = check_family_dict(family_dict,name[0],None,name[1])
            else:
                family_dict = check_family_dict(family_dict,name[0],name[2],name[1])
        result_data+=[(family[1],key[0],str([i[1] for i in family_dict[key]]), str([j[0] for j in family_dict[key]]))
                      for key in family_dict if len(family_dict[key]) > 1]
    return result_data

# writes the duplicate data passed in to a csv file named 'TaxonDuplicateReport.csv'
def write_report(data):
    with open("TaxonDuplicateReport.csv", "w") as file_writer:
        writer = csv.writer(file_writer)
        writer.writerow(["Family Name", "Duplicate Full Name", "Authors", "TaxonIDs"])
        for row in data:
            writer.writerow(row)
    print("Report saved as 'TaxonDuplicateReport.csv'")

# calls on functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for duplicate taxon full names in the same family ")
    rank_records_dict = rank_dict(db)
    tree = build_tree(rank_records_dict)
    result_data = search_tree(rank_records_dict, tree)
    write_report(result_data)

if __name__ == "__main__":
    main()