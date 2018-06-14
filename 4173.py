import pymysql as MySQLdb

db = MySQLdb.connect("localhost", #username, #password, #specifyDatabaseName)

fetchAttachmentID = db.cursor()
fetchTables = db.cursor()
deleteAttachmentReference = db.cursor()
deleteAttachment = db.cursor()

fetchAttachmentID.execute("SELECT A.AttachmentID FROM collectionobjectattachment C INNER JOIN attachment A ON A.AttachmentID = C.AttachmentID WHERE A.MimeType LIKE 'image/jpeg'")
attachmentID = fetchAttachmentID.fetchall() #selects AttachmentIDs that reference a collection object and are a jpeg

fetchTables.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME LIKE 'AttachmentID'")
tablesToDelete = fetchTables.fetchall() #selects tables that references attachmentID

for record in attachmentID:
    for tableName in tablesToDelete:
        deleteAttachmentReference.execute("DELETE FROM %s WHERE AttachmentID = %s" % (tableName[0], record[0])) #deletes any entry that reference the attachment

    deleteAttachment.execute("DELETE FROM attachment WHERE AttachmentID = %s" % record[0]) #deletes attachment from the attachment table
    db.commit()

db.close()