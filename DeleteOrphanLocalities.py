"""
Redmine Support #12199
Deletes localities that are not attached to any collectionobject by selecting the orphan localityID's then updating any
references of the localityID in the schema to NULL, then deletes the locality from schema. Gives user the option to
create a csv file of the locality ID's of the orphans that will be deleted, and/or a csv file of any conflicts that
occur while deleting.
"""
import pymysql as MySQLdb
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

# calls on appropriate functions and displays user options
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    orphans = orphan_ids(db)
    print('%s orphan localities found' % len(orphans))
    delete_all = input('Delete all? [y/n/save] ')
    if delete_all == 'y':
        delete_orphans(db,orphans)
    elif delete_all == 'save':
        # writes a csv file containing the locality ID's passed in
        write_report("LocalitiesToBeDeleted",["Locality ID"], orphans)
        print("Report saved as '%s.csv'" % file_name)
    elif delete_all == "n":
        pass
    else:
        print("Invalid command")
        main()

if __name__ == "__main__":
    main()