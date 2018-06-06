import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle
import xlwt

# results are saved in a file called '12204Results.xls'

try:                    y
    db = MySQLdb.connect("localhost",#username, #password, #specifyDatabaseName)
except:
    print('MySQL connecting error')

familyName = db.cursor()
fetchrlvl1 = db.cursor()
fetchrlvl2 = db.cursor()
fetchrlvl3 = db.cursor()
fetchrlvl4 = db.cursor()

familyName.execute("SELECT FullName, Author, ParentID, TaxonID FROM taxon WHERE RankID = 140") #140 is the rank where all the family nodes are found (beginning of search)
fetchrlvl1.execute('SELECT FullName, Author, ParentID, TaxonID FROM taxon WHERE RankID = 180') #180 is the only rank who has parents in the 140 rank
fetchrlvl2.execute('SELECT FullName, Author, ParentID, TaxonID FROM taxon WHERE RankID = 220') #220 is the only rank who has parents in the 180 rank
fetchrlvl3.execute('SELECT FullName, Author, ParentID, TaxonID FROM taxon WHERE RankID IN (225,227,230,285,287,270,240,250,260)') #all of these ranks have parents in the 220 rank
fetchrlvl4.execute('SELECT FullName, Author, ParentID, TaxonID FROM taxon WHERE RankID IN (250,260,270)') #all of these ranks have parents in the above ranks

lvl0 = familyName.fetchall()
lvl1 = fetchrlvl1.fetchall()
lvl2 = fetchrlvl2.fetchall()
lvl3 = fetchrlvl3.fetchall()
lvl4 = fetchrlvl4.fetchall()

wb = xlwt.Workbook() #opening excel/LibreOffice file for results to be written too
ws = wb.add_sheet('12204 Results',cell_overwrite_ok= True)

# Add headings with styling and frozen first row
heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
headings = ['Taxon FullName', 'Author 1','ParentID 1', 'TaxonID 1', 'Author 2', 'ParentID 2', 'TaxonID 2']
rowx = 0
ws.set_panes_frozen(True)
ws.set_horz_split_pos(rowx+1)
ws.set_remove_splits(True)
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

resultData = [] #creating the table that will later be used for writing the duplicates to the excel file

root = Node('root') #creating the 'root' node that everything will attach to

def checkHash(hashDict, dupTable, name, Author, PID, TID):
    if hash(name) in hashDict:  # checks to see if the current fullName is already in the hashStore
        dup = hashDict[hash(name)]  # if it is, the duplicate already in the hash table and the current info are added to the duplicatesTable
        dupTable.append((name, Author, PID, TID, dup))
    else:  # if the current info is not in hashStore then it is added
        hashDict[hash(name)] = (Author, PID,TID)
    return [hashDict, dupTable]

def addNode(fullName, TID, parentB4): # creates node with info passed in, setting the parent to the node that was created before
    node = Node((fullName,TID), parent=parentB4)
    return node

for familyName in lvl0:
    hashStore = {}  # creating a new hashStore(dict) and duplicatesTable for each family
    duplicatesTable = []
    famFullName = familyName[0]
    famTID = familyName[3]
    hashStore[hash(famFullName)] = famTID
    a = Node((famFullName, famTID), parent=root)

    for r1 in lvl1: # for each level, checks to see if each record is a child of the record before, and if so calls on the different functions to preform the next actions
        if r1[2] == famTID:
            b = addNode(r1[0], r1[3], a)
            check1 = checkHash(hashStore,duplicatesTable,r1[0],r1[1],r1[2],r1[3])
            hashStore = check1[0]
            duplicatesTable = check1[1]

            for r2 in lvl2:
                if r2[2] == r1[3]:
                    c = addNode(r2[0], r2[3], b)
                    check2 = checkHash(hashStore,duplicatesTable,r2[0],r2[1],r2[2],r2[3])
                    hashStore = check2[0]
                    duplicatesTable = check2[1]

                    for r3 in lvl3:
                        if r3[2] == r2[3]:
                            d = addNode(r3[0], r3[3], c)
                            check3 = checkHash(hashStore,duplicatesTable,r3[0],r3[1],r3[2],r3[3])
                            hashStore = check3[0]
                            duplicatesTable = check3[1]

                            for r4 in lvl4:
                                if r4[2] == r3[3]:
                                    e = addNode(r4[0], r4[3], d)
                                    check4 = checkHash(hashStore,duplicatesTable,r4[0],r4[1],r4[2],r4[3])
                                    hashStore = check4[0]
                                    duplicatesTable = check4[1]

    if duplicatesTable != []:
        print('Possible duplicate record found in', famFullName)
        for dup in duplicatesTable:
            author1 = dup[1]
            author2 = dup[4][0]
            if (author1 != None) and (author2 != None) and (author1 != '') and (author2 != ''): #makes sure that the first letters of the authors are names
                if author1[0] == author2[0]: #checks to see if the first letters of the two authors are the same
                    print('Taxon FullName:', dup[0], 'Author1:', dup[1], 'ParentID1:', dup[2], 'TaxonID1:', dup[3], 'Author2:', dup[4][0], 'ParentID2:', dup[4][1], 'TaxonID2:', dup[4][2])
                    resultData.append((dup[0], dup[1], dup[2], dup[3], dup[4][0], dup[4][1], dup[4][2])) #at this point the two records are considered duplicates are are added to the table that will be written to the excel file

for i, row in enumerate(resultData): #adding each set of data in the resultData table to the excel file
    for j, col in enumerate(row):
        ws.write(i+1, j, col)
v = [len(row[0]) for row in resultData]
ws.col(0).width = 256 * max(v) if v else 0

wb.save('12204Results.xls')
db.close()

