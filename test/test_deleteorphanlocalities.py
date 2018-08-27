"""
5 different test methods for the deleteorphanlocalities.py script.
"""
import unittest
import os
import sqlite3
from specifycleaning import deleteorphanlocalities

class TestDatabase(unittest.TestCase):
    # Testing the script deleteorphanlocalities.py

    def setUp(self):
        # Creates test database and inserts sample data
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE locality (LocalityID NOT NULL,data1, PRIMARY KEY(LocalityID))")
        test_locality = [("1", "test1"), ("2", "test2"), ("3", "test3"),
                         ("4", "test4"), ("5", "test5"), ("6", "test6")]
        cursor.executemany("INSERT INTO locality VALUES (?,?)", test_locality)
        conn.commit()

        cursor.execute("CREATE TABLE collectingevent "
                       "(LocalityID, data2, FOREIGN KEY(LocalityID)"
                       " REFERENCES locality(LocalityID))")
        test_collecting_event = [("1", "test7"), ("2", "test8"), ("3", "test9")]
        cursor.executemany("INSERT INTO collectingevent VALUES (?,?)", test_collecting_event)
        conn.commit()

        cursor.execute("CREATE TABLE table1 ("
                       "LocalityID, data3, FOREIGN KEY(LocalityID) "
                       "REFERENCES locality(LocalityID))")
        test_table_1 = [("1", "test11"), ("2", "test12"), ("3", "test13"), ("7", "test14")]
        cursor.executemany("INSERT INTO table1 VALUES (?,?)", test_table_1)
        conn.commit()

        cursor.execute("CREATE TABLE table2 "
                       "(LocalityID, data4, FOREIGN KEY(LocalityID) "
                       "REFERENCES locality(LocalityID))")
        test_table_2 = [("1", "test11"), ("3", "test12"), ("2", "test13"), ("8", "test14")]
        cursor.executemany("INSERT INTO table2 VALUES (?,?)", test_table_2)
        conn.commit()

    def tearDown(self):
        # Removes test database
        os.remove("specifytest.db")

    def test_orphan_ids(self):
        # Confirms localityID's are selected and returned in the proper format
        conn = sqlite3.connect("specifytest.db")
        actual = deleteorphanlocalities.orphan_ids(conn)
        expected = [("4", ), ("5", ), ("6", )]
        self.assertEqual(expected, actual)

    def test_check_orphans(self):
        # Confirms that the LocalityID's returned are actually 'orphans'
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM collectingevent WHERE LocalityID IN ('4','5','6')")
        actual = cursor.fetchall()
        expected = []
        self.assertEqual(expected, actual)

    def test_delete_orphans_no_conflicts(self):
        # Confirms the delete_orphans function returns an empty list when no conflicts occur
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_orphans = [("4", ), ("5", ), ("6", )]
        test_referenced_tables = [("table1", ), ("table2", ), ("collectingevent", )]
        test_integrity_error = sqlite3.IntegrityError
        actual = deleteorphanlocalities.delete_orphans(
            conn, test_orphans, test_referenced_tables, test_integrity_error)
        expected = []
        self.assertEqual(expected, actual)

    def test_delete_orphans_check(self):
        # Confirms records are deleted when no conflicts occur
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_orphans = [("4", ), ("5", ), ("6", )]
        test_referenced_tables = [("table1",), ("table2",)]
        test_integrity_error = sqlite3.IntegrityError
        deleteorphanlocalities.delete_orphans(
            conn, test_orphans, test_referenced_tables, test_integrity_error)
        cursor.execute("SELECT LocalityID FROM locality WHERE LocalityID IN ('4','5','6')")
        actual = cursor.fetchall()
        expected = []
        self.assertEqual(expected, actual)

    def test_delete_orphans_conflicts(self):
        # Confirms correct conflict list is returned when conflicts occur
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_orphans = [("1",), ("3",), ("2",)]
        test_referenced_tables = [("table1",)]
        test_integrity_error = sqlite3.IntegrityError
        actual = deleteorphanlocalities.delete_orphans(
            conn, test_orphans, test_referenced_tables, test_integrity_error)
        expected = ["1", "3", "2"]
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
