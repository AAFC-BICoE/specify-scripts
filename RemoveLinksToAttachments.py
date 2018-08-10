"""
Removes all references to image/jpeg MimeTypes from the schema by selecting attachmentID's from collection objects
referencing a image/jpeg. Then, uses the ID's to delete entries from the referenced tables, then deletes the entry from
the attachment table. Defaults to saving a file of the attachmentID's to be deleted (with timestamp in filename), unless
prompted to delete with --delete argument. If any conflicts are found while attempting to delete, a report of the
conflicts is created (with timestamp in filename). Supports option to print the attachmentIDs to be deleted to screen.
"""
import pymysql, argparse, datetime
from csvwriter import write_report

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
def delete_attachments(db,referenced_tables,attachments, exception):
    db_delete_reference = db.cursor()
    db_delete_attachment = db.cursor()
    conflicts = []
    for record in attachments:
        for table in referenced_tables:
            try:
                db_delete_reference.execute("DELETE FROM %s WHERE AttachmentID = '%s'" % (table[0], record[0]))
            except exception:
                # will be thrown if a foreign key constraint fails
                conflicts += [record[0]]
                continue
        try:
            db_delete_attachment.execute("DELETE FROM attachment WHERE AttachmentID = '%s'" % record[0])
            db.commit()
        except exception:
            # will be thrown if a foreign key constraint fails
            conflicts += [record[0]]
            continue
    return conflicts

# calls on functions and creates argument parser commands
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--username", action="store", dest ="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password",required= True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL specify database", required=True)
    parser.add_argument("--show", action= "store_true", dest="show", help= "Print attachments to be deleted to screen")
    parser.add_argument("--delete",action="store_true",dest="delete", help= "Delete attachments")
    parser.add_argument("--report", action="store_true",dest="report", default=True,
                        help="(default) Creates report of attachmentIDs that will be deleted")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    show = args.show
    delete = args.delete
    report= args.report
    exception = pymysql.err.IntegrityError
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    attachments = select_attachments(db)
    if show:
        for image in attachments:
            print(image[0])
    if delete:
        referenced_tables = select_references(db)
        conflicts = delete_attachments(db,referenced_tables,attachments,exception)
        if len(conflicts) == 0:
            print("%s conflicts, %s attachments deleted" % (len(conflicts), len(attachments)))
        else:
            print( "%s conflicts, %s attachments deleted" % ((int(len(attachments)) - int(len(conflicts))), len(attachments)))
            file_name = "AttachmentConflicts[%s]" % (datetime.date.today())
            heading = ["Attachment ID"]
            write_report(file_name, heading, conflicts)
            print("Report saved as %s.csv" % file_name)
    if report:
        if delete:
            file_name = "AttachmentsDeleted[%s]"  % (datetime.date.today())
        else:
            file_name = "AttachmentsToDelete[%s]" % (datetime.date.today())
        heading = ["Attachment ID"]
        write_report(file_name, heading, attachments)
        if not delete:
            print("No changes made, report of %s attachmentIDs to be deleted saved as %s.csv" % (len(attachments),file_name))
            return print("See -h for more options")
        return print("Report saved as '%s.csv'" % file_name)

if __name__ == "__main__":
    main()
