"""
4 different test methods for the script csvwriter.
"""
import  os
import csv
import unittest
from specifycleaning import csvwriter

class WriteReport(unittest.TestCase):
    # Tests the write_report function from the csvwriter.py module

    def test_file_exists(self):
        # Confirms that a csv file with the file name does not already exist in directory
        test_file_name = "test"
        result = os.path.exists("%s.csv" % test_file_name)
        self.assertFalse(result)

    def test_file_create(self):
        # Confirms that a csv is created when function is called on
        test_file_name = "test"
        test_heading = ["test"]
        test_data = ["a", "b", "c"]
        csvwriter.write_report(test_file_name, test_heading, test_data)
        result = os.path.exists("%s.csv" % test_file_name)
        os.remove("%s.csv" % test_file_name)
        self.assertTrue(result)

    def test_in_file(self):
        # Confirms that a test object passed into function appears in the csv file
        test_file_name = "test"
        test_heading = ["test"]
        test_data = ["a", "b", "c"]
        csvwriter.write_report(test_file_name, test_heading, test_data)
        test_object = "a"
        result = False
        with open("%s.csv" % test_file_name, "rt") as test_file:
            test_reader = csv.reader(test_file, delimiter=",")
            for row in test_reader:
                for field in row:
                    if field == test_object:
                        result = True
        os.remove("%s.csv" % test_file_name)
        self.assertTrue(result)

    def test_is_not_in_file(self):
        # Confirms that a test object not passed in is not in the csv file
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
