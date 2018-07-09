"""
Redmine Support #12464
Creates an xls report of duplicate locality names within a country. Selects duplicate names by first building a tree
using the library 'anytree', then iterates each node within a country subtree and creates a dictionary with locality
names as keys and loclaityID's as values. Once dictionary is complete, iterates back over and counts number of IDs that
are attached to each locality name, if there is more than one, locality name and ID's are added to the report.
Note: Typo search is case insensitive (so 'Canada' and 'canada' are considered duplicates)
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import xlwt
import itertools

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()
fetchLocalityInfo = db.cursor()

fetchRankIDs.execute("SELECT DISTINCT RankID FROM geography WHERE RankID >=200 ORDER BY RankID ASC")
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
    recordsFromRank.execute("SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = %s", (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the geography tree by searching for a relationship between parentIDs and geographyIDs and connects
for r in recordsByRank:
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = add_node(record[1], record[2], record[0], root)
        else:
            b = treeDict[record[0]][2]
            newNode = add_node(record[1], record[2], record[0], b)

# searches each country 'subtree' for matching names & puts into dict if found then searches dict for keys with len > 1
for country in recordsByRank[200]:
    localityDict = {}
    for localityNode in ([node.name for node in PreOrderIter(treeDict[country[2]][2])]):
        fetchLocalityInfo.execute("SELECT LocalityName,LocalityID FROM locality WHERE GeographyID=%s" %localityNode[1])
        for locality in fetchLocalityInfo.fetchall():
            if locality[0].lower() in localityDict: localityDict[locality[0].lower()].append(locality[1])
            else: localityDict[locality[0].lower()] = [locality[1]]
    for key in localityDict:
        if len(localityDict[key])> 1: resultData.append((country[1], key, str(localityDict[key])))

# writes contents of resultData to an xls report saved as 'LocalityDuplicateReport.xls'
wb = xlwt.Workbook()
ws = wb.add_sheet("Locality Duplicate Report")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Country FullName", "Duplicate FullName", "LocalityIDs"]
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)
for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)
wb.save("LocalityDuplicateReport.xls")
db.close()