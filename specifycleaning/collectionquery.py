"""
Searches across all collections within the schema by restrictions set from command line arguments.
Using a MySQL statement that joins the required tables and a formatted list of the restrictions,
the CatalogNumber, DAO Accession Number, Collection Name, Collector Last Name, Taxon Full Name,
Geography and Year Collected of records satisfying the restraints are returned. A report is then
created with this data.
"""
import argparse
import datetime
import pymysql
from specifycleaning.csvwriter import write_report

def format_records(query_data):
    # Formats records with multiple collectors, returns the number of distinct catalog numbers
    raw_data = {}
    catalog_nums = []
    for record in query_data:
        if record[0] not in catalog_nums:
            catalog_nums.append(record[0])
        key = (record[0], record[4], record[2])
        if (key in raw_data) and \
                (record[3] not in raw_data[key][3][0]) and \
                (record[2] == raw_data[key][2][0]):
            raw_data[key][3][0] += ", " + str(record[3])
        else:
            raw_data[key] = [[record[0]], [record[1]], [record[2]], [str(record[3])],
                             [record[4]], [record[5]], [record[6]]]
    clean_data = [[y for x in raw_data[value] for y in x] for value in raw_data]
    return clean_data, len(catalog_nums)

def fetch_info(database, restriction_list):
    # Selects required columns from schema using passed in formatted restrictions on data
    db_fetch_records = database.cursor()
    db_fetch_records.execute("SELECT CO.CatalogNumber, CO.AltCatalogNumber, CL.CollectionName, "
                             "A.LastName, T.Fullname, G.FullName, CE.StartDate "
                             "FROM collectionobject CO "
                             "INNER JOIN collection CL ON CL.CollectionID = CO.CollectionID "
                             "INNER JOIN collectingevent CE "
                             "ON CE.CollectingEventID = CO.CollectingEventID "
                             "INNER JOIN collector C "
                             "ON C.CollectingEventID = CE.CollectingEventID "
                             "INNER JOIN determination D "
                             "ON D.CollectionObjectID = CO.CollectionObjectID "
                             "INNER JOIN agent A ON A.AgentID = C.AgentID "
                             "INNER JOIN taxon T ON T.TaxonID = D.TaxonID "
                             "INNER JOIN locality L ON L.LocalityID = CE.LocalityID "
                             "INNER JOIN geography G ON G.GeographyID = L.GeographyID "
                             "WHERE %s" % restriction_list)
    return format_records(db_fetch_records.fetchall())

def format_args(catalognum, dao, lastname, taxon, year, province):
    # Configures data restrictions into a statement that MySQL is able to interpret
    input_list = [("CO.CatalogNumber LIKE '%s' ", catalognum),
                  ("CO.AltCatalogNumber LIKE '%s' ", dao),
                  ("A.LastName LIKE '%s%s%s' ", ('%', lastname, '%')),
                  ("T.FullName LIKE '%s' ", taxon),
                  ("YEAR(CE.StartDate) LIKE '%s' ", year),
                  ("G.FullName LIKE '%s%s%s' ", ('%', province, '%'))]
    statement_list = list((field[0] % field[1] + "AND ") for field in input_list if field[1] != "")
    formatted_list = (("".join(statement_list))[:-4])
    return formatted_list

def save_to_file(data_list, show):
    # Saves the results of the query to a csv file, prints data to screen if specified
    file_name = "QueryReport[%s]" % (datetime.date.today())
    headings = ["Catalog Number", "DAO Accession Number", "Collection", "Collector Last Name(s)",
                "Taxon Name", "Geography", "Date Collected"]
    write_report(file_name, headings, data_list[0])
    if show:
        for row in data_list[0]:
            print(*row, sep=", ")
    print("%s records found | %s distinct catalog numbers" % (len(data_list[0]), data_list[1]))
    print("Report saved as %s.csv" % file_name)

# Creates command line arguments and coordinates function calling
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", action="store", dest="username",
                        help="MySQL username", required=True)
    parser.add_argument("-p", "--password", action="store", dest="password",
                        help="MySQL password", required=True)
    parser.add_argument("-d", "--database", action="store", dest="database",
                        help="Name of MySQL Specify database", required=True)
    parser.add_argument("--report", action="store_true", dest="report", default=True,
                        help="(default) Create a report of query results")
    parser.add_argument("--show", action="store_true", dest="show", help="Display query results")
    parser.add_argument("--catalognumber", action="store", dest="catnum", default="",
                        help="Search collections by CatalogNumber")
    parser.add_argument("--DAOaccessionnumber", action="store", dest="dao", default="",
                        help="Search collections by DAO Accession Number (AltCatalogNumber)")
    parser.add_argument("--lastname", action="store", dest="lastname", default="",
                        help="Search collections by collector last name")
    parser.add_argument("--taxon", action="store", dest="taxon", default="",
                        help="Search collections by taxon full name")
    parser.add_argument("--year", action="store", dest="year", default="",
                        help="Search collections by year collected")
    parser.add_argument("--province", action="store", dest="province", default="",
                        help="Search collections by province/state object was collected in")
    args = parser.parse_args()
    report = args.report
    show = args.show
    catnum = args.catnum
    dao = args.dao
    lastname = args.lastname
    taxon = args.taxon
    year = args.year
    province = args.province
    try:
        database = pymysql.connect("localhost", args.username, args.password, args.database)
    except pymysql.err.OperationalError:
        return print("Error connecting to database")
    if not (catnum or dao or lastname or taxon or year or province):
        return print("Must enter at least one argument, see -h for more options")
    if report:
        format_list = format_args(catnum, dao, lastname, taxon, year, province)
        data_list = fetch_info(database, format_list)
        if data_list:
            return print("No records found")
        return save_to_file(data_list, show)
    return None

if __name__ == "__main__":
    main()
