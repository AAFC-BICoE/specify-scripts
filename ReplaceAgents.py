"""
Redmine Support #5722
Reading from a csv file containing two GUID's, the specified 'Bad Agent' is deleted from the schema by changing all
references of the 'Bad Agent' to the specified 'Good Agent' using the database schema to look for references of 'AgentID'
in column names and foreign keys. Defaults to saving a csv file of what agentIDs will be deleted/updated, will only
actually preform the changes if '--replace' is added to the command line argument.
NOTE: csv format should have the GUID of the agent to be deleted FIRST, then the GUID of the agent that the info will be
changed to SECOND in the same row
"""
import pymysql
import argparse
import csv
import datetime
from csvwriter import write_report

# selects agentIDs corresponding to provided GUID's
def agent_info(db,guid):
    db_agent_id= db.cursor()
    db_agent_id.execute("SELECT AgentID FROM agent WHERE GUID = '%s' " % guid)
    return db_agent_id.fetchall()[0][0]

# updates instances of the 'bad agent' with the good agent then deletes the bad agent
def update_agents(guid_list,agent_references,db,show,replace):
    db_update = db.cursor()
    db_delete = db.cursor()
    agent_list = []
    for agent in guid_list:
        try:
            bad_agent = agent_info(db,agent[0])
            good_agent = agent_info(db,agent[1])
            agent_list += [(str(bad_agent),str(good_agent))]
            if show:
                print('Updating all instances of AgentID %s to AgentID %s' %(bad_agent,good_agent))
            if replace:
                for column_name in agent_references:
                    db_update.execute("UPDATE %s SET %s = %s WHERE %s = %s"
                                   % (column_name[0],column_name[1],good_agent,column_name[1],bad_agent))
                db_delete.execute("DELETE FROM agent WHERE AgentID = %s" % bad_agent)
                db.commit()
                print("Agent replaced")
        except IndexError:
           print("Agent GUID set: ",agent," not found in database" )
    return agent_list

# creates command line arguments, reads GUID data from csv file, selects schema information that references agentIDs
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required= True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="MySQL specify database name", required=True)
    parser.add_argument("-csv", action="store", dest="file_name", help ="Name of .csv file containing agent GUIDs", required= True)
    parser.add_argument("--show", action="store_true", dest ="show", help="Print the agentID's to screen")
    parser.add_argument("--replace", action="store_true",dest="replace",help="Replace agents")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    file_name = args.file_name
    show = args.show
    replace = args.replace
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    db_foreign_keys = db.cursor()
    db_references = db.cursor()
    try:
        with open("%s"% file_name, newline='')  as csvfile: # Input file path of csv
            guid_list = [row[0].split(",") for row in csv.reader(csvfile,delimiter=" ", quotechar="|")]
    except FileNotFoundError:
        return print("%s not found" % file_name)
    db_foreign_keys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                       "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'")
    db_references.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE "
                             "COLUMN_NAME LIKE '%AgentID%' AND TABLE_NAME != 'AGENT'")
    agent_references = (db_foreign_keys.fetchall() + db_references.fetchall())
    agent_list = update_agents(guid_list,agent_references,db,show,replace)
    name = "AgentsReplaced[%s]" % (datetime.date.today())
    heading =["Removed AgentID","AgentID"]
    write_report(name,heading,agent_list)
    print("Report saved as %s.csv" % name)

if __name__ == "__main__":
    main()