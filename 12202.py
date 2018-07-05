"""
Creates an xls report of duplicate geography names within a country. First creates a tree using geography ranks using
library 'anytree' then iterates through each country subtree and compares each name with each other, if two geography
full names are a match then they are considered a duplicate and are added to the report.
"""
import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute("SELECT DISTINCT RankID FROM geography WHERE RankID >=200")
rankIDs = fetchRankIDs.fetchall()

treeDict = {}
recordsByRank = {}
resultData = []
root = Node("root")

# creates new node and new treeDict key, sets parent to the node that was created before
def add_node(name, gid, pid, previous_parent):
    node = Node((name, gid), parent=previous_parent)
    treeDict[gid] = (name, pid, node)
    return node

# selects all records with a certain rankID and puts them in a dictionary
for iD in rankIDs:
    recordsFromRank.execute("SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = %s ", (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the geography tree by searching for a relationship between an existing GID and new PID of each
# record of each level and connects where necessary
for r in recordsByRank:
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = add_node(record[1], record[2], record[0], root)
        else:
            b = treeDict[record[0]][2]
            newNode = add_node(record[1], record[2], record[0], b)

# searches each country 'subtree' for matching names
for country in recordsByRank[200]:
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter((treeDict[country[2]][2]))]), 2):
        if name1[0] == name2[0]:
            resultData.append((country[1], name1[0], name1[1], name2[1]))

# writes the results of the search to an xls file named '12202Report'
wb = xlwt.Workbook()
ws = wb.add_sheet("12202 Results")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Country FullName", "Duplicate FullName", "GeographyID 1", "GeographyID 2"]
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)
for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)
v = [len(row[0]) for row in resultData]
ws.col(0).width = 256 * max(v) if v else 0
wb.save("12202Report.xls")
db.close()