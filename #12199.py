import pymysql as MySQLdb

db = MySQLdb.connect("localhost",#username, #password, #specify database name)

fetchLocalityIDs = db.cursor()
fetchLocalityIDKeys = db.cursor()
removeReference = db.cursor()
deleteLocality = db.cursor()

fetchLocalityIDKeys.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME = 'LocalityID'") #selects all tables where the locaityID is a foreign key
fetchLocalityIDs.execute("SELECT L.LocalityID FROM locality L LEFT JOIN collectingevent C ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL ") #selects all localityID's that are not attached to a record

localityKey = fetchLocalityIDKeys.fetchall()
localityID = fetchLocalityIDs.fetchall()

for iD in localityID:
    for tableName in localityKey:
        removeReference.execute('UPDATE %s SET LocalityID = NULL WHERE LocalityID = %s' % (tableName[0],iD[0])) #sets any references to the orphan locality in the database to NULL
        db.commit()

    deleteLocality.execute('DELETE FROM locality WHERE LocalityID = %s' % (iD[0])) #deletes the orphan locality record
    db.commit()

db.close()
