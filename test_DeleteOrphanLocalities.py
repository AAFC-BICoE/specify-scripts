# Test for the DeleteOrphanLocalities script. Creates and populates test database for use with the script, tests for
# 5 different cases.
import DeleteOrphanLocalities, unittest, datetime, os, sqlite3

class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Creates test database and inserts sample data
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE locality (LocalityID NOT NULL, data1, PRIMARY KEY(LocalityID))")
        test_locality = [("1","test1"),("2","test2"),("3","test3"), ("4","test4"),("5","test5"),("6","test6")]
        cursor.executemany("INSERT INTO locality VALUES (?,?)", test_locality)
        conn.commit()

        cursor.execute(
            "CREATE TABLE collectingevent (LocalityID, data2, FOREIGN KEY(LocalityID) REFERENCES locality(LocalityID))")
        test_collecting_event = [("1","test7"),("2","test8"),("3","test9")]
        cursor.executemany("INSERT INTO collectingevent VALUES (?,?)", test_collecting_event)
        conn.commit()

        cursor.execute(
            "CREATE TABLE table1 (LocalityID, data3, FOREIGN KEY(LocalityID) REFERENCES locality(LocalityID))")
        test_table_1 = [("1", "test11"), ("2", "test12"), ("3", "test13")]#, ("7", "test14")]
        cursor.executemany("INSERT INTO table1 VALUES (?,?)", test_table_1)
        conn.commit()

        cursor.execute(
            "CREATE TABLE table2 (LocalityID, data4, FOREIGN KEY(LocalityID) REFERENCES locality(LocalityID))")
        test_table_2 = [("1", "test11"), ("3", "test12"), ("2", "test13")]#, ("8", "test14")]
        cursor.executemany("INSERT INTO table2 VALUES (?,?)", test_table_2)
        conn.commit()

    def tearDown(self):
        # Removes test database
        os.remove("specifytest.db")

    def test_orphan_ids(self):
        # Tests to confirm orphan locality ID's are returned in the proper format
        conn = sqlite3.connect("specifytest.db")
        actual = DeleteOrphanLocalities.orphan_ids(conn)
        expected = [("4",),("5",),("6",)]
        self.assertEqual(expected,actual)

    def test_check_orphans(self):
        # Tests to confirm that the orphans returned from the orphan_ids are actually orphans
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM collectingevent WHERE LocalityID IN ('4','5','6')")
        actual = cursor.fetchall()
        expected = []
        self.assertEqual(expected,actual)

    def test_delete_orphans_no_conflicts(self):
        # Tests to confirm that the delete_orphans function returns an empty list when there are no conflicts
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_orphans = [("4",),("5",),("6",)]
        test_referenced_tables = [("table1",),("table2",),("collectingevent",)]
        test_integrity_error = sqlite3.IntegrityError
        actual = DeleteOrphanLocalities.delete_orphans(conn,test_orphans,test_referenced_tables,test_integrity_error)
        expected = []
        self.assertEqual(expected,actual)

    def test_delete_orphans_check(self):
        # Tests to confirm that the delete_orphans function actually deletes the records from the locality table when
        # There are no conflicts
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_orphans = [("4",), ("5",), ("6",)]
        test_referenced_tables = [("table1",), ("table2",)]
        test_integrity_error = sqlite3.IntegrityError
        DeleteOrphanLocalities.delete_orphans(conn, test_orphans, test_referenced_tables, test_integrity_error)
        cursor.execute("SELECT LocalityID FROM locality WHERE LocalityID IN ('4','5','6')")
        actual = cursor.fetchall()
        expected = []
        self.assertEqual(expected,actual)

    def test_delete_orphans_conflicts(self):
        # Tests to confirm that the delete_orphans function returns the correct conflict list when there are conflicts
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_orphans = [("1",), ("3",), ("2",)]
        test_referenced_tables = [("table1",)]
        test_integrity_error = sqlite3.IntegrityError
        actual = DeleteOrphanLocalities.delete_orphans(conn, test_orphans, test_referenced_tables, test_integrity_error)
        expected = ["1","3","2"]
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
