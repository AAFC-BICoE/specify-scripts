"""
13 test methods for the typosearch.py script.
"""
import os
import unittest
import datetime
import typosearch

class TestTypoSearch(unittest.TestCase):
    # Tests the typosearch.py script. Script only tests the methods that do not correspond to tree
    # Iteration to avoid type conversion conflicts.

    def test_check_author_positive(self):
        # Confirms the correct distance value is returned when valid parameters are passed in
        actual = typosearch.check_author("C", "test", "C", "test1")
        expected = 1
        self.assertEqual(expected, actual)

    def test_check_author_negative(self):
        # Confirms False is returned when invalid parameters are passed in
        actual = typosearch.check_author("C", "test", "D", "test1")
        self.assertFalse(actual)

    def test_find_taxon_typos_name1_brackets_positive(self):
        # Confirms the expected list is returned when name1's author begins with a bracket
        test_name1 = ("testname", 123, "(testAuthor)")
        test_name2 = ("testname3", 456, "test")
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        expected = [("taxonname", "testname", "testname3", "(testAuthor)", "test", 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_name1_brackets_negative(self):
        # Confirms an empty list is returned when name1's author begins with brackets and the names
        # Do not meet the requirement to be flagged as a possible typo
        test_name1 = ("testname", 123, "[bestAuthor]")
        test_name2 = ("testname3", 456, "test")
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        self.assertFalse(actual)

    def test_find_taxon_typos_name2_brackets_positive(self):
        # Confirms the expected list is returned when name2's author begins with brackets and the
        # Names meet the requirements to be flagged as a possible typo
        test_name1 = ("testname", 123, "testAuthor")
        test_name2 = ("testname3", 456, "[test]")
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        expected = [("taxonname", "testname", "testname3", "testAuthor", "[test]", 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_name2_brackets_negative(self):
        # Confirms an empty list is returned when name2's author begins with brackets and the names
        # Do not meet the requirements to be flagged as a possible typo
        test_name1 = ("testname", 123, "bestAuthor")
        test_name2 = ("testname3", 456, "(test)")
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        self.assertFalse(actual)
        
    def test_find_taxon_typos_name1_name2_positive(self):
        # Confirms the correct list is returned when names are flagged as a possible typo
        test_name1 = ("testname", 123, "testAuthor")
        test_name2 = ("testname3", 456, "test")
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        expected = [("taxonname", "testname", "testname3", "testAuthor", "test", 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_name1_name2_negative(self):
        # Confirms an empty list is returned when the authors begin with different letters
        test_name1 = ("testname", 123, "bestAuthor")
        test_name2 = ("testname3", 456, "test")
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        self.assertFalse(actual)

    def test_find_taxon_typos_authors_positive(self):
        # Confirms the correct list is returned when the author is None for both names and names
        # Have a LD of <= 2
        test_name1 = ("testname", 123, None)
        test_name2 = ("testname3", 456, None)
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        expected = [("taxonname", "testname", "testname3", None, None, 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_names_negative(self):
        # Confirms an empty list is returned when the author is None for both names and LD is > 2
        test_name1 = ("cat", 123, None)
        test_name2 = ("horse", 456, None)
        test_data = ["", "taxonname"]
        actual = typosearch.find_taxon_typos(test_name1, test_name2, [], test_data, 2)
        self.assertFalse(actual)

    def test_find_geography_typos_positive(self):
        # Confirms the correct list is returned for names that have a LD <= 2
        test_name_list = [(("test", 123), ("test1", 456))]
        test_data = ("", "geographyname")
        actual = typosearch.find_geography_typos(test_name_list, [], test_data, 2)
        expected = [("geographyname", "test", "test1", 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_geography_typos_negative(self):
        # Confirms an empty list is returned for names that have a LD > 2
        test_name_list = [(("cat", 123), ("horse", 456))]
        test_data = ("", "geographyname")
        actual = typosearch.find_geography_typos(test_name_list, [], test_data, 2)
        self.assertFalse(actual)

    def test_report_exists(self):
        # Confirms a report is create/exists when the report method is called
        test_file_name = "TypoReport[%s]" % (datetime.date.today())
        test_headings = ["test"]
        test_result_data = ["data1", "data2"]
        typosearch.report(test_headings, test_result_data, False)
        test_file_path = str(os.getcwd() + "/" + test_file_name + ".csv")
        actual = os.path.exists(test_file_path)
        os.remove(test_file_path)
        self.assertTrue(actual)

if __name__ == "__main__":
    unittest.main()
