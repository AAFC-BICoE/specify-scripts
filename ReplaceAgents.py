"""
Redmine Support #5722
Given 2 GUID's pointing to a bad agent and good agent in the schema, the specified 'Bad Agent' is deleted from
the schema by changing all references of it to the specified 'Good Agent'.

# sample showing proper way GUID's are to be input, sample refers to 'bad agent': Haider_NO Fatima
    guidList = [("cc6b6a55-6571-45d9-a934-cb2aa1c66cc1", "4fd2f063-e490-4098-821a-6b207e1d39d0")]
"""
import pymysql as MySQLdb

# selects agentIDs corresponding to provided GUID's
def agent_info(guid):
    fetch_id.execute("SELECT AgentID FROM agent WHERE GUID = '%s' " % guid)
    return fetch_id.fetchall()[0][0]

# updates instances of the 'bad agent' with the good agent then deletes the bad agent
def update_agents():
    for agent in guidList:
        try:
            bad_agent = agent_info(agent[0])
            good_agent = agent_info(agent[1])
            for column_name in agent_references:
                update.execute("UPDATE %s SET %s = %s WHERE %s = %s"
                               % (column_name[0],column_name[1],good_agent,column_name[1],bad_agent))
            delete.execute("DELETE FROM agent WHERE AgentID = %s" % bad_agent)
            db.commit()
        except IndexError:
            print("Agent with GUID: ",agent," not found in database" )

if __name__ == "__main__":
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    fetch_keys = db.cursor()
    fetch_references = db.cursor()
    fetch_id = db.cursor()
    update = db.cursor()
    delete = db.cursor()
    guidList = [("GUID OF AGENT TO BE DELETED", "GUID OF GOOD AGENT")]

    # selects all tables with columns that reference an agentID field by name or by foreign key
    fetch_keys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                       "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'")
    fetch_references.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE "
                             "COLUMN_NAME LIKE '%AgentID%' AND TABLE_NAME != 'AGENT'")
    agent_references = (fetch_keys.fetchall() + fetch_references.fetchall())
    update_agents()
