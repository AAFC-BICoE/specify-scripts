""" 9 different test cases for the imagepull.py script.


Image 01-01000489870.JPG is to be used with this script for testing with metadata ***
"""
import unittest
import os
import csv
import datetime
import imagepull

class TestImagePull(unittest.TestCase):
    # Tests the imagepull.py script

    def test_copy_files_positive_directory(self):
        # Confirms a new directory is created and files are copied when no errors occur
        test_name = "ImagePull[%s]" % (datetime.date.today())
        test_destination = os.getcwd() + "/%s"
        test_new_dir = str(test_destination % test_name)
        with open("text.txt", "w") as file:
            file.write("test")
        test_image_paths = [os.path.abspath("text.txt")]
        imagepull.copy_files(test_image_paths, test_destination)
        actual = os.path.exists(test_new_dir + "/text.txt")
        expected = os.path.exists(test_destination % "text.txt")
        os.remove(test_new_dir + "/text.txt")
        os.remove(test_destination % "text.txt")
        os.rmdir(test_new_dir)
        self.assertEqual(expected, actual)

    def test_copy_files_negative_directory(self):
        # Confirms when errors occur, False is returned and no directory is created
        test_folder = "ImagePull[%s]" % (datetime.date.today())
        test_destination = os.getcwd() + "/%s"
        test_new_dir = str(test_destination % test_folder)
        os.mkdir(test_new_dir)
        test_image_paths = os.getcwd()
        actual = imagepull.copy_files(test_image_paths, test_destination)
        os.rmdir(test_new_dir)
        self.assertFalse(actual)

    def test_source_search(self):
        # Confirms the correct image path is returned for an image found in the source path
        test_source = os.getcwd()
        actual = imagepull.source_search(test_source)
        expected = [str(test_source + '/01-01000489870.JPG')]
        self.assertEqual(expected, actual)

    def test_md_search_positive(self):
        # Confirms that a metadata search with valid data returns the correct image path
        test_image_paths = [str(os.getcwd() + '/01-01000489870.JPG')]
        actual = imagepull.md_search(test_image_paths, "XPSubject", "Phalaris")
        expected = [str(os.getcwd() + '/01-01000489870.JPG')]
        self.assertEqual(expected, actual)

    def test_md_search_negative(self):
        # Confirms that a metadata search wih invalid data returns an empty list
        test_image_paths = [str(os.getcwd() + '/01-01000489870.JPG')]
        actual = imagepull.md_search(test_image_paths, "XPSubject", "test")
        self.assertFalse(actual)

    def test_csv_search_positive(self):
        # Confirms the expected path and conflict list is returned when a valid csv file is input
        with open("testcsv.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["01-01000489870"])
        test_csv_file = str((os.getcwd() + "/%s") % "testcsv.csv")
        actual = imagepull.csv_search(os.getcwd(), test_csv_file)
        expected = ([str(os.getcwd() + "/01-01000489870.JPG")], [])
        os.remove(test_csv_file)
        self.assertTupleEqual(expected, actual)

    def test_csv_search_negative(self):
        # Confirms the expected conflict list is returned when an invalid catalog number is present
        with open("testcsv.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["test"])
        test_csv_file = str((os.getcwd() + "/%s") % "testcsv.csv")
        actual = imagepull.csv_search(os.getcwd(), test_csv_file)
        expected = ([], [["test"]])
        os.remove(test_csv_file)
        self.assertTupleEqual(expected, actual)

    def test_csv_search_file_not_found(self):
        # Confirms the correct handling occurs when a csv file that does not exist is input
        test_csv_file = str((os.getcwd() + "/%s") % "test.csv")
        actual = imagepull.csv_search(os.getcwd(), test_csv_file)
        self.assertFalse(actual)

    def test_csv_report(self):
        # Confirms a report is created when report writing method is called
        imagepull.csv_report("testcsv", ["test", "headings"], ["testdata"], False)
        actual = os.path.exists(str(os.getcwd() + "/testcsv.csv"))
        os.remove(os.getcwd() + "/testcsv.csv")
        self.assertTrue(actual)



if __name__ == "__main__":
    unittest.main()
