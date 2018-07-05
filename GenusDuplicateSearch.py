"""
Redmine Support #12463
Creates an xls report of duplicate full genus names that are in the same genus and have the same first character of author.
First creates a tree of taxon ranks using the library 'anytree', then iterates through each genus subtree and creates
a dictionary with keys as the genus name and first letter of author, and the values as the taxonID. Then searches
through dictionary and adds key/value pairs with more than one value to the report.
"""
import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools

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

# checks the existing genus dict for any matching keys (duplicates), then creates a new key or adds
# the taxonID to the existing
def check_genus_dict(genusDict, name, author, TID):
    if (name, author) in genusDict:
        genusDict[(name, author)].append(TID)
    else:
        genusDict[(name, author)] = [TID]
    return genusDict

# selects all records with a certain rankID and puts them in a dictionary
for iD in fetchRankIDs.fetchall():
    recordsFromRank.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s ",(iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the taxon tree by searching for a relationship between an existing GID and new PID of each record of
# each level and connects where necessary
for r in recordsByRank:
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = add_node(record[1], record[2], record[0], record[3], root)
        else:
            b = treeDict[record[0]][2]
            newNode = add_node(record[1], record[2], record[0], record[3], b)

# searches each genus 'subtree' for matching names with the same first character of author
for genus in recordsByRank[180]:
    genusDict = {}
    for name in [node.name for node in PreOrderIter(treeDict[genus[2]][2])]:
        if (name[2] is None) or (name[2] == ''):
            genusDict = check_genus_dict(genusDict,name[0],None,name[1])
        else:
            genusDict = check_genus_dict(genusDict,name[0],name[2][0],name[1])
    for key in genusDict:
        if len(genusDict[key]) > 1:
            print(genus[1], key[0], key[1], str(genusDict[key]))
            resultData.append((genus[1], key[0], key[1], str(genusDict[key])))

# writes the results of the search to an xls file named '12463DuplicateReport'
wb = xlwt.Workbook()
ws = wb.add_sheet("12463 Duplicate Report")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Genus FullName", "Duplicate FullName", "First Letter of Author", "Taxon IDs"]
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
wb.save("12463DuplicateReport.xls")
db.close()