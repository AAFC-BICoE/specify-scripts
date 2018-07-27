"""
Redmine Support #12199
Deletes localities that are not attached to any collectionobject by selecting the orphan localityID's then updating any
references of the localityID in the schema to NULL, then deletes the locality from schema. Defaults to saving a file of
the locality ID's to be deleted (with timestamp in filename) and supports option to print locality ID's to scree.
Defaults to not actually deleting attachments unless prompted with --delete argument.
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
    for iD in orphans:
        for tableName in referenced_tables:
            db_remove_reference.execute("UPDATE %s SET LocalityID=NULL WHERE LocalityID=%s" % (tableName[0],iD[0]))
        db_delete.execute('DELETE FROM locality WHERE LocalityID=%s' % (iD[0]))
        db.commit()
    print('%s orphan localities deleted' % len(orphans))

# calls on appropriate functions, connects to database via command line arguments
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required= True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required= True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database", required= True)
    parser.add_argument("--show", action="store_true", dest="show", help="Print Locality ID's to be deleted to screen")
    parser.add_argument("--delete", action="store_true", dest="delete", help="Delete orphan localities")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    show= args.show
    delete = args.delete
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        print('Error connecting to database, try again')
        return
    orphans = orphan_ids(db)
    # writes a csv file containing the locality ID's passed in
    file_name = ("LocalitiesDeleted[%s]" % (datetime.date.today()))
    write_report(file_name, ["Locality ID"], orphans)
    if show:
        for iD in orphans:
            print(iD)
    try:
        if delete:
            delete_orphans(db,orphans)
    except pymysql.err.DatabaseError:
        print("Error when trying to delete orphan localities")
    print("Report saved as '%s.csv'" % file_name)

if __name__ == "__main__":
    main()