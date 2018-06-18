import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance
# Saves results as '12464TypoResults.xls'
db = MySQLdb.connect("localhost",#username, #password, #specifyDatabaseName )

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute('SELECT DISTINCT RankID FROM taxon WHERE RankID >=180 ORDER BY RankID ASC')
rankIDs = fetchRankIDs.fetchall()

def addnode(name, gid, pid, author,previousParent):  # creates new node and new treeDict key, sets parent to the node that was created before
    node = Node((name, gid, author), parent=previousParent)
    treeDict[gid] = (name, pid, node)
    return node

treeDict = {}
recordsByRank = {}
resultData = []
root = Node('root')

for iD in rankIDs:  # selects all records corresponding to a certain rankID and places them in a dictionary with RankID as key
    recordsFromRank.execute('SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s', (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

for r in recordsByRank: # builds the taxon tree by searching for a relationship between an existing GID and new PID of each record of each level and connects where necessary
    for record in recordsByRank[r]:
        if  not (any(str.isdigit(c) for c in record[1])): # removes any names that have numbers in them to avoid trivial typo flags
            if record[0] not in treeDict:
                a = addnode(record[1], record[2], record[0], record[3], root)
            else:
                b = treeDict[record[0]][2]
                newNode = addnode(record[1], record[2], record[0], record[3], b)

for genus in recordsByRank[180]: # searches and compares within each genus 'subtree' for matching first letter in Author then computes the LS Distance
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(treeDict[genus[2]][2])]), 2):
        if (((name1[2] is not None and name1[2] != '') and (name2[2] is not None and name2[2] != '')) and (name1[2][0] == name2[2][0])) \
                or (name1[2] is None and name2[2] is None) or (name1[2] == '' and name2[2]==''):
            LD = distance(name1[0], name2[0])
            if LD == 1:
                resultData.append((genus[1],name1[0], name2[0], name1[2], name2[2], name1[1], name2[1],LD))

wb = xlwt.Workbook()
ws = wb.add_sheet('12463 Typo Results')

heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
headings = ['GenusFullName', 'FullName 1', 'FullName 2', 'Author 1', 'Author 2', 'TaxonID 1', 'TaxonID 2', 'Levenshtein Distance']
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx + 1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

for i, row in enumerate(resultData):
    for j, col in enumerate(row):
        ws.write(i + 1, j, col)

wb.save('12463TypoResults.xls')
db.close()
