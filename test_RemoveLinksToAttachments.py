# Tests the RemoveLinksToAttachments across 4 cases. Creates and deletes test database.
import os
import sqlite3
import unittest
import RemoveLinksToAttachments

class TestDatabase(unittest.TestCase):
    # Testing the script RemoveLinksToAttachments.py

    def setUp(self):
        # Creates the test database, inserts sample data into test tables
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE attachment "
                       "(AttachmentID NOT NULL, MimeType, data2, data3, "
                       "PRIMARY KEY(AttachmentID))")
        conn.commit()
        test_attachment_data = [("1", "image/jpeg", "b", "c"), ("2", "otherfile", "e", "f"),
                                ("3", "image/jpeg", "h", "i"), ("4", "image/jpeg", "k", "l")]
        cursor.executemany("INSERT INTO attachment VALUES (?,?,?,?)", test_attachment_data)
        conn.commit()
        cursor.execute("CREATE TABLE collectionobjectattachment "
                       "(AttachmentID, data1, data2, data3, FOREIGN KEY(AttachmentID) "
                       "REFERENCES attachment(AttachmentID))")
        conn.commit()
        test_collectionobjectattachment_data = [("1", "a", "b", "c"), ("2", "b", "c", "d"),
                                                ("4", "c", "d", "e"), ("3", "d", "e", "f")]
        cursor.executemany("INSERT INTO collectionobjectattachment VALUES (?,?,?,?)",
                           test_collectionobjectattachment_data)
        conn.commit()
        cursor.execute("CREATE TABLE testdata1 "
                       "(AttachmentID, data1, data2, data3, FOREIGN KEY(AttachmentID) "
                       "REFERENCES attachment(AttachmentID))")
        test_testdata1 = [("1", "a", "b", "c"), ("2", "b", "c", "d"),
                          ("4", "c", "d", "e"), ("3", "d", "e", "f")]
        cursor.executemany("INSERT INTO testdata1 VALUES (?,?,?,?)", test_testdata1)
        conn.commit()
        cursor.execute("CREATE TABLE testdata2 "
                       "(AttachmentID, data1, data2, data3, FOREIGN KEY(AttachmentID) "
                       "REFERENCES attachment(AttachmentID))")
        test_testdata2 = [("1", "i", "b", "c"), ("4", "o", "e", "f"),
                          ("2", "g", "h", "i"), ("3", "j", "k", "l")]
        cursor.executemany("INSERT INTO testdata2 VALUES (?,?,?,?)", test_testdata2)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        # Deletes the test database
        os.remove("specifytest.db")

    def test_select_attachments(self):
        # Tests to confirm AttachmentID's that are a image/jpeg MimeType are returned
        conn = sqlite3.connect("specifytest.db")
        actual = RemoveLinksToAttachments.select_attachments(conn)
        expected = [("1", ), ("4", ), ("3", )]
        self.assertEqual(expected, actual)

    def test_delete_attachments_attachment_table(self):
        # Tests to confirm that AttachmentID's are deleted
        exception = sqlite3.IntegrityError
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        test_referenced_tables = [("testdata1",), ("testdata2",), ("collectionobjectattachment",)]
        test_attachments = [("1", ), ("2", ), ("3", )]
        RemoveLinksToAttachments.delete_attachments(
            conn, test_referenced_tables, test_attachments, exception)
        cursor.execute("SELECT * FROM attachment WHERE AttachmentID = 1")
        actual = cursor.fetchall()
        self.assertFalse(actual)

    def test_delete_attachments_no_conflicts(self):
        # Tests to confirm an empty list is returned when no conflicts occur
        exception = sqlite3.IntegrityError
        conn = sqlite3.connect("specifytest.db")
        test_referenced_tables = [("testdata1",), ("testdata2",), ("collectionobjectattachment",)]
        test_attachments = [("1", ), ("2", ), ("3", )]
        actual = RemoveLinksToAttachments.delete_attachments(
            conn, test_referenced_tables, test_attachments, exception)
        expected = []
        self.assertEqual(expected, actual)

    def test_delete_attachments_conflicts(self):
        # Tests to confirm correct values are returned when conflicts occur
        exception = sqlite3.IntegrityError
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_referenced_tables = [("testdata1", )]
        test_attachments = [("1", ), ("2", ), ("3", ), ("4", )]
        actual = RemoveLinksToAttachments.delete_attachments(
            conn, test_referenced_tables, test_attachments, exception)
        expected = ["1", "2", "3", "4"]
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
