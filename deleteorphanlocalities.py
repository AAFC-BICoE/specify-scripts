"""
Deletes localities that are not attached to any collection object by selecting the "orphan
LocalityID's", updating any references of the ID in the schema to NULL, then deleting the locality.
Defaults to saving a file of the ID's to be deleted unless prompted by the --delete argument.
"""
import argparse
import datetime
import pymysql
from csvwriter import write_report

def foreign_keys(database):
    # Selects all tables where the localityID is referenced as a foreign key
    database_fetch_references = database.cursor()
    database_fetch_references.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                                      "WHERE CONSTRAINT_SCHEMA = 'specify' "
                                      "AND REFERENCED_COLUMN_NAME = 'LocalityID'")
    return database_fetch_references.fetchall()

def orphan_ids(database):
    # Selects all localityID's that are not attached to a collection object
    database_orphan_ids = database.cursor()
    database_orphan_ids.execute("SELECT L.LocalityID FROM locality L LEFT JOIN collectingevent C "
                                "ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL")
    return database_orphan_ids.fetchall()

def delete_orphans(database, orphans, referenced_tables, integrity_error):
    # Sets any reference of orphan localities in the schema to NULL then deletes locality, if
    # Conflicts occur due to foreign_key restrictions, LocalityID is added to the conflict list
    database_remove_reference = database.cursor()
    database_delete = database.cursor()
    conflicts = []
    for record in orphans:
        for table_name in referenced_tables:
            database_remove_reference.execute(
                "UPDATE %s SET LocalityID = NULL WHERE LocalityID = '%s'"
                % (table_name[0], record[0]))
        try:
            database_delete.execute("DELETE FROM locality WHERE LocalityID = '%s'" % (record[0]))
            database.commit()
        except integrity_error:
            conflicts += [record[0]]
            continue
    return conflicts

def main():
    # Creates command line arguments and coordinates calls to functions
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username",
                        help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password",
                        help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="Name of MySQL specify database", required=True)
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Print Locality ID's to be deleted to screen")
    parser.add_argument("--delete", action="store_true", dest="delete",
                        help="Delete orphan localities")
    parser.add_argument("--report", action="store_true", default=True, dest="report",
                        help="(default) Create a report of what localities will be deleted")
    args = parser.parse_args()
    show = args.show
    delete = args.delete
    report = args.report
    integrity_error = pymysql.err.IntegrityError
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database, see -h for more options")
    orphans = orphan_ids(database)
    if show:
        for record in orphans:
            print(record[0])
    if delete:
        referenced_tables = foreign_keys(database)
        conflicts = delete_orphans(database, orphans, referenced_tables, integrity_error)
        if conflicts:
            file_name = ("OrphanLocalityConflicts[%s]" % (datetime.date.today()))
            write_report(file_name, ["LocalityID"], [conflicts])
            print("%s conflicts occurred when trying to delete, report saved as %s.csv"
                  % (len(conflicts), file_name))
            print("%s localities successfully deleted" % (int(len(orphans)-len(conflicts))))
        else:
            print("%s localities successfully deleted" % len(orphans))
    if report:
        file_name = ("LocalitiesDeleted[%s]" % (datetime.date.today()))
        write_report(file_name, ["Locality ID"], orphans)
        if not delete:
            print("No changes made, report of localities to be deleted saved as %s" % file_name)
            return print("See -h for more options")
        return print("Report saved as '%s.csv'" % file_name)
    return None

if __name__ == "__main__":
    main()
