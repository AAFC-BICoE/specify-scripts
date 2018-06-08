import pymysql as MySQLdb
from anytree import Node, RenderTree, AsciiStyle
import xlwt

try:
    # localhost   #username #password  #specify
    db = MySQLdb.connect("localhost", "brookec", "temppass", "specify")

except:
    print('MySQL connecting error')

rank200 = db.cursor()
rank300 = db.cursor()
rank400 = db.cursor()
rank500 = db.cursor()
check = db.cursor()

rank200.execute('''SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = 200 limit 10 ''')
rank300.execute('''SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = 300 ''')
rank400.execute('''SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = 400 ''')
rank500.execute('''SELECT ParentID, FullName, GeographyID FROM geography WHERE RankID = 500 ''')

lvl2 = rank200.fetchall()
lvl3 = rank300.fetchall()
lvl4 = rank400.fetchall()
lvl5 = rank500.fetchall()

wb = xlwt.Workbook() #opening excel file for results to be written too
ws = wb.add_sheet('12202 Results',cell_overwrite_ok= True)

# Add headings with styling and froszen first row
heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
headings = ['Country FullName', 'FullName','GeographyID 1', 'GeographyID 2']
rowx = 0
ws.set_panes_frozen(True) # frozen headings instead of split panes
ws.set_horz_split_pos(rowx+1) # in general, freeze after last heading row
ws.set_remove_splits(True) # if user does unfreeze, don't leave a split there
for colx, value in enumerate(headings):
    ws.write(rowx, colx, value, heading_xf)

root = Node('root')

# the rank of 'levels' that are used are: country > state > district > town

for country in lvl2:  # country node
    hashStore = {}  # creating a new hashStore(dict) and duplicatesTable for each country
    duplicatesTable = []

    countryFullName = country[1]
    countryGID = country[2]
    a = Node((countryFullName, countryGID),
             parent=root)  # adding country to the root node
    hashStore[hash(
        countryFullName)] = countryGID  # adding the country to hashStore

    for state in lvl3:  # searching for states that have country parents
        if state[0] == countryGID:
            stateFullName = state[1]
            stateGID = state[2]
            b = Node((stateFullName, stateGID), parent=a)
            if hash(
                    stateFullName) in hashStore:  # if node is already in the hashStore then its name, GID and the GID of the node already in HastStore are added to the duplicateTable
                dup = hashStore[hash(stateFullName)]
                duplicatesTable.append((stateFullName, stateGID, dup))
            else:  # if the node is not in the hashStore then it is added
                hashStore[hash(stateFullName)] = stateGID

            for district in lvl4:  # searching for districts that have state parents
                if district[0] == stateGID:
                    districtFullName = district[1]
                    districtGID = district[2]
                    c = Node((districtFullName, districtGID), parent=b)
                    if hash(districtFullName) in hashStore:
                        dup = hashStore[hash(districtFullName)]
                        duplicatesTable.append((districtFullName, districtGID, dup))
                    else:
                        hashStore[hash(districtFullName)] = districtGID

                    for town in lvl5:  # searching for towns that have district parents
                        if town[0] == districtGID:
                            townFullName = town[1]
                            townGID = town[2]
                            d = Node((townFullName, townGID), parent=c)
                            if hash(townFullName) in hashStore:
                                dup = hashStore[hash(townFullName)]
                                duplicatesTable.append((townFullName, townGID, dup))
                            else:
                                hashStore[hash(townFullName)] = townGID

            for town in lvl5:  # searching for towns that have state parents
                if town[
                    0] == stateGID:  # if a town is the direct child of a state, then the town is treated as a district
                    districtFullName = town[1]
                    districtGID = town[2]
                    c = Node((districtFullName, districtGID), parent=b)
                    if hash(districtFullName) in hashStore:
                        dup = hashStore[hash(districtFullName)]
                        duplicatesTable.append((districtFullName, districtGID, dup))
                    else:
                        hashStore[hash(districtFullName)] = districtGID

    for district in lvl4:  # searching for districts that have country parents
        if district[
            0] == countryGID:  # if a district is a direct child of a country then the district is treated as a state
            stateFullName = district[1]
            stateGID = district[2]
            b = Node((stateFullName, stateGID), parent=a)
            if hash(stateFullName) in hashStore:
                dup = hashStore[hash(stateFullName)]
                duplicatesTable.append((stateFullName, stateGID, dup))
            else:
                hashStore[hash(stateFullName)] = stateGID

            for town in lvl5:  # searching for towns that have district parents and country 'grandparents'
                if town[
                    0] == stateGID:  # if a town is the direct child of a state, then the town is treated as a district
                    districtFullName = town[1]
                    districtGID = town[2]
                    c = Node((districtFullName, districtGID), parent=b)
                    if hash(districtFullName) in hashStore:
                        dup = hashStore[hash(districtFullName)]
                        duplicatesTable.append((districtFullName, districtGID, dup))
                    else:
                        hashStore[hash(districtFullName)] = districtGID

    for town in lvl5:  # searching for towns that have country parents
        if town[
            0] == countryGID:  # if a town is a direct child of a country, then the town is treated as a state
            stateFullName = town[1]
            stateGID = town[2]
            b = Node((stateFullName, stateGID), parent=a)
            if hash(stateFullName) in hashStore:  #
                dup = hashStore[hash(stateFullName)]
                duplicatesTable.append((stateFullName, stateGID, dup))
            else:
                hashStore[hash(stateFullName)] = stateGID

                # once reached here, the tree is built for the country

    if duplicatesTable != []:
        resultData = []
        print('Possible duplicates In: ', countryFullName)
        for duplicate in duplicatesTable:
            duplicateName = duplicate[0]
            GID1 = duplicate[1]
            GID2 = duplicate[2]

            print('FullName: ', duplicateName, 'GeographyIDs:', GID1, ',', GID2)
            resultData.append((countryFullName,duplicateName, GID1, GID2))
        for i, row in enumerate(resultData):
            for j, col in enumerate(row):
                ws.write(i+1, j, col)
        v = [len(row[0]) for row in resultData]
        ws.col(0).width = 256 * max(v) if v else 0

wb.save('12202ResultsTEST.xls')


''' 
#prints the tree created (for interest only)                                                                                                                                                                                                                        
for pre,fill, node in RenderTree(root):                                                                                                                                                                                     
    print("%s%s" % (pre, node.name[0]))                                                                                                                                                                                     
'''

print('Complete')

db.close()