"""
Redmine Support #12204
Creates an xls report of duplicate taxon names that are part of the same family and have the same first letter of author.
First builds the taxon tree using library 'anytree', then iterates through each family subtree and creates a dictionary
with keys as the taxon fullname and first letter of author, and the values as taxonID. Then searches through dictionary
 and adds key/value pairs with more than one value to the report.
"""
import pymysql as MySQLdb
from anytree import Node, PreOrderIter
import xlwt
import itertools

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRankIDs = db.cursor()
recordsFromRank = db.cursor()

fetchRankIDs.execute("SELECT DISTINCT RankID FROM taxon WHERE RankID >=140 ORDER BY RankID ASC ")
rankIDs = fetchRankIDs.fetchall()

treeDict = {}
recordsByRank = {}
resultData = []
root = Node("root")

# creates new node and new treeDict key, sets parent to the node that was created before
def add_node(name, gid, pid, author,previous_parent):
    node = Node((name, gid, author), parent=previous_parent)
    treeDict[gid] = (name, pid, node)
    return node

# if an existing key is already in dictionary, appends value, or creates new key/value and adds to dictionary
def add_to_dict(dict,key,value):
    if key in dict: dict[key].append(value)
    else: dict[key]=[value]
    return dict

# calls on function to add to dict with parameters chosen according to what the author is for each record
def check_family_dict(familyDict, name, author, TID):
    return (add_to_dict(familyDict, (name,author), (TID,author)) if author is None else
        (add_to_dict(familyDict, (name,author[0]), (TID,author)) if (author[0] != '(') and (author != '[')
         else add_to_dict(familyDict,(name,author[1]), (TID,author))))

# selects all records with a certain rankID and puts them in a dictionary
for iD in rankIDs:
    recordsFromRank.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s", (iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the taxon tree by searching for a relationship between existing TIDs and new PIDs of records
for r in recordsByRank:
    for record in recordsByRank[r]:
        if record[0] not in treeDict:
            a = add_node(record[1], record[2], record[0], record[3], root)
        else:
            b = treeDict[record[0]][2]
            newNode = add_node(record[1], record[2], record[0], record[3], b)

for family in recordsByRank[140]:
    familyDict = {}
    for name in [node.name for node in PreOrderIter(treeDict[family[2]][2])]:
        if (name[2] is None) or (name[2] == ""): familyDict = check_family_dict(familyDict,name[0],None,name[1])
        else: familyDict = check_family_dict(familyDict,name[0],name[2],name[1])
    resultData+=[(family[1],key[0],str([i[1] for i in familyDict[key]]), str([j[0] for j in familyDict[key]])) for
                 key in familyDict if len(familyDict[key]) > 1]

# writes the results of the search to an xls file named 'TaxonDuplicateReport'
wb = xlwt.Workbook()
ws = wb.add_sheet("Taxon Duplicate Report")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Family FullName", "Duplicate FullName", "Authors", "TaxonIDs"]
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
wb.save("TaxonDuplicateReport.xls")
db.close()