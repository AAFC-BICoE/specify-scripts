import pymysql as MySQLdb

db = MySQLdb.connect("localhost",#username, #password, #specify database name)

guidList = [(''#GUID associated with duplicate agent to be deleted' , '#GUID associated with good copy of agent ')]

fetchAgentIDKeys = db.cursor()
fetchBadAgentID = db.cursor()
fetchGoodAgentID = db.cursor()
update = db.cursor()
delete = db.cursor()

fetchAgentIDKeys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'") #selects all tables where an agentID field is referenced
agentKey = fetchAgentIDKeys.fetchall()

try:
    for agent in guidList:
        fetchBadAgentID.execute("SELECT AgentID FROM agent WHERE GUID = %s" , agent[0])
        badAgent = fetchBadAgentID.fetchall()[0][0]
        fetchGoodAgentID.execute("SELECT AgentID FROM agent WHERE GUID = %s" , agent[1])
        goodAgent = fetchGoodAgentID.fetchall()[0][0]

        for tableColumnName in agentKey:
            update.execute("UPDATE %s SET %s = %s WHERE %s = %s" % (tableColumnName[0],tableColumnName[1],goodAgent,tableColumnName[1],badAgent))
            db.commit()

        delete.execute("DELETE FROM agent WHERE AgentID = %s" % badAgent)
        db.commit()
        print('AgentID', badAgent, 'successfully deleted from database')

except IndexError:
    print("Agent with GUID's", agent, "not found in database" )

db.close()