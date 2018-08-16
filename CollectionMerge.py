"""
Merges two collections together by checking for any catalog number conflicts, then changing all references of the
collection being merged (collection1) to the collection being merged to (collection2). If there are catalog number
conflicts, creates a report of the conflicting catalog numbers with time stamp in file name. If there are no conflicts,
then preforms the collection switches. Defaults to just saving a file of the catalognumbers that will be merged unless
prompted to merge with the --merge command, and then deletes the (now empty) collection with the --delete command.
"""
import pymysql, argparse, datetime
from csvwriter import write_report

# selects catalognumbers belonging to passed in collection, returns list of formatted catalognumbers
def fetch_catalog_numbers(db, collectionid):
    db_catalog_numbers = db.cursor()
    db_catalog_numbers.execute("SELECT CatalogNumber FROM collectionobject WHERE CollectionID = '%s'" % collectionid)

    cat_list = [[catalog_number[0]] for catalog_number in db_catalog_numbers.fetchall()]
    return cat_list

# checks for conflicting catalog numbers between the two collections, returns formatted list catalog numbers if any
def check_conflicts(db, collection1, collection2):
    cat_numbers1 = fetch_catalog_numbers(db, collection1)
    cat_numbers2 = fetch_catalog_numbers(db, collection2)
    return [cn for cn in cat_numbers1 if cn in cat_numbers2]

# switches any references of collection1 to collection2 except for references in the table 'collection'
def switch_references(db,table_list,c1,c2):
    db_update = db.cursor()
    for table in table_list:
        db_update.execute("UPDATE %s SET %s = '%s' WHERE %s = '%s' " % (table[0], table[1], c2, table[1], c1))
        db.commit()

# removes the (now empty) collection1 from the schema using its collectionID
def delete_collection(db,collectionid):
    db_delete = db.cursor()
    db_delete.execute("DELETE FROM collection WHERE collectionID = '%s'" % collectionid)
    db.commit()

# writes report with timestamp in file name and shows data if the command is passed in
def csv_report(file_name,headings,result_data,show):
    write_report(file_name, headings, result_data)
    if show:
        for row in result_data:
            print(row[0])

# creates command line arguments and coordinates functions
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username", help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password", help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database", help="Name of MySQL Specify database",
                        required=True)
    parser.add_argument("-collection1", action="store",dest="cid1",
                        help ="CollectionID of collection that will be merged (will be removed)", required=True)
    parser.add_argument("-collection2",action="store", dest="cid2",
                        help="CollectionID of collection that will have collection objects added", required=True)
    parser.add_argument("--report", action="store_true", dest="report", default=True,
                        help="(default) Create a report of what Catalog Numbers will be merged")
    parser.add_argument("--show", action="store_true", dest="show", help="Display Catalog Numbers that will be merged")
    parser.add_argument("--merge",action="store_true",dest="merge",help="Merge collection1 into collection2")
    parser.add_argument("--delete", action="store_true",dest="delete", help="Delete (empty) collection1 after merge")
    args = parser.parse_args()
    username = args.username
    password = args.password
    database = args.database
    collection1 = args.cid1
    collection2 = args.cid2
    report = args.report
    show = args.show
    merge = args.merge
    delete = args.delete
    try:
        db = pymysql.connect("localhost", username, password, database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database")
    if report:
        conflicts = check_conflicts(db,collection1,collection2)
        if len(conflicts) >1:
            file_name = ("CatalogNumberConflicts[%s]" % (datetime.date.today()))
            headings = ["Catalog Number Conflicts"]
            csv_report(file_name,headings,conflicts,show)
            print("No collection objects merged")
            return print("%s conflicts found, saved in file %s.csv" % (len(conflicts),file_name))
        file_name = "CatalogNumbersMerged[%s]" % (datetime.date.today())
        headings = ["Catalog Numbers Merged from collectionID %s into collectionID %s" % (collection1, collection2)]
        csv_report(file_name, headings, cat_numbers1, show)
        if merge:
            db_switch_ref = db.cursor()
            db_switch_ref.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE "
                                  "CONSTRAINT_SCHEMA = 'specify' AND REFERENCED_COLUMN_NAME IN "
                                  "('CollectionID','CollectionMemberID','UserGroupScopeID') AND TABLE_NAME != 'collection' ")
            table_list = db_switch_ref.fetchall()
            switch_references(db,table_list,collection1,collection2)
            print("%s collection objects merged" % len(cat_numbers1))
            if delete:
                delete_collection(db,collection1)
                print("CollectionID %s deleted from schema" % collection1)
            return print("Report saved as %s" % file_name)
        print("No collection objects merged, report saved as %s" % file_name)
        return print("See -h for more options")

if __name__ == "__main__":
    main()