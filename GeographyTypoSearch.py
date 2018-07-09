"""
Redmine Support #12203
Creates an xls report of possible typos within the geography tree. First builds a tree by rank using the library
'anytree' and excludes any geography full names with numbers in them to avoid any trivial typos (ie. 'Zone 1' vs 'Zone 2')
Then searches through each country subtree, if two names have a levenshtein distance of 1 then they are flagged as
possible typos and are added to the report.
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute("SELECT DISTINCT RankID FROM geography WHERE RankID >=200 ORDER BY RankID ASC")
rankIDs = fetchRankIDs.fetchall()

treeDict = {}
recordsByRank = {}
resultData = []
root = Node("root")

# creates new node and new treeDict key, sets parent to the node that was created before
def add_node(name, gid, pid,previous_parent):
    node = Node((name, gid), parent=previous_parent)
    treeDict[gid] = (name, pid, node)
    return node

# selects all records with a certain rankID and puts them in a dictionary
for iD in rankIDs:
    recordsFromRank.execute("SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = %s ", (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the geography tree by searching for a relationship between PIDs and GIDs and excludes names with numbers
for r in recordsByRank:
    for record in recordsByRank[r]:
        if (any(str.isdigit(c) for c in record[1])) is False:
            if record[0] not in treeDict:
                a = add_node(record[1], record[2], record[0], root)
            else:
                b = treeDict[record[0]][2]
                newNode = add_node(record[1], record[2], record[0], b)

# searches each country 'subtree' and compares names, searching for names with a levenshtein distance of 1
for country in recordsByRank[200]:
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter((treeDict[country[2]][2]))]), 2):
        LD = distance(name1[0], name2[0])
        if LD == 1:
            print((country[1], name1[0], name2[0], name1[1], name2[1], LD))
            resultData.append((country[1], name1[0], name2[0], name1[1], name2[1], LD))

# writes the results of the search to an xls file named 'Geography Typo Report'
wb = xlwt.Workbook()
ws = wb.add_sheet("Geography Typo Report",cell_overwrite_ok= True)
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Country", "FullName 1","FullName 2","GeographyID 1", "GeographyID 2", "Levenshtein Distance"]
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx+1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)
for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i+1, j, col)
ws.col(0).width = 256 * max([len(row[0]) for row in resultData])
wb.save("GeographyTypoReport.xls")
db.close()