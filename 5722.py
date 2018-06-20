import pymysql as MySQLdb

db = MySQLdb.connect("localhost", 'brookec', 'temppass', 'specify')

guidList = [(''#GUID associated with duplicate agent to be deleted' , '#GUID associated with good copy of agent ')]
fetchAgentIDKeys = db.cursor()
fetchAgentID = db.cursor()
update = db.cursor()
delete = db.cursor()

fetchAgentIDKeys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                         "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'") #selects all tables where an agentID field is referenced
agentKey = fetchAgentIDKeys.fetchall()

def agentInfo(GUID): #selects AgentIDs corresponding to given GUID's
    fetchAgentID.execute("SELECT AgentID FROM agent WHERE GUID = '%s' " % GUID)
    return fetchAgentID.fetchall()[0][0]
try: #updating all instances of the 'bad agent' with the good agent then deleting the bad agent
    for agent in guidList:
        badAgent = agentInfo(agent[0])
        goodAgent = agentInfo(agent[1])
        for tableColumnName in agentKey:
            update.execute("UPDATE %s SET %s = %s WHERE %s = %s" % (tableColumnName[0],tableColumnName[1],goodAgent,tableColumnName[1],badAgent))
            db.commit()
        delete.execute("DELETE FROM agent WHERE AgentID = %s" % badAgent)
        db.commit()
        print('Agent with AgentID', badAgent, 'deleted from database')

except IndexError:
    print("Agent with GUID's", agent, "not found in database" )

db.close()