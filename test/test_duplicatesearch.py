"""
8 test methods for the duplicatesearch.py script.
"""
import os
import sqlite3
import unittest
from specifycleaning import duplicatesearch

class TestDatabase(unittest.TestCase):
    # Testing the duplicatesearch.py script. Only tests methods that do not involve tree iteration
    # To avoid type conversion conflicts.
    def setUp(self):
        # Creates the test database, inserts sample data into test table
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE locality (LocalityName, LocalityID, GeographyID)")
        conn.commit()
        test_locality = [("test", "1", "11"), ("Test", "2", "22"),
                         ("foo", "3", "33"), ("bar", "4", "44")]
        cursor.executemany("INSERT INTO locality VALUES (?,?,?)", test_locality)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        # Deletes the test database
        os.remove("specifytest.db")

    def test_find_geography_duplicates_locality_positive(self):
        # Confirms duplicates are found if searching by locality name
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {"test": ["55"]}
        test_name = ("Test", 11)
        actual = duplicatesearch.find_geography_duplicates(conn, True, test_node_dict, test_name)
        expected = {"test": ["55", "1"]}
        self.assertDictEqual(expected, actual)

    def test_find_geography_duplicates_locality_negative(self):
        # Confirms no duplicates found if searching by locality name
        conn = sqlite3.connect("specifytest.db")
        test_name = ("Test", 11)
        actual = duplicatesearch.find_geography_duplicates(conn, True, {}, test_name)
        expected = {"test": ["1"]}
        self.assertDictEqual(expected, actual)

    def test_find_geography_duplicates_positive(self):
        # Confirms duplicates are found if searching by geography name
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {"test": ["55"]}
        test_name = ("Test", 11)
        actual = duplicatesearch.find_geography_duplicates(conn, True, test_node_dict, test_name)
        expected = {"test": ["55", "1"]}
        self.assertDictEqual(expected, actual)

    def test_find_geography_duplicates_negative(self):
        # Confirms no duplicates are found if searching by geography name
        conn = sqlite3.connect("specifytest.db")
        test_node_dict = {"foo": ["55"]}
        test_name = ("Test", 11)
        actual = duplicatesearch.find_geography_duplicates(conn, True, test_node_dict, test_name)
        expected = {"foo":["55"], "test": ["1"]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_no_author_positive(self):
        # Confirms duplicates are found when an author is not present
        test_level_dict = {("Test", None): [(55, None)]}
        test_name = ("Test", 11, None)
        actual = duplicatesearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", None): [(55, None), (11, None)]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_no_author_negative(self):
        # Confirms no duplicates are found when an author is not present
        test_level_dict = {("Test", None): [(55, None)]}
        test_name = ("foo", 11, "")
        actual = duplicatesearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", None): [(55, None)], ("foo", None): [(11, None)]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_author_positive(self):
        # Confirms duplicates are found if an author is present
        test_level_dict = {("Test", "f"): [(55, "foo")]}
        test_name = ("Test", 11, "fo")
        actual = duplicatesearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", "f"): [(55, "foo"), (11, "fo")]}
        self.assertDictEqual(expected, actual)

    def test_find_taxon_duplicates_author_negative(self):
        # Confirms no duplicates are found if an author is present
        test_level_dict = {("Test", "f"): [(55, "foo")]}
        test_name = ("Test", 11, "bar")
        actual = duplicatesearch.find_taxon_duplicates(test_name, test_level_dict)
        expected = {("Test", "f"): [(55, "foo")], ("Test", "b"): [(11, "bar")]}
        self.assertDictEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
