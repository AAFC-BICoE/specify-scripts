"""
Tests the RemoveLinksToAttachments script for 4 different cases. First creates a test database with 4 tables, populated
with test data to be passed into the original script. Tests are preformed to confirm that attachmentID's with mimeType
'image/jpeg' are selected properly, that attachmentID's that create no conflicts are removed properly, that when the
function is called with no conflicts an empty conflict list is returned, and that when the function is called with
conflicts a non empty conflict list is returned
"""
import RemoveLinksToAttachments, os, sqlite3, unittest

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """ creates the test database and a test table, inserts sample data into test table """
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE attachment 
                            (AttachmentID NOT NULL, MimeType, data2, data3, PRIMARY KEY (AttachmentID))""")
        conn.commit()
        test_attachment_data = [("1", "image/jpeg", "b", "c"), ("2", "otherfile", "e", "f"),
                                ("3", "image/jpeg", "h", "i"), ("4", "image/jpeg", "k", "l")]
        cursor.executemany("""INSERT INTO attachment VALUES (?,?,?,?)""", test_attachment_data)
        conn.commit()
        cursor.execute("""CREATE TABLE collectionobjectattachment 
                      (AttachmentID,data1,data2,data3,FOREIGN KEY(AttachmentID) REFERENCES attachment(AttachmentID))""")
        conn.commit()
        test_collectionobjectattachment_data = [("1","a","b","c"),("2","b","c","d"),("4","c","d","e"),("3","d","e","f")]
        cursor.executemany("""INSERT INTO collectionobjectattachment VALUES (?,?,?,?)""" ,
                           test_collectionobjectattachment_data)
        conn.commit()
        cursor.execute("""CREATE TABLE testdata1 
                      (AttachmentID,data1,data2,data3,FOREIGN KEY(AttachmentID) REFERENCES attachment(AttachmentID))""")
        test_testdata1 = [("1","a","b","c"),("2","b","c","d"),("4","c","d","e"),("3","d","e","f")]
        cursor.executemany("""INSERT INTO testdata1 VALUES (?,?,?,?)""", test_testdata1)
        conn.commit()
        cursor.execute("""CREATE TABLE testdata2 
                      (AttachmentID,data1,data2,data3,FOREIGN KEY(AttachmentID) REFERENCES attachment(AttachmentID))""")
        test_testdata2 = [("1", "i", "b", "c"), ("4", "o", "e", "f"), ("2", "g", "h", "i"), ("3", "j", "k", "l")]
        cursor.executemany(""" INSERT INTO testdata2 VALUES (?,?,?,?)""", test_testdata2)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        """ deletes the test database"""
        os.remove("specifytest.db")

    def test_select_attachments(self):
        """ tests to confirm attachmentID's that correspond to a image/jpeg MimeType are being selected properly"""
        conn = sqlite3.connect("specifytest.db")
        actual = RemoveLinksToAttachments.select_attachments(conn)
        expected = [("1",),("4",),("3",)]
        self.assertEqual(expected,actual)

    def test_delete_attachments_attachment_table(self):
        """ tests to confirm that attachmentIDs are deleted with no conflicts properly"""
        exception = sqlite3.IntegrityError
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        test_referenced_tables = [("testdata1",),("testdata2",),("collectionobjectattachment",)]
        test_attachments = [("1",),("2",),("3",)]
        RemoveLinksToAttachments.delete_attachments (conn, test_referenced_tables,test_attachments,exception)
        cursor.execute("""SELECT * FROM attachment where AttachmentID = 1""")
        actual = cursor.fetchall()
        self.assertFalse(actual)

    def test_delete_attachments_no_conflicts(self):
        """ tests to confirm that when attachments are deleted with no conflicts, corrected values are returned"""
        exception = sqlite3.IntegrityError
        conn = sqlite3.connect("specifytest.db")
        test_referenced_tables = [("testdata1",),("testdata2",),("collectionobjectattachment",)]
        test_attachments = [("1",),("2",),("3",)]
        actual = RemoveLinksToAttachments.delete_attachments (conn, test_referenced_tables,test_attachments,exception)
        expected = []
        self.assertEqual(expected,actual)

    def test_delete_attachments_conflicts(self):
        """ tests to confirm that when attachments are deleted and conflicts occur, corrected values are returned"""
        exception = sqlite3.IntegrityError
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("""PRAGMA foreign_keys = ON""")
        conn.commit()
        test_referenced_tables = [("testdata1",)]
        test_attachments = [("1",),("2",),("3",),("4",)]
        actual = RemoveLinksToAttachments.delete_attachments (conn, test_referenced_tables,test_attachments,exception)
        expected = ["1","2","3","4"]
        self.assertEqual(expected,actual)

if __name__ == "__main__":
    unittest.main()
