"""
Removes all references to image/jpeg MimeTypes from the schema by selecting AttachmentID's from
referenced collection objects. Uses the ID's to delete entries from the tables referenced by
foreign keys then deletes the entry from the attachment table. Saves a file of the AttachmentID's
to be deleted unless prompted to delete. A report of conflicts is created if any occur.
"""
import argparse
import datetime
import pymysql
from csvwriter import write_report

def select_attachments(database):
    # Selects AttachmentIDs that reference a collection object with image/jpeg MimeType
    database_attachments = database.cursor()
    database_attachments.execute("SELECT A.AttachmentID FROM collectionobjectattachment C "
                                 "INNER JOIN attachment A ON A.AttachmentID = C.AttachmentID "
                                 "WHERE A.MimeType LIKE 'image/jpeg'")
    return database_attachments.fetchall()

def select_references(database):
    # Selects tables that reference the column 'AttachmentID' by foreign key
    database_reference = database.cursor()
    database_reference.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                               "WHERE CONSTRAINT_SCHEMA='specify' "
                               "AND REFERENCED_COLUMN_NAME LIKE 'AttachmentID' "
                               "AND table_name != 'attachment'")
    return database_reference.fetchall()

def delete_attachments(database, referenced_tables, attachments, exception):
    # Deletes entries that reference AttachmentID columns, handles foreign key constraint conflicts
    database_delete_reference = database.cursor()
    database_delete_attachment = database.cursor()
    conflicts = []
    for record in attachments:
        for table in referenced_tables:
            try:
                database_delete_reference.execute("DELETE FROM %s WHERE AttachmentID = '%s'"
                                                  % (table[0], record[0]))
            except exception:
                conflicts += [record[0]]
                continue
        try:
            database_delete_attachment.execute("DELETE FROM attachment WHERE AttachmentID = '%s'"
                                               % record[0])
            database.commit()
        except exception:
            conflicts += [record[0]]
            continue
    return conflicts

def main():
    # Creates command line arguments and coordinates function calls
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username",
                        help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password",
                        help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="Name of MySQL specify database", required=True)
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Print attachments to be deleted to screen")
    parser.add_argument("--delete", action="store_true", dest="delete",
                        help="Delete attachments")
    parser.add_argument("--report", action="store_true", dest="report", default=True,
                        help="(default) Creates report of attachmentIDs that will be deleted")
    args = parser.parse_args()
    show = args.show
    delete = args.delete
    report = args.report
    exception = pymysql.err.IntegrityError
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print('Error connecting to database, try again')
    attachments = select_attachments(database)
    if show:
        for image in attachments:
            print(image[0])
    if delete:
        referenced_tables = select_references(database)
        conflicts = delete_attachments(database, referenced_tables, attachments, exception)
        if conflicts:
            print("%s conflicts, %s attachments deleted" % (len(conflicts), len(attachments)))
        else:
            print("%s conflicts, %s attachments deleted"
                  % ((int(len(attachments)) - int(len(conflicts))), len(attachments)))
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
            print("No changes made, report of %s attachmentIDs to be deleted saved as %s.csv"
                  % (len(attachments), file_name))
            return print("See -h for more options")
        return print("Report saved as '%s.csv'" % file_name)
    return None

if __name__ == "__main__":
    main()
