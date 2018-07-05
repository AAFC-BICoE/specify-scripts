"""
Deletes localities that are not attached to any collectionobject by selecting the orphan localityID's then updating any
references of the localityID in the schema to NULL, then deleting locality from schema.
"""
import pymysql as MySQLdb

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchLocalityIDs = db.cursor()
fetchLocalityIDKeys = db.cursor()
removeReference = db.cursor()
deleteLocality = db.cursor()

# selects all tables where the locaityID is referenced as a foreign key
fetchLocalityIDKeys.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                            "WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME = 'LocalityID'")
localityKey = fetchLocalityIDKeys.fetchall()

# selects all localityID's that are not attached to a record
fetchLocalityIDs.execute("SELECT L.LocalityID FROM locality L LEFT JOIN collectingevent C "
                         "ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL ")

# sets any references to the orphan locality in the database to NULL then deletes the orphan locality record
for iD in fetchLocalityIDs.fetchall():
    for tableName in localityKey:
        removeReference.execute("UPDATE %s SET LocalityID = NULL WHERE LocalityID = %s" % (tableName[0],iD[0]))
    deleteLocality.execute('DELETE FROM locality WHERE LocalityID = %s' % (iD[0]))
    db.commit()

db.close()
