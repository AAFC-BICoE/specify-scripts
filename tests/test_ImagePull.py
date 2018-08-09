""" Tests the ImagePull script across 16 different cases.
**NOTE: Some operating systems name metadata tags differently, some test functions have the dictionary 'system_names'
VALUES changed to what the particular OS calls the fields 'subject' and 'tags'.***
"""
import unittest, ImagePull, os, csv, datetime

class TestImagePull(unittest.TestCase):
    """Tests the ImagePull script"""

    def test_configure_combo(self):
        """tests to confirm the configure function returns an int when given a string containing numbers and letters"""
        test_number = "0t1e2s3t4"
        actual = ImagePull.configure(test_number)
        expected = 1234
        self.assertEqual(expected,actual)

    def test_configure_string(self):
        """tests to confirm the configure function returns None when given a string containing no numbers"""
        test_number = "test"
        actual = ImagePull.configure(test_number)
        expected = None
        self.assertEqual(expected, actual)

    def test_configure_numbers(self):
        """tests to confirm the configure function returns an int when given string containing only numbers"""
        test_number = "01234"
        actual = ImagePull.configure(test_number)
        expected = 1234
        self.assertEqual(expected, actual)

    def test_copy_files_positive_directory(self):
        """tests to confirm that when no errors occur, a new directory is created"""
        test_folder = "ImagePull[%s]" % (datetime.date.today())
        test_destination = os.getcwd() + "/%s"
        test_new_dir = str(test_destination % test_folder)
        with open("text.txt","w") as file:
            file.write("test")
        test_image_paths = [os.path.abspath("text.txt")]
        ImagePull.copy_files(test_image_paths,test_destination)
        actual = os.path.exists(test_new_dir)
        os.remove(test_new_dir + "/text.txt")
        os.remove(test_destination % "text.txt")
        os.rmdir(test_new_dir)
        self.assertTrue(actual)

    def test_copy_files_negative_directory(self):
        """tests to confirm that when errors occur, False is returned and no directory is created"""
        test_folder = "ImagePull[%s]" % (datetime.date.today())
        test_destination = os.getcwd() + "/%s"
        test_new_dir = str(test_destination % test_folder)
        os.mkdir(test_new_dir)
        test_image_paths = os.getcwd()
        actual = ImagePull.copy_files(test_image_paths,test_destination)
        os.rmdir(test_new_dir)
        self.assertFalse(actual)

    def test_copy_files_copied(self):
        """tests to confirm when there are no conflicts a file is actually copied and is present in the new directory"""
        test_folder = "ImagePull[%s]" % (datetime.date.today())
        test_destination = os.getcwd() + "/%s"
        test_new_dir = str(test_destination % test_folder)
        with open("text.txt", "w") as file:
            file.write("test")
        test_image_paths = [os.path.abspath("text.txt")]
        ImagePull.copy_files(test_image_paths, test_destination)
        actual = os.path.exists(test_new_dir + "/text.txt")
        os.remove(test_new_dir + "/text.txt")
        os.remove(test_destination % "text.txt")
        os.rmdir(test_new_dir)
        self.assertTrue(actual)

    def test_source_search(self):
        """tests to confirm that the correct image path is returned for the image in the file path"""
        test_source = os.getcwd()
        actual = ImagePull.source_search(test_source)
        expected = [str(test_source + '/01-01000489870.JPG')]
        self.assertEqual(expected,actual)

    def test_multi_md_search_positive(self): ## VALUES MAY NEED TO BE CHANGED FOR DIFFERENT OPERATING SYSTEMS
        """tests to confirm that a search across the metadata fields 'subject' and 'tags' return the correct paths when
        valid metadata tags are passed in"""
        system_names = {"subject": "XPSubject","tags": "XPKeywords"}
        test_image_paths = [str(os.getcwd() + '/01-01000489870.JPG')]
        test_field1 = system_names["subject"]
        test_keyword1 = "Phalaris"
        test_field2 = system_names["tags"]
        test_keyword2 = "PMC"
        actual = ImagePull.multi_md_search(test_image_paths,test_field1,test_field2,test_keyword1,test_keyword2)
        expected = [str(os.getcwd() + '/01-01000489870.JPG')]
        self.assertEqual(expected,actual)

    def test_multi_md_search_negative(self): ## VALUES MAY NEED TO BE CHANGED FOR DIFFERENT OPERATING SYSTEMS
        """tests to confirm that a search across the metadata fields 'subject' and 'tags' return an empty list when non
        existent metadata tags are passed in"""
        system_names = {"subject": "XPSubject","tags": "XPKeywords"}
        test_image_paths = [str(os.getcwd() + '/01-01000489870.JPG')]
        test_field1 = system_names["subject"]
        test_keyword1 = "test"
        test_field2 = system_names["tags"]
        test_keyword2 = "PMC"
        actual = ImagePull.multi_md_search(test_image_paths, test_field1, test_field2, test_keyword1, test_keyword2)
        expected = []
        self.assertEqual(expected, actual)

    def test_single_md_search_positive(self): ## VALUES MAY NEED TO BE CHANGED FOR DIFFERENT OPERATING SYSTEMS
        """tests to confirm that a single metadata search with valid data returns the correct paths"""
        system_names = {"subject": "XPSubject", "tags": "XPKeywords"}
        test_image_paths = [str(os.getcwd() + '/01-01000489870.JPG')]
        test_field = system_names["subject"]
        test_keyword = "Phalaris"
        actual = ImagePull.single_md_search(test_image_paths,test_field,test_keyword)
        expected = [str(os.getcwd() + '/01-01000489870.JPG')]
        self.assertEqual(expected, actual)

    def test_single_md_search_negative(self): ## VALUES MAY NEED TO BE CHANGED FOR DIFFERENT OPERATING SYSTEMS
        """tests to confirm that a single metadata search wih invalid data returns an empty list"""
        system_names = {"subject": "XPSubject", "tags": "XPKeywords"}
        test_image_paths = [str(os.getcwd() + '/01-01000489870.JPG')]
        test_field = system_names["subject"]
        test_keyword = "test"
        actual = ImagePull.single_md_search(test_image_paths,test_field,test_keyword)
        expected = []
        self.assertEqual(expected, actual)

    def test_csv_search_positive(self):
        """tests to confirm that the correct path is returned when valid catalog number is read from a valid csv file"""
        test_source = os.getcwd()
        test_destination = os.getcwd() + "/%s"
        with open("testcsv.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["01-01000489870"])
        test_csv_file =   str(test_destination % "testcsv.csv")
        actual = ImagePull.csv_search(test_source,test_destination,test_csv_file)
        expected = [str(os.getcwd() +  "/01-01000489870.JPG")]
        os.remove(test_csv_file)
        self.assertEqual(expected,actual)

    def test_csv_search_negative(self):
        """tests to confirm that an empty list is returned when a valid csv file contains an invalid catalog number"""
        test_source = os.getcwd()
        test_destination = os.getcwd() + "/%s"
        with open("testcsv.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["test"])
        test_csv_file = str(test_destination % "testcsv.csv")
        actual = ImagePull.csv_search(test_source, test_destination, test_csv_file)
        expected = []
        os.remove(test_csv_file)
        self.assertEqual(expected, actual)

    def test_csv_search_file_not_found(self):
        """tests to confirm that the correct handling of a csv file that does not exist occurs"""
        test_source = os.getcwd()
        test_destination = os.getcwd() + "/%s"
        test_csv_file = str(test_destination % "test.csv")
        actual = ImagePull.csv_search(test_source,test_destination,test_csv_file)
        expected = None
        self.assertEqual(expected,actual)

    def test_csv_search_images_not_found(self):
        """tests to confirm that if there are catalognumbers not found in original csv then a csv report is created"""
        test_source = os.getcwd()
        test_destination = os.getcwd() + "/%s"
        test_file_name = "ImagesNotFound[%s]" % (datetime.date.today())
        with open("testcsv.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["01-01000489870"])
            writer.writerow(["01-01234"])
        test_csv_file = str(test_destination % "testcsv.csv")
        ImagePull.csv_search(test_source, test_destination, test_csv_file)
        actual = os.path.exists(str(test_destination % test_file_name + ".csv"))
        os.remove(str(test_destination % test_file_name + ".csv"))
        self.assertTrue(actual)

    def test_images_not_found_contents(self):
        """tests to confirm that the catalog numbers that are not found are actually written to the not found report"""
        test_source = os.getcwd()
        test_destination = os.getcwd() + "/%s"
        test_file_name = str(test_destination % ("ImagesNotFound[%s].csv" % (datetime.date.today())))
        with open("testcsv.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["01-01000489870"])
            writer.writerow(["01-01234"])
        test_csv_file = str(test_destination % "testcsv.csv")
        ImagePull.csv_search(test_source, test_destination, test_csv_file)
        actual = [row[0] for row in csv.reader(open(test_file_name, newline=""))]
        expected = ["Image Names Not Found","01-01234"]
        os.remove(test_file_name)
        self.assertEqual(expected,actual)

if __name__ == "__main__":
    unittest.main()
