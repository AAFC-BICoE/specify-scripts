import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance
#NOTE: Typo search is case insensitive
# Saves file as '12464TypoResults.xls'
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

for r in recordsByRank:  # builds the geography tree by searching for a relationship between an existing GID and new PID of each record of each level and connects where necessary
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = addnode(record[1], record[2], record[0], root)
        else:
            b = treeDict[record[0]][2]
            newNode = addnode(record[1], record[2], record[0], b)

for country in recordsByRank[200]:  # searches each country 'subtree' for names with a Levenshtein distance of 1 o 2 (can be changed) 
    localityName = []
    for localityNode in ([node.name for node in PreOrderIter(treeDict[country[2]][2])]):
        fetchLocalityInfo.execute("SELECT LocalityName, LocalityID FROM locality where GeographyID = %s" % localityNode[1])
        for locality in fetchLocalityInfo.fetchall():
            localityName.append((locality[0],locality[1]))
    for name1, name2 in itertools.combinations(localityName, 2):
        LD = distance(name1[0].lower(), name2[0].lower())
        if 0 < LD  <=2:
            resultData.append((country[1],name1[0],name2[0], name1[1], name2[1], LD))

wb = xlwt.Workbook()  # writes contents of resultData to an .xls file saved as '12464TypoResults.xls'
ws = wb.add_sheet('12464 Typo Results')

heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
headings = ['Country FullName', 'Name 1', 'Name 2', 'LocalityID 1', 'LocalityID 2', 'Levenshtein Distance']
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)

wb.save('12464TypoResults.xls')
db.close()