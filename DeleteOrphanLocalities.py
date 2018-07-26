"""
Redmine Support #12199
Deletes localities that are not attached to any collectionobject by selecting the orphan localityID's then updating any
references of the localityID in the schema to NULL, then deletes the locality from schema. Gives user the option to
create a csv file of the locality ID's of the orphans that will be deleted, and/or a csv file of any conflicts that
occur while deleting. Supports command line arguments
"""
import pymysql
import argparse
import datetime
from csvwriter import write_report

# selects all tables where the localityID is referenced as a foreign key
def foreign_keys(db):
    db_fetch_references= db.cursor()
    db_fetch_references.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                                "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME = 'LocalityID'")
    return db_fetch_references.fetchall()

# selects all localityID's that are not attached to a collection object
def orphan_ids(db):
    db_orphan_ids = db.cursor()
    db_orphan_ids.execute("SELECT L.LocalityID FROM locality L LEFT JOIN collectingevent C "
                             "ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL ")
    return db_orphan_ids.fetchall()

# sets any references to the orphan locality in the database to NULL then deletes the orphan locality record
def delete_orphans(db,orphans):
    db_remove_reference = db.cursor()
    db_delete = db.cursor()
    referenced_tables = foreign_keys(db)
    conflicts = []
    for iD in orphans:
        try:
            for tableName in referenced_tables:
                db_remove_reference.execute("UPDATE %s SET LocalityID=NULL WHERE LocalityID=%s" % (tableName[0],iD[0]))
            db_delete.execute('DELETE FROM locality WHERE LocalityID=%s' % (iD[0]))
            db.commit()
        except:
            conflicts += [iD[0]]
    if len(conflicts) == 0:
        print('%s localities deleted' % len(orphans))
        print("No conflicts")
    else:
        print("%s localities deleted" % (int(len(orphans)) - int(len(conflicts))))
        conflict_report = input("%s conflicts occurred [save/show/n] " % len(conflicts))
        if conflict_report == 'save':
            # writes a csv file containing the locality ID's passed in
            write_report("OrphanConflicts",["Locality ID"],conflicts)
            print("Report saved as '%s.csv'" % file_name)
        elif conflict_report == "show":
            for lid in conflicts:
                print(lid)

# calls on appropriate functions, displays user options connects to database via command line arguments
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required= True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required= True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database", required= True)
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        print('Error connecting to database, try again')
        return
    orphans = orphan_ids(db)
    print('%s orphan localities found' % len(orphans))
    delete_all = input('Delete all? [y/n/save] ')
    if delete_all == 'y':
        delete_orphans(db,orphans)
    elif delete_all == 'save':
        # writes a csv file containing the locality ID's passed in
        file_name = ("LocalitiesToBeDeleted[%s]" % (datetime.date.today()))
        write_report(file_name,["Locality ID"], orphans)
        print("Report saved as '%s.csv'" % file_name)
    elif delete_all == "n":
        pass
    else:
        print("Invalid command")
        main()

if __name__ == "__main__":
    main()