import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance
# NOTE: Duplicate search is case insensitive
# Results are saved to a file named '12464DuplicateResults.xls'
db = MySQLdb.connect("localhost", #username, #password, #specifyDatabaseName)

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()
fetchLocalityInfo = db.cursor()

fetchRankIDs.execute('SELECT DISTINCT RankID FROM geography WHERE RankID >=200')
rankIDs = fetchRankIDs.fetchall()

treeDict = {}
recordsByRank = {}
resultData = []
root = Node('root')

def addnode(name, gid, pid, previousParent):  # creates new node and new treeDict key, sets parent to the node that was created before
    node = Node((name, gid), parent=previousParent)
    treeDict[gid] = (name, pid, node)
    return node

for iD in rankIDs:  # selects all records with a certain rankID and puts them in a dictionary
    recordsFromRank.execute('SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = %s', (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

for r in recordsByRank: # builds the geography tree by searching for a relationship between an existing GID and new PID of each record of each level and connects where necessary
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = addnode(record[1], record[2], record[0], root)
        else:
            b = treeDict[record[0]][2]
            newNode = addnode(record[1], record[2], record[0], b)

for country in recordsByRank[200]: # searches each country 'subtree' for matching names & puts into dict if found
    localityDict = {}
    for localityNode in ([node.name for node in PreOrderIter(treeDict[country[2]][2])]):
        fetchLocalityInfo.execute("SELECT LocalityName, LocalityID FROM locality where GeographyID = %s" % localityNode[1])
        for locality in fetchLocalityInfo.fetchall():
            if locality[0].lower() in localityDict:
                localityDict[locality[0].lower()].append(locality[1])
            else:
                localityDict[locality[0].lower()] = [locality[1]]
    for key in localityDict: #searches the dict for any locality names with more than one GID attached to it (considered a duplicate)
        if len(localityDict[key])> 1:
            resultData.append((country[1], key, str(localityDict[key])))

wb = xlwt.Workbook() # writes contents of resultData to an xls file saved as '12464DuplicateResults.xls'
ws = wb.add_sheet('12464 Duplicate Results')

heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
headings = ['Country FullName', 'Duplicate FullName', 'LocalityIDs']
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)

wb.save('12464DuplicateResults.xls')
db.close()