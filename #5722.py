import pymysql as MySQLdb

badGoodAgentGUID = [('#GUID of the duplicate (bad) agent','#GUID of the agent to be updated (good agent)')]
try:

    db = MySQLdb.connect("localhost","#username","#password","specify" )
except NameError:
    print('MySQL connecting error')

fetchTableNames = db.cursor()
fetchBadAgentID = db.cursor()
fetchGoodAgentID = db.cursor()
tableColumnName = db.cursor()
tableCheck1 = db.cursor()
tableUpdate = db.cursor()
tableCheck2 = db.cursor()
tableDelete = db.cursor()
foreignKeyOff = db.cursor()
foreignKeyOn = db.cursor()

for guid in badGoodAgentGUID:
    try: # fetching the agentID's associated with the duplicate and and the good agent, catches any that are not in the database
        fetchBadAgentID.execute(""" SELECT AgentID FROM agent WHERE GUID = %s """ ,(guid[0]))
        badAgentID = fetchBadAgentID.fetchall()
        badID = badAgentID[0][0]
    except IndexError:
        print('Agent record with GUID' , guid[0], 'does not exist in the database')
        continue
    try:    
        fetchGoodAgentID.execute(""" SELECT AgentID FROM agent WHERE GUID = %s """ , (guid[1]))
        goodAgentID = fetchGoodAgentID.fetchall()
        goodID = goodAgentID[0][0]
    except IndexError:
        print('Agent record with GUID' , guid[0], 'does not exist in the database')
        continue
    try: # searches for any table (except the agent table) that has %agentID as a column 
        fetchTableNames.execute(""" SELECT table_name, column_name FROM information_schema.columns WHERE column_name LIKE '%agentID%' """)
        tableNames = fetchTableNames.fetchall()
        for tableType in tableNames:
            tableName = tableType[0] 
            idType = tableType[1]
            if tableName != 'agent': 
                tableCheck1.execute("""SELECT COUNT(*) FROM %s WHERE %s = %s""" % (tableName, idType, badID))
                check1 = tableCheck1.fetchall()
                if check1[0][0] != 0:
                    try: # if table has an occurrence of the duplicate agentID in it, then it is updated with the good agentID
                        tableUpdate.execute("UPDATE %s SET %s = %s WHERE %s = %s" % (tableName, idType, goodID, idType, badID))
                        db.commit()
                        print("""UPDATED %s RECORDS IN TABLE: %s""" % (check1[0][0], tableName))
                    except:
                        print('Error when trying to update')
    except:
        print('Error when checking for occurrences of agentID')
    try: #checks to make sure there are no remaining records that have the duplicateID still in them    
        tableData = []
        for tableType in tableNames:
            tableName = tableType[0] 
            idType = tableType[1]
            if tableName != 'agent':
                tableCheck2.execute("""SELECT COUNT(*) FROM %s WHERE %s = %s""" % (tableName, idType, badID))
                check2 = tableCheck2.fetchall()
                tableData.append(check2[0][0])
        if all(i ==0 for i in tableData):
            try: # deleting the duplicate agent from database
                foreignKeyOff.execute(""" SET FOREIGN_KEY_CHECKS = 0 """)
                tableDelete.execute(""" DELETE agent FROM agent WHERE agentID = %s""" % (badID))
                foreignKeyOn.execute(""" SET FOREIGN_KEY_CHECKS = 1""")
                db.commit()
                print(""" DELETED AGENT WITH AGENTID = %s FROM DATABASE SUCCESSFULLY""" % (badID))
            except:
                print('Error when trying to remove agent from database')
        else:
            print('Records not updated successfully')
    except:
        print('Error')

db.close()
