import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
import Levenshtein

db = MySQLdb.connect("localhost",#username, #password, #specifyDatabaseName )

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute('SELECT DISTINCT RankID FROM taxon WHERE RankID >=140')
rankIDs = fetchRankIDs.fetchall()

def addnode(name, gid, pid, author,previousParent):  # creates new node and new treeDict key, sets parent to the node that was created before
    node = Node((name, gid, author), parent=previousParent)
    treeDict[gid] = (name, pid, node)
    return node

treeDict = {}
recordsByRank = {}
resultData = []
root = Node('root')

for iD in rankIDs:  # selects all records with a certain rankID and puts them in a dictionary
    recordsFromRank.execute('SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s', (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

for r in recordsByRank: # builds the taxon tree by searching for a relationship between an existing GID and new PID of each record of each level and connects where necessary
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = addnode(record[1], record[2], record[0], record[3], root)
        else:
            b = treeDict[record[0]][2]
            newNode = addnode(record[1], record[2], record[0], record[3], b)

for family in recordsByRank[140]: # searches each family 'subtree' for matching names and matching first letter of author
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(treeDict[family[2]][2])]), 2):
        if (((name1[2] is not None and name1[2] != '') and (name2[2] is not None and name2[2] != '')) and (name1[0] == name2[0]) and (name1[2][0] == name2[2][0])) \
                or (name1[2] is None and name2[2] is None) or (name1[2] == '' and name2[2]==''):
            LD = Levenshtein.ratio(name1[0], name2[0])
            if 1 > LD >= 0.9:
                print('Name 1', name1[0],'Name 2',name2[0], 'Levenshtein Distance', LD)
                resultData.append((family[1],name1[0], name2[0], name1[2], name2[2], name1[1], name2[1],LD))  # at this point the records are considered possible duplicates and are added to the duplicates table

wb = xlwt.Workbook() # opening excel file for results to be written to
ws = wb.add_sheet('12203 Taxon Results')

heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')  # add headings with styling and frozen first row
headings = ['Family FullName', 'Name 1', 'Name 2', 'Author 1', 'Author 2', 'TaxonID 1', 'TaxonID 2', 'Levenshtein Distance']
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

for i, row in enumerate(resultData):  # writes the duplicate records information to the execl file
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)
v = [len(row[0]) for row in resultData]
ws.col(0).width = 256 * max(v) if v else 0

wb.save('12203TaxonResults.xls')
db.close()