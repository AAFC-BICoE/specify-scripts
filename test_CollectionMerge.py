"""
9 different test methods for the CollectionMerge.py script.
"""
import os
import sqlite3
import unittest
import CollectionMerge

class TestDatabase(unittest.TestCase):
    # Tests the script CollectionMerge.py

    def setUp(self):
        # Creates test database, inserts sample data into test tables
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE collection (CollectionID, CatalogNumber, data2, data3, "
                       "PRIMARY KEY(CollectionID))")
        test_attachment_data = [("1", "4", "b", "c"), ("2", "5", "e", "f"),
                                ("3", "6", "h", "i"), ("4", "7", "k", "l")]
        cursor.executemany("INSERT INTO collection VALUES (?,?,?,?)", test_attachment_data)

        cursor.execute("CREATE TABLE collectionobject (CollectionID, CatalogNumber, data2, data3, "
                       "FOREIGN KEY(CollectionID) REFERENCES collection(CollectionID))")
        test_attachment_data = [("1", "4", "b", "c"), ("2", "4", "e", "f"),
                                ("3", "6", "h", "i"), ("1", "7", "k", "l")]
        cursor.executemany("INSERT INTO collectionobject VALUES (?,?,?,?)", test_attachment_data)


        cursor.execute("CREATE TABLE testdata1 (ID1, data1, data2, data3, "
                       "FOREIGN KEY(ID1) REFERENCES collection(CollectionID))")
        test_testdata1 = [("1", "a", "b", "c"), ("3", "b", "c", "d"),
                          ("5", "c", "d", "e"), ("2", "d", "e", "f")]
        cursor.executemany("INSERT INTO testdata1 VALUES (?,?,?,?)", test_testdata1)


        cursor.execute("CREATE TABLE testdata2 (ID2, data1, data2, data3, "
                       "FOREIGN KEY(ID2) REFERENCES collection(CollectionID))")
        test_testdata2 = [("1", "i", "b", "c"), ("3", "o", "e", "f"),
                          ("2", "g", "h", "i"), ("5", "j", "k", "l")]
        cursor.executemany("INSERT INTO testdata2 VALUES (?,?,?,?)", test_testdata2)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        # Deletes the test database
        os.remove("specifytest.db")

    def test_fetch_catalog_numbers_positive(self):
        # Confirms the expected list is returned when catalog numbers are selected by collectionID
        conn = sqlite3.connect("specifytest.db")
        actual = CollectionMerge.fetch_catalog_numbers(conn, "1")
        expected = [["4"], ["7"]]
        self.assertListEqual(expected, actual)

    def test_fetch_catalog_numbers_negative(self):
        # Confirms an empty list is returned when an invalid collectionID is entered
        conn = sqlite3.connect("specifytest.db")
        actual = CollectionMerge.fetch_catalog_numbers(conn, "7")
        self.assertFalse(actual)

    def test_check_conflicts_positive(self):
        # Confirms the expected list is returned if there are catalog number conflicts
        conn = sqlite3.connect("specifytest.db")
        actual = CollectionMerge.check_conflicts(conn, "1", "2")
        expected = ([["4"]], [["4"], ["7"]])
        self.assertTupleEqual(expected, actual)

    def test_check_conflicts_negative(self):
        # Confirms the expected list is returned if there are no catalog number conflicts
        conn = sqlite3.connect("specifytest.db")
        actual = CollectionMerge.check_conflicts(conn, "1", "3")
        expected = ([], [["4"], ["7"]])
        self.assertTupleEqual(expected, actual)

    def test_switch_references(self):
        # Confirms that switches ('merges') made between the collectionIDs are executed
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        test_table_list = [("testdata1", "ID1"), ("testdata2", "ID2")]
        CollectionMerge.switch_references(conn, test_table_list, "1", "2")
        cursor.execute("SELECT ID1 FROM testdata1 WHERE ID1 == '1'")
        actual = cursor.fetchall()
        self.assertFalse(actual)

    def test_delete_collection(self):
        # Confirms that a collection is deleted when no conflicts occur
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        test_integrity_error = sqlite3.IntegrityError
        CollectionMerge.delete_collection(conn, "1", test_integrity_error)
        cursor.execute("SELECT CollectionID FROM collection WHERE CollectionID == '1'")
        actual = cursor.fetchall()
        self.assertFalse(actual)

    def test_delete_collection_positive(self):
        # Confirms None is returned when a collection is deleted and no conflicts occur
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        test_integrity_error = sqlite3.IntegrityError
        actual = CollectionMerge.delete_collection(conn, "4", test_integrity_error)
        self.assertIsNone(actual)

    def test_delete_collection_negative(self):
        # Confirms False is returned when an integrity error occurs when attempting to delete
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        test_integrity_error = sqlite3.IntegrityError
        actual = CollectionMerge.delete_collection(conn, "1", test_integrity_error)
        self.assertFalse(actual)

    def test_csv_report_exists(self):
        # Confirms when the report writing method is called, a report is actually created
        CollectionMerge.csv_report("test", ["test heading"], ["data"], False)
        actual = os.path.exists(str(os.getcwd() + "/test.csv"))
        os.remove(str(os.getcwd() + "/test.csv"))
        self.assertTrue(actual)

if __name__ == "__main__":
    unittest.main()
