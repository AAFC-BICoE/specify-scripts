"""Tests the specifytreebuilder module across 12 cases. Creates and deletes a test database."""
import os
import sqlite3
import unittest
from anytree import Node
import specifytreebuilder

class TestDatabase(unittest.TestCase):
    """ Creates test database to use for testing the specifytreebuilder.py script."""

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
        # Tests to confirm the fetch_ranks function selects & returns the correct list
        conn = sqlite3.connect("specifytest.db")
        actual = specifytreebuilder.fetch_ranks(conn, "testranks")
        expected = [("1", ), ("2", ), ("3", )]
        self.assertListEqual(expected, actual)

    def test_rank_dict(self):
        # Tests to confirm the dictionary created is returning the correct list
        conn = sqlite3.connect("specifytest.db")
        test_columns = "data1, data2"
        test_table = "testranks"
        test_rank = [("1", ), ("2", ), ("3", )]
        actual = specifytreebuilder.rank_dict(
            conn, test_columns, test_table, test_rank)
        expected = {"1": [("a", "b")], "2": [("d", "e"), ("g", "h")], "3": [("j", "k")]}
        self.assertDictEqual(expected, actual)

    def test_add_to_dict_in_dict(self):
        # Tests to confirm that if a key exists in the dictionary, its value is appended
        test_dict = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"]}
        actual = specifytreebuilder.add_to_dict(test_dict, "a", "j")
        expected = {"a": ["b", "c", "j"], "d": ["e", "f"], "g": ["h", "i"]}
        self.assertDictEqual(expected, actual)

    def test_add_to_dict_not_in_dict(self):
        # Tests to confirm that if a key does not exist in the dictionary, it is created
        test_dict = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"]}
        actual = specifytreebuilder.add_to_dict(test_dict, "k", "j")
        expected = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"], "k": ["j"]}
        self.assertDictEqual(expected, actual)

    def test_check_author_none(self):
        # Tests to confirm that the check author function works if None is passed in as the author
        test_dictionary = {}
        test_name = "foo"
        test_author = None
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", None): [("123", None)]}
        self.assertDictEqual(expected, actual)

    def test_check_author_brackets(self):
        # Tests to confirm the correct dict is returned if the author first letter is a bracket
        test_dictionary = {}
        test_name = "foo"
        test_author = "[bar]"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", "b"): [("123", "[bar]")]}
        self.assertDictEqual(expected, actual)

    def test_check_author_round_brackets_fail(self):
        # Tests to confirm the correct dict is returned if the author first letters do not match
        test_dictionary = {}
        test_name = "foo"
        test_author = "(bar)"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", "("): [("123", "(bar)")]}
        self.assertNotEqual(expected, actual)

    def test_check_author_brackets_normal(self):
        # Tests to confirm the correct dict is returned if the author first letters are letters
        test_dictionary = {}
        test_name = "foo"
        test_author = "bar"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo", "b"): [("123", "bar")]}
        self.assertEqual(expected, actual)

    def test_build_tree_with_nums_with_author(self):
        # Tests to confirm that tree building with author and numbers works properly
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
        # Tests to confirm that tree building without author and with numbers works properly
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
        # Tests to confirm that tree building with author and without numbers works properly
        test_dict = {"1": [('None', 'Life', '1', 'test1')],
                     "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = True
        actual = specifytreebuilder.build_tree_without_nums(test_dict, author_toggle)
        expected = {'1': ('Life', 'None', Node("root/('Life', '1', 'test1')"))}
        # Converted to str to avoid conversion conflicts
        self.assertEqual(str(expected), str(actual))

    def test_build_tree_without_nums_without_author(self):
        # Tests to confirm that tree building with author and without numbers works properly
        test_dict = {"1": [('None', 'Life', '1', 'test1')],
                     "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = False
        actual = specifytreebuilder.build_tree_without_nums(test_dict, author_toggle)
        expected = {'1': ('Life', 'None', Node("root/('Life', '1')"))}
        # Converted to str to avoid conversion conflicts
        self.assertEqual(str(expected), str(actual))

if __name__ == "__main__":
    unittest.main()
