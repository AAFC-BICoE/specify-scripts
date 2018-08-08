"""
Test for the DuplicateSearch script"""


import specifytreebuilder, os, sqlite3, unittest, DuplicateSearch
from anytree import Node, PostOrderIter

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """ creates the test database and a test table, inserts sample data into test table """
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE locality (LocalityName, LocalityID, GeographyID)""")
        conn.commit()
        test_locality = [("test", "1", "11"), ("Test", "2", "22"), ("foo", "3", "33"), ("bar", "4", "44")]
        cursor.executemany("""INSERT INTO locality VALUES (?,?,?)""", test_locality)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        """ deletes the test database"""
        os.remove("specifytest.db")

    def test_search_tree_country_locality_positive(self):
        """ tests to confirm that duplicates are found if searching by locality name and duplicates are present"""
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {'test': ['55']}
        test_name= ('Test', 11)
        test_locality_toggle = True
        actual = DuplicateSearch.find_geography_duplicates(conn,test_locality_toggle, test_node_dict,test_name)
        expected = {"test": ['55','1']}
        self.assertEqual(expected,actual)

    def test_search_tree_country_locality_negative(self):
        """tests to confirm that no duplicates are found if searching by locality name and no duplicates are present"""
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {}
        test_name = ('Test', 11)
        test_locality_toggle = True
        actual = DuplicateSearch.find_geography_duplicates(conn, test_locality_toggle, test_node_dict, test_name)
        expected = {"test": ['1']}
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
