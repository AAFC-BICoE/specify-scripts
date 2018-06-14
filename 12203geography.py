import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance

db = MySQLdb.connect("localhost", #username, #password, #specifyDatabaseName)

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute('SELECT DISTINCT RankID FROM geography WHERE RankID >=200')
rankIDs = fetchRankIDs.fetchall()

def addnode(name, gid, pid,previousParent):  # creates new node and new treeDict key, sets parent to the node that was created before
    node = Node((name, gid), parent=previousParent)
    treeDict[gid] = (name, pid, node)
    return node

treeDict = {}
recordsByRank = {}
resultData = []
root = Node('root')

for iD in rankIDs:  # selects all records with a certain rankID and puts them in a dictionary
    recordsFromRank.execute('SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = %s ', (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

for r in recordsByRank:  # builds the geography tree by searching for a relationship between an existing GID and new PID of each record of each level and connects where necessary
    for record in recordsByRank[r]:

        if (any(str.isdigit(c) for c in record[1])) == False: #removes any geography names with numbers in them to avoid flags for trivial typos (ie Zone1 & Zone2) (can be removed if user wants those included)

            if record[0] not in treeDict:
                a = addnode(record[1], record[2], record[0], root)
            else:
                b = treeDict[record[0]][2]
                newNode = addnode(record[1], record[2], record[0], b)

for country in recordsByRank[200]:  # searches each country 'subtree' for names with a levenshtein distance of 1 (can be changed depending on what user wants to be considered a typo)
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter((treeDict[country[2]][2]))]), 2):
        LD = distance(name1[0], name2[0])
        if LD == 1:
            print('FullName 1:', name1[0], 'FullName 2: ', name2[0], 'LD:', LD)
            resultData.append((country[1], name1[0], name2[0], name1[1], name2[1], LD))

wb = xlwt.Workbook() #opening excel/LibreOffice file for results to be written too
ws = wb.add_sheet('12203 Geography Results',cell_overwrite_ok= True)

heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center') # add headings with styling and frozen first row
headings = ['Country', 'FullName 1','FullName 2','GeographyID 1', 'GeographyID 2', 'Levenshtein Distance']
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx+1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

for i, row in enumerate(resultData): # writes the duplicate records information to the execl file
    for j, col in enumerate(row):
        ws.write(i+1, j, col)
ws.col(0).width = 256 * max([len(row[0]) for row in resultData])

wb.save('12203GeographyResults.xls')
db.close()
