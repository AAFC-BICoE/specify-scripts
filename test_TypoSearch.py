# Tests the TypoSearch script for 13 cases. Script only tests the TypoSearch functions that do not correspond to any
# Tree iteration to avoid type conversion conflicts
import TypoSearch, os, unittest, datetime

class TestTypoSearch(unittest.TestCase):

    def test_check_author_positive(self):
        # Tests to confirm the function check_author returns the correct LD when valid parameters are passed in
        test_author_letter_1 = "C"
        test_name1 = "test"
        test_author_letter_2 = "C"
        test_name2 = "test1"
        actual = TypoSearch.check_author(test_author_letter_1,test_name1,test_author_letter_2,test_name2)
        expected = 1
        self.assertEqual(expected,actual)

    def test_check_author_negative(self):
        # Tests to confirm the function check_author returns False when invalid parameters are passed in
        test_author_letter_1 = "C"
        test_name1 = "test"
        test_author_letter_2 = "D"
        test_name2 = "test1"
        actual = TypoSearch.check_author(test_author_letter_1,test_name1,test_author_letter_2,test_name2)
        self.assertFalse(actual)

    def test_find_taxon_typos_name1_brackets_positive(self):
        # Tests to confirm when taxon name1's author first letter begins with brackets and the rest of the node meets
        # The requirements to be flagged as a possible typo, the correct list is returned
        test_name1 = ("testname",123,"(testAuthor)")
        test_name2 = ("testname3", 456, "test")
        test_result_data = []
        test_data = ["","taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1,test_name2,test_result_data,test_data)
        expected = [("taxonname","testname","testname3","(testAuthor)","test",123,456,1)]
        self.assertListEqual(expected,actual)

    def test_find_taxon_typos_name1_brackets_negative(self):
        # Tests to confirm when taxon name1's author first letter begins with brackets and the rest of the node does not
        # Meet the requirements to be flagged as a possible typo, an empty list is returned
        test_name1 = ("testname", 123, "[bestAuthor]")
        test_name2 = ("testname3", 456, "test")
        test_result_data = []
        test_data = ["", "taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1, test_name2, test_result_data, test_data)
        expected = []
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_name2_brackets_positive(self):
        # Tests to confirm when taxon name2's author first letter begins with brackets and the rest of the node meets
        # The requirements to be flagged as a possible typo, the correct list is returned
        test_name1 = ("testname",123,"testAuthor")
        test_name2 = ("testname3", 456, "[test]")
        test_result_data = []
        test_data = ["","taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1,test_name2,test_result_data,test_data)
        expected = [("taxonname","testname","testname3","testAuthor","[test]",123,456,1)]
        self.assertListEqual(expected,actual)

    def test_find_taxon_typos_name2_brackets_negative(self):
        # Tests to confirm when taxon name2's author first letter begins with brackets and the rest of the node does not
        # Meet the requirements to be flagged as a possible typo, an empty list is returned
        test_name1 = ("testname", 123, "bestAuthor")
        test_name2 = ("testname3", 456, "(test)")
        test_result_data = []
        test_data = ["", "taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1, test_name2, test_result_data, test_data)
        expected = []
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_name1_name2_positive(self):
        # Tests to confirm when taxon name1 and name2 have author first letters beginning with letters and the rest of
        # The node meets the requirements to be flagged as a possible typo, the correct list is returned
        test_name1 = ("testname", 123, "testAuthor")
        test_name2 = ("testname3", 456, "test")
        test_result_data = []
        test_data = ["", "taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1, test_name2, test_result_data, test_data)
        expected = [("taxonname", "testname", "testname3", "testAuthor", "test", 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_name1_name2_negative(self):
        # Tests to confirm when taxon name1 and name2 have author first letters beginning with different letters and the
        # Rest of the node meets the requirements to be flagged as a possible typo, an empty list is returned
        test_name1 = ("testname", 123, "bestAuthor")
        test_name2 = ("testname3", 456, "test")
        test_result_data = []
        test_data = ["", "taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1, test_name2, test_result_data, test_data)
        expected = []
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_authors_positive(self):
        # Tests to confirm when taxon name1 and name2 have the author field as None and the rest of the node meets the
        # Requirements to be flagged as a possible typo, the correct list is returned
        test_name1 = ("testname", 123, None)
        test_name2 = ("testname3", 456, None)
        test_result_data = []
        test_data = ["", "taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1, test_name2, test_result_data, test_data)
        expected = [("taxonname","testname","testname3", None, None, 123, 456, 1)]
        self.assertListEqual(expected, actual)

    def test_find_taxon_typos_names_negative(self):
        # Tests to confirm that when taxon name1 and name2 have the author field as Node and name1 and name2 have names
        # With a LD greater than 2, an empty list is returned
        test_name1 = ("cat", 123, None)
        test_name2 = ("horse", 456, None)
        test_result_data = []
        test_data = ["", "taxonname"]
        actual = TypoSearch.find_taxon_typos(test_name1, test_name2, test_result_data, test_data)
        expected = []
        self.assertListEqual(expected, actual)

    def test_find_geography_typos_positive(self):
        # Tests to confirm that the correct list is returned when geography names that have a LD of 1 or 2 are passed in
        test_name_list = [(("test",123),("test1",456))]
        test_result_data = []
        test_data = ("","geographyname")
        actual = TypoSearch.find_geography_typos(test_name_list,test_result_data,test_data)
        expected = [("geographyname","test","test1",123,456,1)]
        self.assertListEqual(expected,actual)

    def test_find_geography_typos_negative(self):
        # Tests to confirm that an empty list is returned when geography names that have a LD not equal to 1 or 2 are
        # Passed in
        test_name_list = [(("cat",123),("horse",456))]
        test_result_data = []
        test_data = ("","geographyname")
        actual = TypoSearch.find_geography_typos(test_name_list,test_result_data,test_data)
        expected = []
        self.assertListEqual(expected,actual)

    def test_report_exists(self):
        # Tests to confirm that when the report writing function is called, a report is actually created
        test_file_name = "TypoReport[%s]" % (datetime.date.today())
        test_headings = ["test"]
        test_result_data = ["data1","data2"]
        test_show = False
        TypoSearch.report(test_headings,test_result_data,test_show)
        test_file_path = str(os.getcwd() + "/" + test_file_name + ".csv")
        actual = os.path.exists(test_file_path)
        self.assertTrue(actual)
        os.remove(test_file_path)

if __name__ == "__main__":
    unittest.main()
