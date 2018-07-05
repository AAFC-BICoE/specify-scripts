"""
Creates an xls report of possible typos within the taxon tree that are part of the same family and have the same author.
First builds a taxon tree by rank using the library 'anytree' then iterates through each family subtree and takes the
levenshtein distance of each taxon full name that have the same first character of the author. Two names are flagged
as possible duplicates if their levenshtein distance is less than or equal to 2.
"""
import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
import xlwt
import itertools
from Levenshtein import distance

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute("SELECT DISTINCT RankID FROM taxon WHERE RankID >=140 ORDER BY RankID ASC")
rankIDs = fetchRankIDs.fetchall()

# creates new node and new treeDict key, sets parent to the node that was created before
def add_node(name, gid, pid, author,previous_parent):
    node = Node((name, gid, author), parent=previous_parent)
    treeDict[gid] = (name, pid, node)
    return node

treeDict = {}
recordsByRank = {}
resultData = []
root = Node("root")

# selects all records with a certain rankID and puts them in a dictionary
for iD in rankIDs:
    recordsFromRank.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s", (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the taxon tree by searching for a relationship between an existing GID and new PID of each record of each
# level and connects where necessary, also removes any names that have numbers in them to avoid trivial typo flags
for r in recordsByRank:
    for record in recordsByRank[r]:
        if not (any(str.isdigit(c) for c in record[1])):
            if record[0] not in treeDict:
                a = add_node(record[1], record[2], record[0], record[3], root)
            else:
                b = treeDict[record[0]][2]
                newNode = add_node(record[1], record[2], record[0], record[3], b)

# searches each family 'subtree' for matching names and matching first letter of author
for family in recordsByRank[140]:
    for name1, name2 in itertools.combinations(([node.name for node in PreOrderIter(treeDict[family[2]][2])]), 2):
        if (((name1[2] is not None and name1[2] != "") and (name2[2] is not None and name2[2] != "")) and
            (name1[2][0]==name2[2][0])) or (name1[2] is None and name2[2] is None) or (name1[2]== "" and name2[2]==""):
            LD = distance(name1[0], name2[0])
            if 0< LD <= 2:
                resultData.append((family[1],name1[0], name2[0], name1[2], name2[2], name1[1], name2[1],LD))

# writes the results of the search to an xls file named '12203TaxonReport'
wb = xlwt.Workbook()
ws = wb.add_sheet("12203 Taxon Report")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Family FullName","Name 1","Name 2","Author 1","Author 2","TaxonID 1","TaxonID 2","Levenshtein Distance"]
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
wb.save("12203TaxonReport.xls")
db.close()