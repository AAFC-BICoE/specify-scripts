"""
Reading from a csv file containing two GUID's, the "Bad Agent" is deleted from the schema by
changing references to the "Good Agent" GUID. Default is to not replace the agents unless prompted
by the --replace argument.

NOTE: csv format should have the GUID of the agent that will be deleted ("Bad Agent") in the FIRST
column, and the GUID of the agent that references will be switched to ("Good Agent") in the SECOND
column of the same row.
"""
import argparse
import csv
import datetime
import pymysql
from csvwriter import write_report

def foreign_keys(database):
    # Selects the table and column names that reference AgentID by foreign key
    db_foreign_keys = database.cursor()
    db_foreign_keys.execute("SELECT TABLE_NAME, COLUMN_NAME FROM "
                            "INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                            "WHERE CONSTRAINT_SCHEMA = 'specify' "
                            "AND REFERENCED_COLUMN_NAME LIKE '%AgentID%'")
    return db_foreign_keys.fetchall()

def agent_info(database, guid):
    # Selects AgentID corresponding to passed in GUID
    db_agent_id = database.cursor()
    db_agent_id.execute("SELECT AgentID FROM agent WHERE GUID = '%s'" % guid)
    return db_agent_id.fetchall()

def update_agents(database, guid_list, agent_references, integrity_error):
    # Updates all instances of the "Bad Agent' to the "Good Agent", then deletes the Bad Agent. If
    # Any conflicts caused by foreign keys occur, ID's are added to a conflict list
    db_update = database.cursor()
    db_delete = database.cursor()
    agent_list, conflicts = [], []
    for agent in guid_list:
        try:
            bad_agent = agent_info(database, agent[0])[0][0]
            good_agent = agent_info(database, agent[1])[0][0]
        except IndexError:
            conflicts += [agent]
            continue
        for table_name, column_name in agent_references:
            db_update.execute("UPDATE %s SET %s = '%s' WHERE %s = '%s'"
                              % (table_name, column_name, good_agent, column_name, bad_agent))
        try:
            agent_list += [(str(bad_agent), str(good_agent))]
            db_delete.execute("DELETE FROM agent WHERE AgentID = '%s'" % bad_agent)
            database.commit()
        except integrity_error:
            conflicts += [agent]
    return agent_list, conflicts

def main():
    # Creates command line arguments, reads GUID data from csv file, coordinates function calling
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username",
                        help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password",
                        help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="MySQL specify database name", required=True)
    parser.add_argument("-csv", action="store", dest="file_name",
                        help="Name of csv file containing agent GUIDs", required=True)
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Print the agentID's to screen")
    parser.add_argument("--replace", action="store_true", dest="replace",
                        help="Replace agents")
    parser.add_argument("--report", action="store_true", dest="report", default=True,
                        help="(default) Creates report of what will be done to the agentIDs")
    args = parser.parse_args()
    file_name = args.file_name
    show = args.show
    replace = args.replace
    report = args.report
    integrity_error = pymysql.err.IntegrityError
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database, see -h for more options")
    try:
        with open("%s" % file_name, newline="")  as csvfile:
            guid_list = [row[0].split(",") for row in csv.reader(
                csvfile, delimiter=" ", quotechar="|")]
    except FileNotFoundError:
        return print("%s not found" % file_name)
    references = foreign_keys(database)
    if replace:
        agent_list, conflicts = update_agents(database, guid_list, references, integrity_error)
        if show:
            for id1, id2 in agent_list:
                print("Agent Deleted:", id1, "Agent Replaced To:", id2)
        if conflicts:
            file_name = ("AgentConflicts[%s]" % (datetime.date.today()))
            write_report(file_name, ["Bad Agent GUID", "Good Agent GUID"], conflicts)
            print("%s conflict(s) occurred\nReport saved as %s.csv" % (len(conflicts), file_name))
        if agent_list:
            file_name = "AgentsReplaced[%s]" % (datetime.date.today())
            write_report(file_name,
                         ["Removed AgentID (Bad AgentID)", "Replaced AgentID (Good AgentID)"],
                         agent_list)
            print("%s agent(s) successfully replaced\nReport saved as %s.csv"
                  % (len(agent_list), file_name))
    if report:
        if not replace:
            print("No changes made, see -h for more options")
    return None

if __name__ == "__main__":
    main()
