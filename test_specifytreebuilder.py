"""
Tests the specifytreebuilder module for 12 different cases. Case descriptions can be found in specific functions.
For those that require a database, a sample database is created, populated, and destroyed for each instance.
"""
import specifytreebuilder
import os
import sqlite3
import unittest

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """ creates the test database and a test table, inserts sample data into test table """
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE testranks (RankID, data1, data2, data3)""")
        conn.commit()
        test_rank_values = [("1", "a", "b", "c"), ("2", "d", "e", "f"), ("2", "g", "h", "i"), ("3", "j", "k", "l")]
        cursor.executemany("""INSERT INTO testranks VALUES (?,?,?,?)""", test_rank_values)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        """ deletes the test database"""
        os.remove("specifytest.db")

    def test_selecting_rank(self):
        """ tests to confirm the fetch_ranks function selects & returns the properly formatted/ordered list """
        conn = sqlite3.connect("specifytest.db")
        actual = specifytreebuilder.fetch_ranks(conn,"testranks")
        expected = [("1",),("2",),("3",)]
        self.assertListEqual(expected,actual)

    def test_rank_dict(self):
        """ tests to confirm the dictionary created is pulling the correct data in the correct format"""
        conn=sqlite3.connect("specifytest.db")
        test_columns= "data1, data2"
        test_table= "testranks"
        test_rank= [("1",),("2",),("3",)]
        actual = specifytreebuilder.rank_dict(conn,test_columns,test_table,test_rank)
        expected = {"1": [("a","b")], "2":[("d","e"),("g","h")],"3":[("j","k")]}
        self.assertDictEqual(expected,actual)

    def test_add_to_dict_in_dict(self):
        """ tests to confirm that if a key is already in the dictionary, the value is updated """
        test_dict = {"a":["b","c"], "d": ["e","f"],"g":["h","i"]}
        actual = specifytreebuilder.add_to_dict(test_dict,"a","j")
        expected = {"a":["b","c","j"], "d": ["e","f"],"g":["h","i"]}
        self.assertDictEqual(expected,actual)

    def test_add_to_dict_not_in_dict(self):
        """ tests to confirm that if a key is not in the dictionary, it is added"""
        test_dict = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"]}
        actual = specifytreebuilder.add_to_dict(test_dict, "k", "j")
        expected = {"a": ["b", "c"], "d": ["e", "f"], "g": ["h", "i"], "k": ["j"]}
        self.assertDictEqual(expected, actual)

    def test_check_author_none(self):
        """ tests to confirm that the check author function works if None is passed in as the author"""
        test_dictionary = {}
        test_name = "foo"
        test_author = None
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary,test_name,test_author,test_tid)
        expected = {("foo",None): [("123",None)]}
        self.assertDictEqual(expected,actual)

    def test_check_author_brackets(self):
        """ tests to confirm that the check author function works if the first letter of the author is a bracket"""
        test_dictionary = {}
        test_name = "foo"
        test_author = "[bar]"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo","b" ): [("123", "[bar]")]}
        self.assertEqual(expected, actual)

    def test_check_author_round_brackets_fail(self):
        """ tests to confirm that the check author function works if the first letter of the author is a bracket"""
        test_dictionary = {}
        test_name = "foo"
        test_author = "(bar)"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo","(" ): [("123", "(bar)")]}
        self.assertNotEqual(expected, actual)

    def test_check_author_brackets_normal(self):
        """ tests to make sure that the check author function works if a normal author is passed in"""
        test_dictionary = {}
        test_name = "foo"
        test_author = "bar"
        test_tid = "123"
        actual = specifytreebuilder.check_author(test_dictionary, test_name, test_author, test_tid)
        expected = {("foo","b" ): [("123", "bar")]}
        self.assertEqual(expected, actual)

    def test_build_tree_with_nums_with_author(self):
        """ tests to confirm that tree building with author and numbers works properly
        - needs to be converted to str because of 'Node' function"""
        test_rank_records_dict = {"1": [('None', 'Life2', '1', 'test1')], "4":[('1', 'Plantae4', '181107', 'test')]}
        author_toggle = True
        actual = str(specifytreebuilder.build_tree_with_nums(test_rank_records_dict,author_toggle))
        expected ="""{'1': ('Life2', 'None', Node("/root/('Life2', '1', 'test1')")), '181107': ('Plantae4', '1', Node("/root/('Life2', '1', 'test1')/('Plantae4', '181107', 'test')"))}"""
        self.assertEqual(expected,actual)

    def test_build_tree_with_nums_without_author(self):
        """ tests to confirm that tree building without author and with numbers works properly
        - needs to be converted to str because of 'Node' function"""
        test_rank_records_dict = {"1": [('None', 'Life2', '1', 'test1')], "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = False
        actual = str(specifytreebuilder.build_tree_with_nums(test_rank_records_dict, author_toggle))
        expected = """{'1': ('Life2', 'None', Node("/root/('Life2', '1')")), '181107': ('Plantae4', '1', Node("/root/('Life2', '1')/('Plantae4', '181107')"))}"""
        self.assertEqual(expected, actual)

    def test_build_tree_without_nums_with_author(self):
        """tests to confirm that tree building with author and without numbers works properly """
        test_rank_records_dict = {"1": [('None', 'Life', '1', 'test1')], "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = True
        actual = str(specifytreebuilder.build_tree_without_nums(test_rank_records_dict, author_toggle))
        expected = """{'1': ('Life', 'None', Node("/root/('Life', '1', 'test1')"))}"""
        self.assertEqual(expected, actual)

    def test_build_tree_without_nums_without_author(self):
        """tests to confirm that tree building with author and without numbers works properly """
        test_rank_records_dict = {"1": [('None', 'Life', '1', 'test1')], "4": [('1', 'Plantae4', '181107', 'test')]}
        author_toggle = False
        actual = str(specifytreebuilder.build_tree_without_nums(test_rank_records_dict, author_toggle))
        expected = """{'1': ('Life', 'None', Node("/root/('Life', '1')"))}"""
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
