"""
Redmine Support #4173
Removes all attachments and references/links to attachments from the schema by selecting ID's from collection objects
with attachments and selecting all tables where attachments are referenced. Then, uses the ID's to delete the
references from the tables and finally deleting from the attachment table itself. Defaults to saving a file of the
attachmentID's to be deleted (with timestamp in filename), supports option to print the attachmentIDs to be deleted to
screen. Defaults to not actually deleting the attachments unless prompted with --delete argument .
"""
import pymysql
from csvwriter import write_report
import argparse
import datetime

# selects AttachmentIDs that reference a collection object and are of image/jpeg type
def select_attachments(db):
    db_attachments = db.cursor()
    db_attachments.execute("SELECT A.AttachmentID FROM collectionobjectattachment C INNER JOIN attachment A ON "
                           "A.AttachmentID = C.AttachmentID WHERE A.MimeType LIKE 'image/jpeg'")
    return db_attachments.fetchall()

# selects tables that references attachmentID
def select_references(db):
    db_reference = db.cursor()
    db_reference.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA='specify'"
                         " AND REFERENCED_COLUMN_NAME LIKE 'AttachmentID' and table_name != 'attachment'")
    return db_reference.fetchall()

# deletes any entry that references the attachmentID, then deletes attachmentID from the schema, handles any conflicts
def delete_attachments(db,attachments):
    db_delete_reference = db.cursor()
    db_delete_attachment = db.cursor()
    for record in attachments:
        for table in select_references(db):
            db_delete_reference.execute("DELETE FROM %s WHERE AttachmentID = %s" % (table[0], record[0]))
        db_delete_attachment.execute("DELETE FROM attachment WHERE AttachmentID = %s" % record[0])
        db.commit()
    print("%s attachments deleted" % len(attachments))

# calls on functions and creates argument parser commands
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--username", action="store", dest ="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password",required= True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database", required=True)
    parser.add_argument("--show", action= "store_true", dest="show", help= "Print attachments to be deleted to screen")
    parser.add_argument("--delete",action="store_true",dest="delete", help= "Delete attachments")
    parser.add_argument("--report", action="store_true",dest="report", default=True, help="(default) Creates report of attachmentIDs that will be deleted")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    show = args.show
    delete = args.delete
    report= args.report
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    attachments = select_attachments(db)
    if show:
        for image in attachments:
            print(image[0])
    if delete:
        try:
            delete_attachments(db,attachments)
        except pymysql.err.DatabaseError:
            print("Error when trying to delete attachment links")
    if report:
        file_name = "AttachmentsToDelete[%s]" % (datetime.date.today())
        heading = ["Attachment ID"]
        write_report(file_name, heading, attachments)
        if not delete:
            print("No changes made, report of attachmentIDs to be deleted saved as %s.csv" % file_name)
            return print("See -h for more options")
        return print("Report saved as '%s.csv'" % file_name)

if __name__ == "__main__":
    main()