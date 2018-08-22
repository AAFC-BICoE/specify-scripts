"""
8 test methods for the MultiCollectionQuery.py script.
"""
import os
import sqlite3
import unittest
import MultiCollectionQuery

class TestDatabase(unittest.TestCase):
    # Testing the script MultiCollectionQuery.py

    def setUp(self):
        # Creates the test database and test tables, inserts sample data into test tables
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE collectionobject (CatalogNumber, CollectionID, "
                       "CollectingEventID, CollectionObjectID, AltCatalogNumber)")
        test_collection_obj = [("1", "4", "10", "16", "test1"), ("2", "5", "11", "17", "test2"),
                               ("3", "6", "12", "18", "test3")]
        cursor.executemany("INSERT INTO collectionobject VALUES (?,?,?,?,?)", test_collection_obj)

        cursor.execute("CREATE TABLE collection (CollectionID, CollectionName)")
        test_collection = [("4", "test4"), ("5", "test5"), ("6", "test6")]
        cursor.executemany("INSERT INTO collection VALUES (?,?)", test_collection)

        cursor.execute("CREATE TABLE collectingevent "
                       "(CollectingEventID, StartDate DATE, LocalityID)")
        test_collecting_event = [("10", "2011-01-03", "25"), ("11", "2001-09-08", "26"),
                                 ("12", "2003-03-12", "27")]
        cursor.executemany("INSERT INTO collectingevent VALUES (?,?,?)", test_collecting_event)

        cursor.execute("CREATE TABLE collector (CollectingEventID, data1, AgentID )")
        test_collector = [("10", "13", "19"), ("11", "14", "20"), ("12", "15", "21")]
        cursor.executemany("INSERT INTO collector VALUES (?,?,?)", test_collector)

        cursor.execute("CREATE TABLE determination (CollectionObjectID, data1, TaxonID)")
        test_determination = [("16", "7", "22"), ("17", "17", "23"), ("18", "18", "24")]
        cursor.executemany("INSERT INTO determination VALUES (?,?,?)", test_determination)

        cursor.execute("CREATE TABLE agent (AgentID, LastName)")
        test_agent = [("19", "test7"), ("20", "test8"), ("21", "test9")]
        cursor.executemany("INSERT INTO agent VALUES (?,?)", test_agent)

        cursor.execute("CREATE TABLE taxon (TaxonID, FullName)")
        test_taxon = [("22", "test10"), ("23", "test11"), ("24", "test12")]
        cursor.executemany("INSERT INTO taxon VALUES (?,?)", test_taxon)

        cursor.execute("CREATE TABLE locality (LocalityID, data1, GeographyID)")
        test_locality = [("25", "7", "28"), ("26", "8", "29"), ("27", "9", "30")]
        cursor.executemany("INSERT INTO locality VALUES (?,?,?)", test_locality)

        cursor.execute("CREATE TABLE geography (GeographyID, FullName)")
        test_geography = [("28", "test13"), ("29", "test14"), ("30", "test15")]
        cursor.executemany("INSERT INTO geography VALUES (?,?)", test_geography)

        conn.commit()
        cursor.close()
        conn.close()
      
    def tearDown(self):
        # Removes the test database
        os.remove("specifytest.db")

    def test_format_records_multiple_collectors(self):
        # Confirms the function returns the expected list when multiple collectors are passed in
        test_query_data = (("catnum", "dao", "collection", "test1", "taxon", "locality", "year"),
                           ("catnum", "dao", "collection", "test2", "taxon", "locality", "year"))
        actual = MultiCollectionQuery.format_records(test_query_data)
        expected = ([["catnum", "dao", "collection", "test1, test2", "taxon", "locality", "year"]]
                    , 1)
        self.assertTupleEqual(expected, actual)

    def test_format_records_multiple_catalog_nums(self):
        # Confirms the function returns the correct number of unique catalognumbers
        test_query_data = (("catnum1", "dao", "collection", "test1", "taxon", "locality", "year"),
                           ("catnum2", "dao", "collection", "test2", "taxon", "locality", "year"))
        actual = MultiCollectionQuery.format_records(test_query_data)
        expected = ([["catnum1", "dao", "collection", "test1", "taxon", "locality", "year"],
                     ["catnum2", "dao", "collection", "test2", "taxon", "locality", "year"]], 2)
        self.assertEqual(expected, actual)

    def test_fetch_info_restriction_single_positive(self):
        # Confirms the expected list is returned containing the information from a restriction list
        conn = sqlite3.connect("specifytest.db")
        test_restriction_list = "CL.CollectionName LIKE 'test4'"
        actual = MultiCollectionQuery.fetch_info(conn, test_restriction_list)
        expected = ([["1", "test1", "test4", "test7", "test10", "test13", "2011-01-03"]], 1)
        self.assertEqual(expected, actual)

    def test_fetch_info_restriction_single_negative(self):
        # Confirms an empty list is returned when an invalid restriction is passed in
        conn = sqlite3.connect("specifytest.db")
        test_restriction_list = "G.FullName LIKE '1'"
        actual = MultiCollectionQuery.fetch_info(conn, test_restriction_list)
        expected = ([], 0)
        self.assertEqual(expected, actual)

    def test_fetch_info_restriction_multi_positive(self):
        # Confirms the expected list is returned when multiple valid restrictions are passed in
        conn = sqlite3.connect("specifytest.db")
        test_restriction_list = "CO.CatalogNumber LIKE '1' AND A.LastName LIKE 'test7'"
        actual = MultiCollectionQuery.fetch_info(conn, test_restriction_list)
        expected = ([["1", "test1", "test4", "test7", "test10", "test13", "2011-01-03"]], 1)
        self.assertEqual(expected, actual)

    def test_fetch_info_restriction_multi_negative(self):
        # Confirms an empty list is returned when multiple invalid restrictions are passed in
        conn = sqlite3.connect("specifytest.db")
        test_restriction_list = "CO.AltCatalogNumber LIKE '7' AND T.FullName LIKE 'test7'"
        actual = MultiCollectionQuery.fetch_info(conn, test_restriction_list)
        expected = ([], 0)
        self.assertEqual(expected, actual)

    def test_format_args_single(self):
        # Confirms the expected list is returned when a valid single restriction is passed in
        test_catalognum = "test"
        test_dao, test_lastname, test_taxon, test_year, test_province = "", "", "", "", ""
        actual = MultiCollectionQuery.format_args(test_catalognum, test_dao, test_lastname,
                                                  test_taxon, test_year, test_province)
        expected = "CO.CatalogNumber LIKE 'test' AND A.LastName LIKE '%%' AND G.FullName LIKE '%%' "
        self.assertEqual(expected, actual)

    def test_format_args_all(self):
        # Confirms the expected list is returned when all possible restrictions are passed in
        test_catalognum, test_taxon, test_lastname, test_dao, test_year, test_province = \
            "test1", "test2", "test3", "test4", "test5", "test6"
        actual = MultiCollectionQuery.format_args\
            (test_catalognum, test_dao, test_lastname, test_taxon, test_year, test_province)
        expected = "CO.CatalogNumber LIKE 'test1' AND CO.AltCatalogNumber LIKE 'test4' " \
                   "AND A.LastName LIKE '%test3%' AND T.FullName LIKE 'test2' " \
                   "AND YEAR(CE.StartDate) LIKE 'test5' AND G.FullName LIKE '%test6%' "
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
