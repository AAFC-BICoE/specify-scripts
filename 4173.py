"""
Removes all attachments and references/links to attachments from the schema by selecting ID's from collection objects
with attachments and selecting all tables where attachments are referenced. Then, uses the ID's to delete the
references from the tables and finally deleting from the attachment table itself.
"""
import pymysql as MySQLdb

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetch_attachments = db.cursor()
fetch_tables = db.cursor()
delete_reference = db.cursor()
delete_attachment = db.cursor()

# selects AttachmentIDs that reference a collection object and are of jpeg type
fetch_attachments.execute("SELECT A.AttachmentID FROM collectionobjectattachment C "
                          "INNER JOIN attachment A ON A.AttachmentID = C.AttachmentID "
                          "WHERE A.MimeType LIKE 'image/jpeg'")

# selects tables that references attachmentID
fetch_tables.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA = 'specify' "
                    "AND REFERENCED_COLUMN_NAME LIKE 'AttachmentID' and table_name != 'attachment'")
table_names = fetch_tables.fetchall()

# deletes any entry that references the attachmentID, then deletes attachmentID from the schema
for record in fetch_attachments.fetchall():
    for table in table_names:
        delete_reference.execute("DELETE FROM %s WHERE AttachmentID = %s" % (table[0], record[0]))
    delete_attachment.execute("DELETE FROM attachment WHERE AttachmentID = %s" % record[0])
    #db.commit()
print("Complete")

db.close()