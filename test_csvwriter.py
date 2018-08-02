"""
Tests the csvwriter module for 4 different cases: to confirm the test file does not already exist, to
confirm the test file is actually created, to confirm that the data passed in is written to the test.csv
and to confirm that there is no data in the csv file that shouldn't be. In each test case, a csv file
is created and then destroyed.
"""
import unittest, csvwriter, os, csv

class WriteReport(unittest.TestCase):
    """
    Testing the write_report function form the csvwriter module
    """
    def test_file_exists(self):
        """
        tests that a csv file with the file name does not already exist
        """
        test_file_name =  "test"
        result = os.path.exists("%s.csv" % test_file_name)
        self.assertFalse(result)

    def test_file_create(self):
        """
        tests that a csv is created
        """
        test_file_name = "test"
        test_heading = ["test"]
        test_data = ["a", "b", "c"]
        csvwriter.write_report(test_file_name,test_heading,test_data)
        result = os.path.exists("%s.csv" %test_file_name)
        os.remove("%s.csv" % test_file_name)
        self.assertTrue(result)

    def test_in_file(self):
        """
        tests that a test object passed in, is in the csv file
        """
        test_file_name = "test"
        test_heading = ["test"]
        test_data = ["a", "b", "c"]
        csvwriter.write_report(test_file_name, test_heading, test_data)
        test_object = "a"
        result = False
        with open("%s.csv"%test_file_name,"rt") as test_file:
            test_reader = csv.reader(test_file,delimiter =",")
            for row in test_reader:
                for field in row:
                    if field == test_object:
                      result = True
        os.remove("%s.csv" % test_file_name)
        self.assertTrue(result)

    def test_is_not_in_file(self):
        """
        tests that a test object is not in the csv file
        """
        test_file_name = "test"
        test_heading = ["test"]
        test_data = ["a", "b", "c"]
        csvwriter.write_report(test_file_name, test_heading, test_data)
        test_object = "d"
        result = False
        with open("%s.csv" % test_file_name, "rt") as test_file:
            test_reader = csv.reader(test_file, delimiter=",")
            for row in test_reader:
                for field in row:
                    if field == test_object:
                        result = True
        os.remove("%s.csv" % test_file_name)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()