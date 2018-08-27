"""
Merges two collections together by switching references of the source collection to the destination
collection. If there are catalog number conflicts, a report of the conflicting catalog numbers is
created and no collection objects are merged. If there are no conflicts, then collection merge is
preformed. Defaults to saving a report of the catalog numbers that will be merged unless --merge
command is executed. Deletes the empty collection with the --delete command.
"""
import argparse
import datetime
import pymysql
from specifycleaning.csvwriter import write_report

def fetch_catalog_numbers(database, collectionid):
    # Returns list of catalog numbers in collection passed in
    db_catalog_numbers = database.cursor()
    db_catalog_numbers.execute("SELECT CatalogNumber FROM collectionobject "
                               "WHERE CollectionID = '%s'" % collectionid)
    return [[catalog_number[0]] for catalog_number in db_catalog_numbers.fetchall()]

def check_conflicts(database, source, destination):
    # Returns list of catalog number conflicts and list of catalog numbers in source collection
    source_catalog_numbers = fetch_catalog_numbers(database, source)
    destination_catalog_numbers = fetch_catalog_numbers(database, destination)
    conflict = [cn for cn in source_catalog_numbers if cn in destination_catalog_numbers]
    return conflict, source_catalog_numbers

def switch_references(database, table_list, source, destination):
    # Updates references of source collection to destination collection according to table list
    db_update = database.cursor()
    for table, column in table_list:
        db_update.execute("UPDATE %s SET %s = '%s' WHERE %s = '%s' "
                          % (table, column, destination, column, source))
        database.commit()

def delete_collection(database, source, integrity_error):
    # Deletes (now empty) source collection from schema, returns any integrity error conflicts
    db_delete = database.cursor()
    try:
        db_delete.execute("DELETE FROM collection WHERE collectionID = '%s'" % source)
        database.commit()
        return None
    except integrity_error:
        return False

def csv_report(file_name, headings, result_data, show):
    # Writes report, displays data if specified
    if show:
        for row in result_data:
            print(headings[0], ": ", row[0])
    return write_report(file_name, headings, result_data)

def main():
    # Creates command line arguments and coordinates functions
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username",
                        help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password",
                        help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="Name of MySQL Specify database", required=True)
    parser.add_argument("-source_collection", action="store", dest="source",
                        help="CollectionID of collection that will be merged (will become empty)",
                        required=True)
    parser.add_argument("-destination_collection", action="store", dest="destination",
                        help="CollectionID of collection that will have collection objects added",
                        required=True)
    parser.add_argument("--report", action="store_true", dest="report",
                        help="(default) Create a report of what Catalog Numbers will be merged",
                        default=True)
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Display Catalog Numbers that will be merged")
    parser.add_argument("--merge", action="store_true", dest="merge",
                        help="Merge collection1 into collection2")
    parser.add_argument("--delete", action="store_true", dest="delete",
                        help="Delete (empty) collection1 after merge")
    args = parser.parse_args()
    source = args.source
    destination = args.destination
    report = args.report
    show = args.show
    merge = args.merge
    delete = args.delete
    integrity_error = pymysql.err.IntegrityError
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database")
    if report:
        # Returns list of conflicts (if any), list of catalog numbers from destination collection
        conflicts, source_catalog_numbers = check_conflicts(database, source, destination)
        if conflicts:
            file_name = ("CatalogNumberConflicts[%s]" % (datetime.date.today()))
            csv_report(file_name, ["Conflicting Catalog Number"], conflicts, show)
            print("No collection objects merged")
            print("%s conflicts found, saved as %s.csv" % (len(conflicts), file_name))
            return print("See -h for more options")
        if merge:
            db_switch_ref = database.cursor()
            db_switch_ref.execute("SELECT TABLE_NAME, COLUMN_NAME FROM "
                                  "INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE "
                                  "CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME IN "
                                  "('CollectionID','CollectionMemberID','UserGroupScopeID') "
                                  "AND TABLE_NAME != 'collection'")
            table_list = db_switch_ref.fetchall()
            switch_references(database, table_list, source, destination)
            print("%s collection objects merged" % len(source_catalog_numbers))
            if delete:
                delete = delete_collection(database, destination, integrity_error)
                if delete:
                    return print("Integrity Error occurred when attempting to delete collection "
                                 "%s, see -h for more options" % destination)
                print("Collection %s deleted from schema" % destination)
            file_name = "CatalogNumbersMerged[%s]" % (datetime.date.today())
            csv_report(file_name, ["Catalog Number Merged"], source_catalog_numbers, show)
            return print("Report saved as %s" % file_name)
        file_name = "CatalogNumbersToBeMerged[%s]" % (datetime.date.today())
        csv_report(file_name, ["Catalog Number Merged"], source_catalog_numbers, show)
        print("No collection objects merged\nReport saved as %s" % file_name)
    return None

if __name__ == "__main__":
    main()
