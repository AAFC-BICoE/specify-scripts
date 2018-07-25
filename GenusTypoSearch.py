"""
Redmine Support #12463
Creates a csv report of possible typos in taxon full names that are part of the same genus and have the same author
first letter. Creates a taxon tree of parentID/taxonID relationships using the library 'anytree', then iterates through
each genus subtree and takes the levenshtein distance between two taxon names that have the same author first letter.
Names with a LD between 0 and 2 are flagged as possible typos and are added to the report.
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import csv
import itertools
from Levenshtein import distance

# selects ranks within the taxon schema
def fetch_ranks(db):
    db_rank_id = db.cursor()
    db_rank_id.execute("SELECT DISTINCT RankID FROM taxon WHERE RankID >=180 ORDER BY RankID ASC")
    return db_rank_id.fetchall()

# creates new node and new treeDict key, sets parent to the node that was created before
def add_node(name, gid, pid, author,previous_parent, tree):
    node = Node((name, gid, author), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

# if first two letters of the author matches, the LD is taken and returned
def check_author(author1, name1, author2,name2):
    if author1 == author2:
        return distance(name1,name2)
    return False

#selects all records with a certain rankID and puts them in a dictionary
def rank_dict(db):
    rank_records_dict = {}
    db_record_info = db.cursor()
    for iD in fetch_ranks(db):
        db_record_info.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s",(iD[0]))
        rank_records_dict[iD[0]] = db_record_info.fetchall()
    return rank_records_dict

# builds the taxon tree by searching relationships between existing taxonID's and new parentID's within the tree and
# filters out trivial matches with numbers in names
def build_tree(rank_records_dict):
    tree = {}
    root = Node("root")
    for r in rank_records_dict:
        for record in rank_records_dict[r]:
            if  not (any(str.isdigit(c) for c in record[1])):
                if record[0] not in tree:
                    add_node(record[1], record[2], record[0], record[3], root,tree)
                else:
                    b = tree[record[0]][2]
                    add_node(record[1], record[2], record[0], record[3], b,tree)
    return tree

# searches and compares within each genus 'subtree' for matching first letter in Author then computes the LS Distance
def search_tree(rank_records_dict,tree):
    typos = []
    genus_names = rank_records_dict[180]
    for genus in genus_names:
        for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(tree[genus[2]][2])]), 2):
            if (name1[2] is not None and name1[2] != "") and (name2[2] is not None and name2[2] != ""):
                if name1[2][0] == '(' or name1[2][0] == '[':
                    ld = (check_author(name1[2][1], name1[0], name2[2][0], name2[0]))
                elif name2[2][0] == '(' or name2[2][0] == '[':
                    ld = check_author(name1[2][0], name1[0], name2[2][1], name2[0])
                else:
                    ld = check_author(name1[2][0], name1[0], name2[2][0], name2[0])
                if 0 < ld <= 2:
                    typos.append((genus[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], ld))
            elif (name1[2] is None and name2[2] is None) or (name1[2] == "" and name2[2] == ""):
                ld = check_author(name1[2], name1[0], name2[2], name2[0])
                if 0 < ld <= 2:
                    typos.append((genus[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], ld))
    return typos

# writes the typo data passed in to a csv file named 'GenusDuplicateReport.csv'
def write_report(data):
    with open("GenusTypoReport.csv", "w") as file_writer:
        writer = csv.writer(file_writer)
        writer.writerow(["Genus Name", "Taxon Name 1", "Taxon Name 2","Author 1","Author 2", "TaxonID 1",
                         "TaxonID 2","Levenshtein Distance"])
        for row in data:
            writer.writerow(row)
    print("Report saved as 'GenusTypoReport.csv'")

# calls on functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for possible typos in taxon full names within the same genus")
    rank_records_dict = rank_dict(db)
    tree = build_tree(rank_records_dict)
    result_data = search_tree(rank_records_dict, tree)
    write_report(result_data)

if __name__ == "__main__":
    main()