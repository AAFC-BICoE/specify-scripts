"""
Merges two collections together by switching references of collection being merged (collection1)
to the collection being merged into (collection2). If there are catalog number conflicts, a report
of the catalog numbers is created. If there are no conflicts, then collection merge is preformed.

NOTE: Defaults to saving a report of the catalog numbers that will be merged unless --merge command
is executed. Deletes the empty collection with the --delete command.
"""
import argparse
import datetime
import pymysql
from csvwriter import write_report

def fetch_catalog_numbers(database, collectionid):
    # Returns list of catalog numbers in collection
    db_catalog_numbers = database.cursor()
    db_catalog_numbers.execute("SELECT CatalogNumber FROM collectionobject "
                               "WHERE CollectionID = '%s'" % collectionid)
    return [[catalog_number[0]] for catalog_number in db_catalog_numbers.fetchall()]

def check_conflicts(database, collection1, collection2):
    # Returns list of conflicting catalog numbers and list of catalog numbers from collection1
    cat_numbers1 = fetch_catalog_numbers(database, collection1)
    cat_numbers2 = fetch_catalog_numbers(database, collection2)
    conflict = [cn for cn in cat_numbers1 if cn in cat_numbers2]
    return conflict, cat_numbers1

def switch_references(database, table_list, collection1, collection2):
    # Updates references of collection1 to collection2 from passed in table list
    db_update = database.cursor()
    for table in table_list:
        db_update.execute("UPDATE %s SET %s = '%s' WHERE %s = '%s' "
                          % (table[0], table[1], collection2, table[1], collection1))
        database.commit()

def delete_collection(database, collectionid, integrity_error):
    # Deletes collection1 from schema, returns any integrity error conflicts
    db_delete = database.cursor()
    try:
        db_delete.execute("DELETE FROM collection WHERE collectionID = '%s'" % collectionid)
        database.commit()
        return None
    except integrity_error:
        return False

def csv_report(file_name, headings, result_data, show):
    # Writes report, displays data if specified
    if show:
        for row in result_data:
            print(row[0])
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
    parser.add_argument("-collection1", action="store", dest="cid1",
                        help="CollectionID of collection that will be merged (will be removed)",
                        required=True)
    parser.add_argument("-collection2", action="store", dest="cid2",
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
    collection1 = args.cid1
    collection2 = args.cid2
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
        catalog_numbers = check_conflicts(database, collection1, collection2)
        if len(catalog_numbers[0]) > 1:
            file_name = ("CatalogNumberConflicts[%s]" % (datetime.date.today()))
            csv_report(file_name, ["Conflicting Catalog Numbers"], catalog_numbers[0], show)
            print("No collection objects merged")
            print("%s conflicts found, saved as %s.csv" % (len(catalog_numbers[0]), file_name))
            return print("See -h for more options")
        headings = ["Catalog Numbers merged from collection %s into collection %s"
                    % (collection1, collection2)]
        if merge:
            db_switch_ref = database.cursor()
            db_switch_ref.execute("SELECT TABLE_NAME, COLUMN_NAME FROM "
                                  "INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE "
                                  "CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME IN "
                                  "('CollectionID','CollectionMemberID','UserGroupScopeID') "
                                  "AND TABLE_NAME != 'collection'")
            table_list = db_switch_ref.fetchall()
            switch_references(database, table_list, collection1, collection2)
            print("%s collection objects merged" % len(catalog_numbers[1]))
            if delete:
                delete = delete_collection(database, collection1, integrity_error)
                if delete:
                    return print("Integrity Error occurred when attempting to delete collection "
                                 "%s, see -h for more options" % collection1)
                print("Collection %s deleted from schema" % collection1)
            file_name = "CatalogNumbersMerged[%s]" % (datetime.date.today())
            csv_report(file_name, headings, catalog_numbers[1], show)
            return print("Report saved as %s" % file_name)
        file_name = "CatalogNumbersToBeMerged[%s]" % (datetime.date.today())
        csv_report(file_name, headings, catalog_numbers[1], show)
        print("No collection objects merged, report saved as %s" % file_name)
        print("Report saved as %s" % file_name)
    return None

if __name__ == "__main__":
    main()
