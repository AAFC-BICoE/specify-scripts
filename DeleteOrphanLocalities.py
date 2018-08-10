# Deletes localities that are not attached to any collectionobject by selecting the orphan localityID's then updating
# Any references of the localityID in the schema to NULL. Deletes the locality from schema if prompted. Defaults to
# Saving a file of the locality ID's to be deleted (with timestamp in filename) and not actually deleting attachments
# Unless prompted with --delete argument. If any conflicts occur, a conflict report is created.
import pymysql, argparse, datetime
from csvwriter import write_report

# Selects all tables where the localityID is referenced as a foreign key
def foreign_keys(db):
    db_fetch_references= db.cursor()
    db_fetch_references.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                                "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME = 'LocalityID'")
    return db_fetch_references.fetchall()

# Selects all localityID's that are not attached to a collection object
def orphan_ids(db):
    db_orphan_ids = db.cursor()
    db_orphan_ids.execute("SELECT L.LocalityID FROM locality L LEFT JOIN collectingevent C "
                             "ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL")
    return db_orphan_ids.fetchall()

# Sets any references to the orphan locality in the database to NULL then deletes the orphan locality record, if
# Conflicts occur due to foreign_key restrictions, the localityID is added to the conflict list
def delete_orphans(db,orphans, referenced_tables, integrity_error):
    db_remove_reference = db.cursor()
    db_delete = db.cursor()
    conflicts = []
    for iD in orphans:
        for table_name in referenced_tables:
           db_remove_reference.execute("UPDATE %s SET LocalityID = NULL WHERE LocalityID = '%s'" %(table_name[0],iD[0]))
        try:
            db_delete.execute("DELETE FROM locality WHERE LocalityID = '%s'" % (iD[0]))
            db.commit()
        except integrity_error:
            conflicts += [iD[0]]
            continue
    return conflicts

# Calls on functions and creates argument parser commands
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required= True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required= True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="Name of MySQL specify database", required= True)
    parser.add_argument("--show", action="store_true", dest="show", help="Print Locality ID's to be deleted to screen")
    parser.add_argument("--delete", action="store_true", dest="delete", help="Delete orphan localities")
    parser.add_argument("--report", action="store_true", default = True, dest="report",
                        help="(default) Create a report of what localities will be deleted")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    show= args.show
    delete = args.delete
    report = args.report
    integrity_error = pymysql.err.IntegrityError
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database, try again")
    orphans = orphan_ids(db)
    if show:
        for iD in orphans:
            print(iD[0])
    if delete:
        referenced_tables = foreign_keys(db)
        conflicts = delete_orphans(db,orphans,referenced_tables,integrity_error)
        if len(conflicts) != 0:
            file_name = ("OrphanLocalityConflicts[%s]" % (datetime.date.today()))
            write_report(file_name,["LocalityID"],[conflicts])
            print("%s conflicts occurred when trying to delete, report saved as %s.csv" % (len(conflicts),file_name))
            print("%s localities successfully deleted" % (int(len(orphans)-len(conflicts))))
        else:
            print("%s localities successfully deleted" % len(orphans))
    if report:
        file_name = ("LocalitiesDeleted[%s]" % (datetime.date.today()))
        write_report(file_name, ["Locality ID"], orphans)
        if not delete:
            print("No changes made, report of orphan localities to be deleted saved as %s" % file_name)
            return print("See -h for more options")
        return print("Report saved as '%s.csv'" % file_name)

if __name__ == "__main__":
    main()
