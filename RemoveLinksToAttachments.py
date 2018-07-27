"""
Redmine Support #4173
Removes all attachments and references/links to attachments from the schema by selecting ID's from collection objects
with attachments and selecting all tables where attachments are referenced. Then, uses the ID's to delete the
references from the tables and finally deleting from the attachment table itself. Gives user the option to save/show
the attachmentID's that are going to be deleted in a csv file, time stamps the csv file name.
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

# writes the data passed in to a csv file
def save_report(file_name,data):
    write_report(file_name,["Attachment ID"],data)
    print("Report saved as '%s.csv'" % file_name)

# deletes any entry that references the attachmentID, then deletes attachmentID from the schema, handels any conflicts
def delete_attachments(db,attachments):
    db_delete_reference = db.cursor()
    db_delete_attachment = db.cursor()
    conflicts = []
    for record in attachments:
        try:
            for table in select_references(db):
                db_delete_reference.execute("DELETE FROM %s WHERE AttachmentID = %s" % (table[0], record[0]))
            db_delete_attachment.execute("DELETE FROM attachment WHERE AttachmentID = %s" % record[0])
            db.commit()
        except:
            conflicts += [record[0]]
    if len(conflicts) == 0:
        print(attachments)
        print("%s attachments deleted" % len(attachments))
        print("no conflicts")
        return
    print("%s attachments deleted" % (int(len(attachments))-int(len(conflicts))))
    display = input("Show or save %s conflict(s)? [show/save/n]" % len(conflicts))
    if display == "show":
        for c in conflicts:
            print(c)
    elif display == "save":
        save_report("AttachmentConflicts",conflicts)
    elif display == "n":
        pass
    else:
        print("Invalid command")

# gives user option of what to do with the attachments
def delete_command(attachments,db):
    delete_option = input("%s attachments found, delete all? [y/n/show]" % len(attachments))
    if delete_option == "y":
        delete_attachments(db, attachments)
    elif delete_option == "show":
        show = input("Show %s attachments or save to csv file? [show/save]" % len(attachments))
        if show == "show":
            for name in attachments:
                print(name[0])
            delete_command(attachments,db)
        elif show == "save":
            save_report(("AttachmentsToDelete[%s]" % (datetime.date.today())),attachments)
            delete_command(attachments,db)
        else:
            print("Invalid command")
            delete_command(attachments,db)
    elif delete_option== "n":
        pass
    else:
        print("Invalid command")
        delete_command(attachments,db)

# calls on functions and creates argument parser commands
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--username", action="store", dest ="username", help="MySQL username", required=True)
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
    attachments = select_attachments(db)
    delete_command(attachments, db)

if __name__ == "__main__":
    main()