"""
Test for the DuplicateSearch script for 8 cases. Script only tests the duplicate search functions and not the tree
iteration to avoid type conversion conflicts"""
import specifytreebuilder, os, sqlite3, unittest, DuplicateSearch

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

    def test_find_geography_duplicates_locality_positive(self):
        """ tests to confirm that duplicates are found if searching by locality name and duplicates are present"""
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {"test": ["55"]}
        test_name = ("Test", 11)
        test_locality_toggle = True
        actual = DuplicateSearch.find_geography_duplicates(conn, test_locality_toggle, test_node_dict, test_name)
        expected = {"test": ["55", "1"]}
        self.assertDictEqual(expected, actual)

    def test_find_geography_duplicates_locality_negative(self):
        """tests to confirm that no duplicates are found if searching by locality name and no duplicates are present"""
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {}
        test_name = ("Test", 11)
        test_locality_toggle = True
        actual = DuplicateSearch.find_geography_duplicates(conn, test_locality_toggle, test_node_dict, test_name)
        expected = {"test": ["1"]}
        self.assertDictEqual(expected, actual)

    def test_find_geography_duplicates_positive(self):
        """tests to confirm that duplicates are found if searching without locality and duplicates are present"""
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {"test":["55"]}
        test_name = ("Test", 11)
        test_locality_toggle = True
        actual = DuplicateSearch.find_geography_duplicates(conn, test_locality_toggle, test_node_dict, test_name)
        expected = {"test": ["55","1"]}
        self.assertDictEqual(expected, actual)

    def test_find_geography_duplicates_negative(self):
        """tests to confirm that no duplicates are found if searching without locality and duplicates are not present"""
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {"foo": ["55"]}
        test_name = ("Test", 11)
        test_locality_toggle = True
        actual = DuplicateSearch.find_geography_duplicates(conn, test_locality_toggle, test_node_dict, test_name)
        expected = {"foo":["55"], "test": ["1"]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_no_author_positive(self):
        """tests to confirm that duplicates are found if duplicates are present and an author is not present"""
        test_level_dict = {("Test",None): [(55,None)]}
        test_name = ("Test", 11, None)
        actual = DuplicateSearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", None): [(55, None),(11, None)]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_no_author_negative(self):
        """tests to confirm that no duplicates are found if no duplicates are present and an author is not present"""
        test_level_dict = {("Test",None): [(55,None)]}
        test_name = ("foo", 11, "")
        actual = DuplicateSearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", None): [(55, None)], ("foo", None): [(11, None)]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_author_positive(self):
        """tests to confirm that duplicates are found if duplicates and an author are present"""
        test_level_dict = {("Test","f"): [(55,"foo")]}
        test_name = ("Test", 11, "fo")
        actual = DuplicateSearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", "f"): [(55, "foo"),(11, "fo")]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_author_negative(self):
        """tests to confirm that no duplicates are found if an author is present and duplicates aren't"""
        test_level_dict = {("Test", "f"): [(55, "foo")]}
        test_name = ("Test", 11, "bar")
        actual = DuplicateSearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", "f"): [(55, "foo")],("Test","b"): [(11, "bar")]}
        self.assertDictEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
