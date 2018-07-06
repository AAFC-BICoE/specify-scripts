"""
Redmine Support #12463
Creates an xls report of possible duplicate full taxon names that are in the same genus and have the same first
letter in the author field. First creates a tree of taxon parent-children relationships by ranks and parentID's using
the library  'anytree', then iterates through each genus subtree and creates a dictionary with keys as the genus name
and first letter of author, and the values as the taxonID and full author name. Then searches through dictionary and adds
key/value pairs with more than one value to the report as possible duplicates.
"""
import pymysql as MySQLdb
from anytree import Node, RenderTree, PreOrderIter
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

# if an existing key is already in dictionary, appends value, or creates new key/value and adds to dictionary
def add_to_dict(dict,key,value):
    if key in dict: dict[key].append(value)
    else: dict[key]=[value]
    return dict

# calls on function to add to dict with parameters chosen according to what the author is for each record
def check_genus_dict(genusDict, name, author, TID):
    return (add_to_dict(genusDict, (name,author), (TID,author)) if author is None else
        (add_to_dict(genusDict, (name,author[0]), (TID,author)) if (author[0] != '(') and (author != '[')
         else add_to_dict(genusDict,(name,author[1]), (TID,author))))

# selects all records with a certain rankID and puts them in a dictionary
for iD in fetchRankIDs.fetchall():
    recordsFromRank.execute("SELECT ParentID, FullName, TaxonID, Author FROM taxon WHERE RankID = %s",(iD[0]))
    recordsByRank[iD[0]] = recordsFromRank.fetchall()

# builds the taxon tree by searching relationships between existing GID's and new PID's within the treeDict
for r in recordsByRank:
    for record in recordsByRank[r]:
        if record[0] not in treeDict: a = add_node(record[1], record[2], record[0], record[3], root)
        else:
            b = treeDict[record[0]][2]
            newNode = add_node(record[1], record[2], record[0], record[3], b)

# searches by genus for matching full names and coordinates checks for author, adds to report list when match is found
for genus in recordsByRank[180]:
    genusDict = {}
    for name in [node.name for node in PreOrderIter(treeDict[genus[2]][2])]:
        if (name[2] is None) or (name[2] == ""): genusDict = check_genus_dict(genusDict,name[0],None,name[1])
        else: genusDict = check_genus_dict(genusDict,name[0],name[2],name[1])
    resultData+=[(genus[1],key[0],str([i[1] for i in genusDict[key]]), str([j[0] for j in genusDict[key]])) for
                 key in genusDict if len(genusDict[key]) > 1]

# writes the contents of the duplicate list to an xls file named 'GenusDuplicateReport'
wb = xlwt.Workbook()
ws = wb.add_sheet("Genus Duplicate Report")
heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
headings = ["Genus FullName", "Duplicate FullName", "Authors", "Taxon IDs"]
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
wb.save("GenusDuplicateReport.xls")
db.close()