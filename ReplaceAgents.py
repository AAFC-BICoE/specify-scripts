# Reading from a csv file containing two GUID's, the 'Bad Agent' is deleted from the schema by changing all references
# In the schema to the specified 'Good Agent'. Defaults to not actually replacing the agents unless prompted by the
# --replace argument. NOTE: csv format should have the GUID of the agent that will be deleted FIRST ('Bad Agent'), then
#  The GUID of the agent that the info will be changed too ('Good Agent') SECOND in the same row.
import pymysql, argparse, csv, datetime, sys
from csvwriter import write_report

# Selects the table and column names that are referenced by agentID
def foreign_keys(db):
    db_foreign_keys = db.cursor()
    db_foreign_keys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                            "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'")
    return db_foreign_keys.fetchall()

# Selects agentIDs corresponding to the GUID passed in
def agent_info(db, guid):
    db_agent_id= db.cursor()
    db_agent_id.execute("SELECT AgentID FROM agent WHERE GUID = '%s' " % guid)
    return db_agent_id.fetchall()

# Updates all instances of the 'bad agent' with the good agent then deletes the bad agent. If there are any conflicts
# Caused by foreign keys then the agentID's are added to the conflict list.
def update_agents(db, guid_list, agent_references, integrity_error):
    db_update = db.cursor()
    db_delete = db.cursor()
    agent_list, conflicts = [], []
    for agent in guid_list:
        try:
            bad_agent = agent_info(db,agent[0])[0][0]
            good_agent = agent_info(db,agent[1])[0][0]
        except IndexError:
            conflicts += [agent]
            continue
        for table_name,column_name in agent_references:
          db_update.execute("UPDATE %s SET %s = '%s' WHERE %s = '%s'"
                            % (table_name, column_name, good_agent, column_name, bad_agent))
        try:
            agent_list += [(str(bad_agent), str(good_agent))]
            db_delete.execute("DELETE FROM agent WHERE AgentID = '%s'" % bad_agent)
            db.commit()
        except integrity_error:
            conflicts += [agent]
    return agent_list, conflicts

# Creates command line arguments, reads GUID data from csv file, coordinates function calling
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required= True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="MySQL specify database name", required=True)
    parser.add_argument("-csv", action="store", dest="file_name",
                        help ="Name of .csv file containing agent GUIDs", required= True)
    parser.add_argument("--show", action="store_true", dest ="show",
                        help="Print the agentID's to screen")
    parser.add_argument("--replace", action="store_true",dest="replace", help="Replace agents")
    parser.add_argument("--report",action="store_true",dest="report",default=True,
                        help="(default) Creates report of what will be done to the agentIDs")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    file_name = args.file_name
    show = args.show
    replace = args.replace
    report = args.report
    integrity_error = pymysql.err.IntegrityError
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database, see -h for more options")
    try:
        with open("%s"% file_name, newline='')  as csvfile:
            guid_list = [row[0].split(",") for row in csv.reader(csvfile, delimiter=" ", quotechar="|")]
    except FileNotFoundError:
        return print("%s not found" % file_name)
    references = foreign_keys(db)
    if replace:
        agent_list,conflicts = update_agents(db, guid_list, references, integrity_error)
        if show:
           for id1,id2 in agent_list:
               print("Agent Deleted:",id1, "Agent Replaced To:",id2)
        if len(conflicts) != 0:
            file_name = ("AgentConflicts[%s]" % (datetime.date.today()))
            write_report(file_name,["Bad Agent GUID","Good Agent GUID"], conflicts)
            print("%s conflict(s) occurred\nReport saved as %s.csv" % (len(conflicts), file_name))
        if len(agent_list) != 0:
            file_name = "AgentsReplaced[%s]" % (datetime.date.today())
            write_report(file_name,["Removed AgentID (Bad AgentID)","Replaced AgentID (Good AgentID)"],agent_list)
            print("%s agent(s) successfully replaced\nReport saved as %s.csv" % (len(agent_list),file_name))
    if report:
        if not replace:
            print("No changes made, see -h for more options")

if __name__ == "__main__":
    main()
