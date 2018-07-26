'''
Module to build trees of data in tables that have a parent/child relationship within the specify mysql schema.
Supports trees that include numbers in names and those that do not (to avoid trivial typos), and trees that include
and author relationship
'''
from anytree import Node, PreOrderIter

# selects ranks within the table schema
def fetch_ranks(db, db_table):
    db_rank_id = db.cursor()
    db_rank_id.execute("SELECT DISTINCT RankID FROM %s ORDER BY RankID ASC" % db_table)
    return db_rank_id.fetchall()

# selects all records with a certain rankID and puts them in a dictionary
def rank_dict(db,db_columns,db_table):
    rank_records_dict = {}
    db_record_info = db.cursor()
    for iD in fetch_ranks(db,db_table):
        db_record_info.execute("SELECT %s FROM %s WHERE RankID = %s" %(db_columns,db_table,iD[0]))
        rank_records_dict[iD[0]] = db_record_info.fetchall()
    return rank_records_dict

# creates new node and new tree key, sets parent to the node that was created before if an author field is not provided
def add_node_without_author(name, gid, pid, previous_parent, tree):
    node = Node((name, gid), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

# creates new node and new tree key, sets parent to the node that was created before if an author field is provided
def add_node_with_author(name, gid, pid, author,previous_parent,tree):
    node = Node((name, gid, author), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

# if an existing key is already in dictionary, appends value, or creates new key/value and adds to dictionary
def add_to_dict(dictionary,key,value):
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key]=[value]
    return dictionary

# builds tree by searching for relationships between existing childID's and new parentID's within the tree without any
# restrictions on numbers in names
def build_tree_with_nums(rank_records_dict,author_toggle):
    tree = {}
    root = Node("root")
    for r in rank_records_dict:
        for record in rank_records_dict[r]:
            if author_toggle:
                if record[0] not in tree:
                    add_node_with_author(record[1], record[2], record[0], record[3], root,tree)
                else:
                    b = tree[record[0]][2]
                    add_node_with_author(record[1], record[2], record[0], record[3], b,tree)
            else:
                if record[0] not in tree:
                    add_node_without_author(record[1], record[2], record[0], root, tree)
                else:
                    b = tree[record[0]][2]
                    add_node_without_author(record[1], record[2], record[0], b, tree)
    return tree

# builds tree by searching for relationships between existing childID's and new parentID's within the tree without
# numbers in names
def build_tree_without_nums(rank_records_dict,author_toggle):
    tree = {}
    root = Node("root")
    for r in rank_records_dict:
        for record in rank_records_dict[r]:
            if (any(str.isdigit(c) for c in record[1])) is False:
                if author_toggle:
                    if record[0] not in tree:
                        add_node_with_author(record[1], record[2], record[0], record[3], root, tree)
                    else:
                        b = tree[record[0]][2]
                        add_node_with_author(record[1], record[2], record[0], record[3], b, tree)
                else:
                    if record[0] not in tree:
                        add_node_without_author(record[1], record[2], record[0], root, tree)
                    else:
                        b = tree[record[0]][2]
                        add_node_without_author(record[1], record[2], record[0], b,tree)
    return tree
