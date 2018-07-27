"""
Redmine Support #12463
Creates a csv report of possible duplicate full taxon names that are in the same genus and have the same author first
letter. Creates a tree of taxon parent-children relationships by ranks and parentID's using the library  'anytree' and
'specifytreebuilder', then iterates through each genus subtree and creates a dictionary with keys as the genus name and
the author first letter, and the values as the taxonID and full author name. Then searches through dictionary and adds
key/value pairs with more than one value to the report as possible duplicates. Supports command line arguments
"""
import pymysql as MySQLdb
from anytree import PreOrderIter
import itertools
from csvwriter import write_report
from specifytreebuilder import add_to_dict, rank_dict, build_tree_with_nums
import argparse

# calls on function to add to dictionary with parameters chosen according to what the author is for each record
def check_genus_dict(genus_dict, name, author, tid):
    return (add_to_dict(genus_dict, (name,author), (tid,author)) if author is None else
           (add_to_dict(genus_dict, (name,author[0]), (tid,author)) if (author[0] != '(') and (author != '[')
            else add_to_dict(genus_dict,(name,author[1]), (tid,author))))

# searches by genus for matching full names and coordinates checks for author, adds to report list when match is found
def search_tree(rank_records_dict,tree):
    result_data = []
    genus_names = rank_records_dict[180]
    for genus in genus_names:
        genus_dict = {}
        for name in [node.name for node in PreOrderIter(tree[genus[2]][2])]:
            if (name[2] is None) or (name[2] == ""):
                genus_dict = check_genus_dict(genus_dict,name[0],None,name[1])
            else:
                genus_dict = check_genus_dict(genus_dict,name[0],name[2],name[1])
        result_data+=[(genus[1],key[0],str([i[1] for i in genus_dict[key]]), str([j[0] for j in genus_dict[key]])) for
                     key in genus_dict if len(genus_dict[key]) > 1]
    return result_data

# calls on functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    print("Searching for duplicate taxon full names in the same genus ")

    # creating a dictionary of records relating to their rank
    rank_dictionary = rank_dict(db,"ParentID, FullName, TaxonID, Author","taxon")

    # building a taxon tree by searching relationships between existing taxonID's and new parentID's within the tree
    tree = build_tree_with_nums(rank_dictionary,True)

    # creates a list of data that is flagged as being a duplicate
    result_data = search_tree(rank_dictionary,tree)
    heading = ["Genus Name", "Duplicate Taxon Full Name", "Authors", "Taxon IDs"]
    file_name = "GenusDuplicateReportTEST"

    # writes the duplicate data passed in to a csv file
    write_report(file_name,heading,result_data)
    print("Report saved as %s.csv"%file_name)

if __name__ == "__main__":
    main()