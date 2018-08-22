"""
6 different tests methods for the script replaceagents.py.
"""
import unittest
import os
import sqlite3
import replaceagents

class TestDatabase(unittest.TestCase):
    # Testing the script replaceagents.py

    def setUp(self):
        # Creates test database and inserts sample data
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE agent (AgentID NOT NULL, GUID, PRIMARY KEY(AgentID))")
        test_agent = [("1", "test1"), ("2", "test2"), ("3", "test3"),
                      ("4", "test4"), ("5", "test5"), ("6", "test6")]
        cursor.executemany("INSERT INTO agent VALUES (?,?)", test_agent)
        cursor.execute("CREATE TABLE table1 (AgentID, data3, FOREIGN KEY(AgentID) "
                       "REFERENCES agent(AgentID))")
        test_table_1 = [("1", "test11"), ("2", "test12"), ("3", "test13"), ("7", "test14")]
        cursor.executemany("INSERT INTO table1 VALUES (?,?)", test_table_1)
        cursor.execute("CREATE TABLE table2 (AgentID, data4, FOREIGN KEY(AgentID) "
                       "REFERENCES agent(AgentID))")
        test_table_2 = [("4", "test15"), ("6", "test16"), ("5", "test17"), ("3", "test18")]
        cursor.executemany("INSERT INTO table2 VALUES (?,?)", test_table_2)
        conn.commit()
        cursor.close()
        conn.close()

    def tearDown(self):
        # Removes test database
        os.remove("specifytest.db")

    def test_agent_info_positive(self):
        # Confirms that the correct AgentID is returned when a valid GUID is passed in
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_guid = "test1"
        actual = replaceagents.agent_info(conn, test_guid)
        expected = [("1",)]
        self.assertListEqual(expected, actual)

    def test_agent_info_negative(self):
        # Confirms that an empty list is returned when an invalid GUID is passed in
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_guid = "test7"
        actual = replaceagents.agent_info(conn, test_guid)
        expected = []
        self.assertListEqual(expected, actual)

    def test_update_agents_positive(self):
        # Confirms the correct list is returned when valid GUIDs are passed in with no conflicts
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_integrity_error = sqlite3.IntegrityError
        test_guid_list = [["test1", "test2"]]
        test_agent_references = (("table1", "AgentID"),)
        actual = replaceagents.update_agents(
            conn, test_guid_list, test_agent_references, test_integrity_error)
        expected = ([("1", "2")], [])
        self.assertTupleEqual(expected, actual)

    def test_update_agents_negative_guid(self):
        # Confirms the correct list is returned when invalid GUIDs are passed in with conflicts
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_integrity_error = sqlite3.IntegrityError
        test_guid_list = [["test1", "test2"], ["test3", "test9"]]
        test_agent_references = (("table1", "AgentID"), )
        actual = replaceagents.update_agents(
            conn, test_guid_list, test_agent_references, test_integrity_error)
        expected = ([("1", "2")], [["test3", "test9"]])
        self.assertTupleEqual(expected, actual)

    def test_update_agents_negative_conflicts(self):
        # Confirms the correct list is returned when valid GUIDs are passed in with conflicts
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_integrity_error = sqlite3.IntegrityError
        test_guid_list = [["test3", "test2"],]
        test_agent_references = (("table1", "AgentID"), )
        actual = replaceagents.update_agents(
            conn, test_guid_list, test_agent_references, test_integrity_error)
        expected = ([("3", "2")], [["test3", "test2"]])
        self.assertTupleEqual(expected, actual)

    def test_update_agents_check(self):
        # Confirms the "Bad Agent" is deleted from the schema when valid GUID's are passed in
        conn = sqlite3.connect("specifytest.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        test_integrity_error = sqlite3.IntegrityError
        test_guid_list = [["test1", "test2"]]
        test_agent_references = (("table1", "AgentID"),)
        replaceagents.update_agents(
            conn, test_guid_list, test_agent_references, test_integrity_error)
        cursor.execute("SELECT * FROM agent WHERE AgentID = '1'")
        self.assertFalse(cursor.fetchall())

if __name__ == "__main__":
    unittest.main()
