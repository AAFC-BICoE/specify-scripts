"""
Redmine Support #12463
Creates an xls report of possible typos in genus names that are part of the same family and have the same first
letter of author. First creates a tree of taxon ranks using the library 'anytree', then iterates through each family
subtree and takes the levenshtein distance between two genus names that meet the requirements. Names with a LD between
0 and 2 are flagged as possible typos and are added to the report.
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute("SELECT DISTINCT RankID FROM taxon WHERE RankID >=180 ORDER BY RankID ASC")

treeDict = {}
recordsByRank = {}
resultData = []
root = Node("root")

# creates new node and new treeDict key, sets parent to the node that was created before
def add_node(name, gid, pid, author,previous_parent):
    node = Node((name, gid, author), parent=previous_parent)
    treeDict[gid] = (name, pid, node)
    return node

# if first two letters of the author matches, the LD is taken, if not then 3 is returned (a LD that wont be recorded)
def check_author(author1, name1, author2,name2):
    if author1 == author2: return distance(name1,name2)
    return 3

# selects all records corresponding to a certain rankID and places them in a dictionary with RankID as key
for iD in fetchRankIDs.fetchall():
    recordsFromRank.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s", (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the taxon tree by searching for relationships between ParentIDs of each record
for r in recordsByRank:
    for record in recordsByRank[r]:
        # removes any names that have numbers in them to avoid trivial typo flags
        if  not (any(str.isdigit(c) for c in record[1])):
            if record[0] not in treeDict:
                a = add_node(record[1], record[2], record[0], record[3], root)
            else:
                b = treeDict[record[0]][2]
                newNode = add_node(record[1], record[2], record[0], record[3], b)

# searches and compares within each genus 'subtree' for matching first letter in Author then computes the LS Distance
for genus in recordsByRank[180]:
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(treeDict[genus[2]][2])]), 2):
        if (name1[2] is not None and name1[2] != "") and (name2[2] is not None and name2[2] != ""):
            if name1[2][0] == '(' or name1[2][0] == '[': LD = (check_author(name1[2][1], name1[0], name2[2][0], name2[0]))
            elif name2[2][0] == '(' or name2[2][0] == '[': LD = check_author(name1[2][0], name1[0], name2[2][1], name2[0])
            else:LD = check_author(name1[2][0], name1[0], name2[2][0], name2[0])
            if 0 < LD <= 2:
                resultData.append((genus[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], LD))
        elif (name1[2] is None and name2[2] is None) or (name1[2] == "" and name2[2] == ""):
            LD = check_author(name1[2], name1[0], name2[2], name2[0])
            if 0 < LD <= 2:
                resultData.append((genus[1], name1[0], name2[0], name1[2], name2[2], name1[1], name2[1], LD))

# writes contents of resultData to an xls report saved as 'GenusTypoReport.xls'
wb = xlwt.Workbook()
ws = wb.add_sheet("12463 Typo Report")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["GenusFullName","FullName 1","FullName 2","Author 1","Author 2","TaxonID 1","TaxonID 2","Levenshtein Distance"]
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)
for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)
wb.save("GenusTypoReport.xls")
db.close()