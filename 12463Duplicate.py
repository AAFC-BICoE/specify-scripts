import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
#Saves results in a file named '12463DuplicateResults.xls'
db = MySQLdb.connect("localhost", #username, #password, #SpecifyDatabaseName)

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute('SELECT DISTINCT RankID FROM taxon WHERE RankID >=180 ORDER BY RankID ASC')
rankIDs = fetchRankIDs.fetchall()

def addnode(name, gid, pid, author,previousParent):  # creates new node and new treeDict key, sets parent to the node that was created before
    node = Node((name, gid, author), parent=previousParent)
    treeDict[gid] = (name, pid, node)
    return node

def checkGenusDict(genusDict, name, author, TID): #checks the existing genus dict for any matching keys (duplicates), then creates a new key or adds the taxonID to the existing
    if (name, author) in genusDict:
        genusDict[(name, author)].append(TID)
    else:
        genusDict[(name, author)] = [TID]
    return genusDict

treeDict = {}
recordsByRank = {}
resultData = []
root = Node('root')

for iD in rankIDs:  # selects all records with a certain rankID and puts them in a dictionary
    recordsFromRank.execute('SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s ',(iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

for r in recordsByRank:  # builds the taxon tree by searching for a relationship between an existing GID and new PID of each record of each level and connects where necessary
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = addnode(record[1], record[2], record[0], record[3], root)
        else:
            b = treeDict[record[0]][2]
            newNode = addnode(record[1], record[2], record[0], record[3], b)

for genus in recordsByRank[180]:  # searches each genus 'subtree' for matching names with the same first character of author
    genusDict = {}
    for name in [node.name for node in PreOrderIter(treeDict[genus[2]][2])]:
        if (name[2] == None) or (name[2] == ''):
            genusDict = checkGenusDict(genusDict,name[0],None,name[1])
        else:
            genusDict = checkGenusDict(genusDict,name[0],name[2][0],name[1])

    for key in genusDict:
        if len(genusDict[key]) > 1:
            resultData.append((genus[1], key[0], key[1], str(genusDict[key])))

wb = xlwt.Workbook()  # opening excel file for results to be written to
ws = wb.add_sheet('12463 Duplicate Results')

heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
headings = ['Genus FullName', 'Duplicate FullName', 'First Letter of Author', 'Taxon IDs']
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

wb.save('12463DuplicateResults.xls')
db.close()