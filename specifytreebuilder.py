""" Builds trees for data in tables that have a parent/child relationship within the specify
MySQL schema. Supports tree building for data that includes/ does not include numbers (to avoid
trivial typos), and data that does/does not include an author relationship."""
from anytree import Node

def fetch_ranks(database, db_table):
    # Returns RankID's from the specified table
    db_rank_id = database.cursor()
    db_rank_id.execute("SELECT DISTINCT RankID FROM %s ORDER BY RankID ASC" % db_table)
    return db_rank_id.fetchall()

def rank_dict(database, db_columns, db_table, db_ranks):
    # Returns a dictionary of RankID's and the records within the ranks from the specified table
    rank_records_dict = {}
    db_record_info = database.cursor()
    for rank in db_ranks:
        db_record_info.execute("SELECT %s FROM %s WHERE RankID = '%s'"
                               % (db_columns, db_table, rank[0]))
        rank_records_dict[rank[0]] = db_record_info.fetchall()
    return rank_records_dict

def add_node_without_author(name, gid, pid, previous_parent, tree):
    # Creates new node and new tree key without an author relationship
    node = Node((name, gid), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

def add_node_with_author(name, gid, pid, author, previous_parent, tree):
    # Creates new node and new tree key with an author relationship
    node = Node((name, gid, author), parent=previous_parent)
    tree[gid] = (name, pid, node)
    return node

def add_to_dict(dictionary, key, value):
    # Searches dictionary for existing key and appends new value, or creates new key/value pair
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]
    return dictionary

def check_author(dictionary, name, author, tid):
    # Feeds parameters chosen according to what the author structure is into dictionary function
    if author is None:
        return add_to_dict(dictionary, (name, author), (tid, author))
    if (author[0] != '(') and (author[0] != '['):
        return add_to_dict(dictionary, (name, author[0]), (tid, author))
    return add_to_dict(dictionary, (name, author[1]), (tid, author))

def build_tree_without_nums(rank_records_dict, author_toggle):
    # Builds tree with restrictions on names by searching for relationships between existing
    # ChildID's and new ParentID's
    tree = {}
    root = Node("root")
    for row in rank_records_dict:
        for record in rank_records_dict[row]:
            if (any(str.isdigit(c) for c in record[1])) is False:
                if author_toggle:
                    if record[0] not in tree:
                        add_node_with_author(record[1], record[2], record[0],
                                             record[3], root, tree)
                    else:
                        before = tree[record[0]][2]
                        add_node_with_author(record[1], record[2], record[0],
                                             record[3], before, tree)
                else:
                    if record[0] not in tree:
                        add_node_without_author(record[1], record[2], record[0], root, tree)
                    else:
                        before = tree[record[0]][2]
                        add_node_without_author(record[1], record[2], record[0], before, tree)
    return tree

def build_tree_with_nums(rank_records_dict, author_toggle):
    # Builds tree without restrictions on names by searching for relationships between existing
    # ChildID's and new parentID's
    tree = {}
    root = Node("root")
    for row in rank_records_dict:
        for record in rank_records_dict[row]:
            if author_toggle:
                if record[0] not in tree:
                    add_node_with_author(record[1], record[2], record[0],
                                         record[3], root, tree)
                else:
                    before = tree[record[0]][2]
                    add_node_with_author(record[1], record[2], record[0],
                                         record[3], before, tree)
            else:
                if record[0] not in tree:
                    add_node_without_author(record[1], record[2], record[0], root, tree)
                else:
                    before = tree[record[0]][2]
                    add_node_without_author(record[1], record[2], record[0], before, tree)
    return tree
