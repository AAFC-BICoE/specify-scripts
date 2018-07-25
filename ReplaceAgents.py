"""
Redmine Support #5722
Reading from a csv file containing two GUID's, the specified 'Bad Agent' is deleted from the schema by changing all
references of the 'Bad Agent' to the specified 'Good Agent' using the database schema to look for references of 'AgentID'
in column names and foreign keys. File path of csv needs to be specified first.
NOTE: csv format should have the GUID of the agent to be deleted FIRST, then the GUID of the agent that the info will be
changed to SECOND in the same row
"""
import pymysql as MySQLdb
import csv

# selects agentIDs corresponding to provided GUID's
def agent_info(fetch_id,guid):
    fetch_id.execute("SELECT AgentID FROM agent WHERE GUID = '%s' " % guid)
    return fetch_id.fetchall()[0][0]

# updates instances of the 'bad agent' with the good agent then deletes the bad agent
def update_agents(guid_list,fetch_id,agent_references,update,delete):
    for agent in guid_list:
        try:
            bad_agent = agent_info(fetch_id,agent[0])
            good_agent = agent_info(fetch_id,agent[1])
            update_agent = input("Update AgentID %s to AgentID %s? [y/n]" % (bad_agent,good_agent))
            if update_agent == "y":
                for column_name in agent_references:
                    update.execute("UPDATE %s SET %s = %s WHERE %s = %s"
                                   % (column_name[0],column_name[1],good_agent,column_name[1],bad_agent))
                delete_agent = input("Delete AgentID %s? [y/n]" %bad_agent)
                if delete_agent == "y":
                    delete.execute("DELETE FROM agent WHERE AgentID = %s" % bad_agent)
                    db.commit()
                elif delete_agent == "n":
                    pass
                else:
                    print("Invalid command")
            elif update_agent == "n":
                pass
            else:
                print("Invalid command")
        except IndexError:
           print("Agent GUID set: ",agent," not found in database" )

# creates cursors and list of data from csv file, selects tables with columns and foreign keys that reference agentIDs
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    fetch_keys = db.cursor()
    fetch_references = db.cursor()
    fetch_id = db.cursor()
    update = db.cursor()
    delete = db.cursor()
    with open(".csv", newline='') as csvfile: # Input file path of csv
        guid_list = [row[0].split(",") for row in csv.reader(csvfile,delimiter=" ", quotechar="|")]
    fetch_keys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                       "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'")
    fetch_references.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE "
                             "COLUMN_NAME LIKE '%AgentID%' AND TABLE_NAME != 'AGENT'")
    agent_references = (fetch_keys.fetchall() + fetch_references.fetchall())
    update_agents(guid_list,fetch_id,agent_references,update,delete)

if __name__ == "__main__":
    main()