"""
Tests the CollectionMerge script for 5 different cases. First builds test database, and populates using test data. Then
tests to confirm catalognumbers are being selected from proper collections, any conflicts that are present are found and
returned in a formatted list, references are being switched correctly (effectively 'merging' the collections together)
and collections are deleted.
"""
import CollectionMerge, os, test_db, sqlite3, unittest

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """ creates the test database and a test table, inserts sample data into test table """
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE collectionobject (CollectionID, CatalogNumber, data2, data3)""")
        conn.commit()
        test_attachment_data = [("1", "4", "b", "c"), ("2", "5", "e", "f"), ("2", "6", "h", "i"), ("1", "7", "k", "l")]
        cursor.executemany("""INSERT INTO collectionobject VALUES (?,?,?,?)""", test_attachment_data)
        conn.commit()

        cursor.execute("""CREATE TABLE collection (CollectionID, CatalogNumber, data2, data3)""")
        conn.commit()
        test_attachment_data = [("1", "4", "b", "c"), ("2", "5", "e", "f"), ("3", "6", "h", "i"), ("4", "7", "k", "l")]
        cursor.executemany("""INSERT INTO collection VALUES (?,?,?,?)""", test_attachment_data)
        conn.commit()

        cursor.execute("""CREATE TABLE testdata1 (ID,data1,data2,data3)""")
        test_testdata1 = [("1","a","b","c"),("1","b","c","d"),("1","c","d","e"),("2","d","e","f")]
        cursor.executemany("""INSERT INTO testdata1 VALUES (?,?,?,?)""", test_testdata1)
        conn.commit()

        cursor.execute("""CREATE TABLE testdata2 (ID,data1,data2,data3)""")
        test_testdata2 = [("1", "i", "b", "c"), ("2", "o", "e", "f"), ("2", "g", "h", "i"), ("2", "j", "k", "l")]
        cursor.executemany("""INSERT INTO testdata2 VALUES (?,?,?,?)""", test_testdata2)
        conn.commit()

        cursor.close()
        conn.close()

    def tearDown(self):
        """ deletes the test database"""
        os.remove("specifytest.db")

    def test_fetch_catalog_numbers(self):
        """ tests to confirm that catalog numbers are selected from the proper collection and in the proper format"""
        conn = sqlite3.connect("specifytest.db")
        test_collectionid = "1"
        actual = CollectionMerge.fetch_catalog_numbers(conn,test_collectionid)
        expected = [["4"],["7"]]
        self.assertEqual(expected,actual)

    def test_check_conflicts(self):
        """ tests to confirm that if there are conflicts present then proper list will be returned"""
        conn = sqlite3.connect("specifytest1.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE collectionobject (CollectionID, CatalogNumber, data2, data3)""")
        conn.commit()
        test_attachment_data = [("1", "6", "b", "c"), ("2", "5", "e", "f"), ("2", "6", "h", "i"), ("1", "7", "k", "l")]
        cursor.executemany("""INSERT INTO collectionobject VALUES (?,?,?,?)""", test_attachment_data)
        conn.commit()
        test_c1 = "1"
        test_c2 = "2"
        actual = CollectionMerge.check_conflicts(conn,test_c1,test_c2)
        expected = [["6"]]
        self.assertEqual(expected,actual)
        cursor.close()
        conn.close()
        os.remove("specifytest1.db")

    def test_check_conflicts_None(self):
        """tests to confirm that if there are no conflicts present, an empty list is returned"""
        conn = sqlite3.connect("specifytest.db")
        test_c1 = "1"
        test_c2 = "2"
        actual = CollectionMerge.check_conflicts(conn, test_c1, test_c2)
        expected = []
        self.assertEqual(expected, actual)

    def test_switch_references(self):
        """tests to confirm that switches ('merges') made for the tables are executed properly  """
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        test_table_list = [("testdata1","ID"),("testdata2","ID")]
        test_c1 = "1"
        test_c2 = "2"
        CollectionMerge.switch_references(conn,test_table_list,test_c1,test_c2)
        conn.commit()
        cursor.execute("SELECT ID FROM testdata1 WHERE ID == '1'")
        actual = cursor.fetchall()
        expected = []
        self.assertEqual(expected,actual)

    def test_delete_collection(self):
        """tests to confirm that a collection is able to be deleted from the database by the collectionid"""
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        test_collectionid = "1"
        CollectionMerge.delete_collection(conn,test_collectionid)
        cursor.execute("SELECT collectionid from collection where collectionid == '1'")
        actual = cursor.fetchall()
        expected = []
        self.assertEqual(expected,actual)

if __name__ == "__main__":
    unittest.main()