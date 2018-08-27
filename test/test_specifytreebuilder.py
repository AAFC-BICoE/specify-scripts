"""
12 different test methods for the specifytreebuilder.py module.
"""
import os
import sqlite3
import unittest
from anytree import Node
from specifycleaning import specifytreebuilder

class TestDatabase(unittest.TestCase):
    # Tests the specifytreebuilder.py module, creates and deletes a test database

    def setUp(self):
        # Creates the test database and a test table, inserts sample data into test table
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE testranks (RankID, data1, data2, data3)")
        conn.commit()
        test_rank_values = [("1", "a", "b", "c"), ("2", "d", "e", "f"),
                            ("2", "g", "h", "i"), ("3", "j", "k", "l")]
        cursor.executemany("INSERT INTO testranks VALUES (?,?,?,?)", test_rank_values)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        # Deletes the test database
        os.remove("specifytest.db")

    def test_selecting_rank(self):
        # Confirms the fetch_ranks function selects and returns the correct RankID's
        conn = sqlite3.connect("specifytest.db")
        actual = specifytreebuilder.fetch_ranks(conn, "testranks")
        expected = [("1", ), ("2", ), ("3", )]
        self.assertListEqual(expected, actual)

    def test_rank_dict(self):
        # Confirms the function returns the correct dictionary of RankID's
        conn = sqlite3.connect("specifytest.db")
        test_columns = "data1, data2"
        test_table = "testranks"
        test_rank = [("1", ), ("2", ), ("3", )]
        actual = specifytreebuilder.rank_dict(
            conn, test_columns, test_table, test_rank)
        expected = {"1": [("a", "b")], "2": [("d", "e"), ("g", "h")], "3": [("j", "k")]}
        self.assertDictEqual(expected, actual)

    def test_add_to_dict_in_dict(self):
        # Confirms if a key value already exists in the dictionary, the new value is appended
        test_dict = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"]}
        actual = specifytreebuilder.add_to_dict(test_dict, "a", "j")
        expected = {"a": ["b", "c", "j"], "d": ["e", "f"], "g": ["h", "i"]}
        self.assertDictEqual(expected, actual)

    def test_add_to_dict_not_in_dict(self):
        # Confirms if a key does not exist in the dictionary, a new key/value entry is created
        test_dict = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"]}
        actual = specifytreebuilder.add_to_dict(test_dict, "k", "j")
        expected = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"], "k": ["j"]}
        self.assertDictEqual(expected, actual)

    def test_check_author_none(self):
        # Confirms the check author function returns the expected dict with None as the author
        test_dictionary = {}
        test_name = "foo"
        test_author = None
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", None): [("123", None)]}
        self.assertDictEqual(expected, actual)

    def test_check_author_brackets(self):
        # Confirms the expected dictionary is returned when the author first letter is a bracket
        test_dictionary = {}
        test_name = "foo"
        test_author = "[bar]"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", "b"): [("123", "[bar]")]}
        self.assertDictEqual(expected, actual)

    def test_check_author_round_brackets_fail(self):
        # Confirms the expected dictionary is returned if the author first letters do not match
        test_dictionary = {}
        test_name = "foo"
        test_author = "(bar)"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", "("): [("123", "(bar)")]}
        self.assertNotEqual(expected, actual)

    def test_check_author_brackets_normal(self):
        # Confirms the expected dictionary is returned if the author first letters are non matching
        test_dictionary = {}
        test_name = "foo"
        test_author = "bar"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", "b"): [("123", "bar")]}
        self.assertEqual(expected, actual)

    def test_build_tree_with_nums_with_author(self):
        # Confirms the build_tree_with_nums method returns the expected dictionary
        test_dict = {"1": [('None', 'Life2', '1', 'test1')],
                     "4":[('1', 'Plantae4', '181107', 'test')]}
        author_toggle = True
        actual = specifytreebuilder.build_tree_with_nums(test_dict, author_toggle)
        expected = {'1': ('Life2', 'None', Node("root/('Life2', '1', 'test1')")),
                    '181107': ('Plantae4', '1', Node("root/('Life2', '1', 'test1')/"
                                                     "('Plantae4', '181107', 'test')"))}
        # Converted to str to avoid conversion conflicts
        self.assertEqual(str(expected), str(actual))

    def test_build_tree_with_nums_without_author(self):
        # Confirms the build_tree_with_nums method returns the expected dictionary
        test_dict = {"1": [('None', 'Life2', '1', 'test1')],
                     "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = False
        actual = specifytreebuilder.build_tree_with_nums(test_dict, author_toggle)
        expected = {'1': ('Life2', 'None', Node("root/('Life2', '1')")),
                    '181107': ('Plantae4', '1', Node("root/('Life2', '1')/"
                                                     "('Plantae4', '181107')"))}
        # Converted to str to avoid conversion conflicts
        self.assertEqual(str(expected), str(actual))

    def test_build_tree_without_nums_with_author(self):
        # Confirms the build_tree_without_nums method returns the expected dictionary
        test_dict = {"1": [('None', 'Life', '1', 'test1')],
                     "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = True
        actual = specifytreebuilder.build_tree_without_nums(test_dict, author_toggle)
        expected = {'1': ('Life', 'None', Node("root/('Life', '1', 'test1')"))}
        # Converted to str to avoid conversion conflicts
        self.assertEqual(str(expected), str(actual))

    def test_build_tree_without_nums_without_author(self):
        # Confirms the build_tree_without_nums method returns the expected dictionary
        test_dict = {"1": [('None', 'Life', '1', 'test1')],
                     "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = False
        actual = specifytreebuilder.build_tree_without_nums(test_dict, author_toggle)
        expected = {'1': ('Life', 'None', Node("root/('Life', '1')"))}
        # Converted to str to avoid conversion conflicts
        self.assertEqual(str(expected), str(actual))

if __name__ == "__main__":
    unittest.main()
