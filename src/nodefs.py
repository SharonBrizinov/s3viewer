import re
from datetime import datetime

from utils import decode_data
from consts import DIRLIST_REGEX


def parse_dirlist_line(line):
    parsed_line = DIRLIST_REGEX.findall(line)
    if parsed_line:
        date_modified, size, full_path = parsed_line[0]
        new_node = FSNode(full_path, date_modified, size)
        return new_node
    else:
        raise Exception("Bad dirlist data. Could not parse line: '{}'".format(line))

def parse_dirlist(dirlist_path):
    # Dirlist:
    #   2016-11-14 16:14:09          0 DirName/
    #   2016-11-14 16:14:10         10 DirName/File.txt
    stats = FSNodeStats()
    root_node = FSNode("", None, 0)
    # Read dirlist
    with open(dirlist_path, "rb") as f:
        dirlist_data_raw = f.read()
    dirlist_data = decode_data(dirlist_data_raw)
    if not dirlist_data:
        raise Exception("Could not decode dirlist. Are you sure your data is valid?")
    # Parse
    lines = dirlist_data.splitlines()
    for i, line in enumerate(lines):
        new_node = parse_dirlist_line(line)
        root_node.process_sub_node(new_node)
        stats.process_node(new_node)
    return root_node, stats

def print_all_nodes(node, level=0):
    print("{}{}".format(level*"\t", node.basename))
    for child_node in node.children.values():
        print_all_nodes(child_node, level+1)


class FSNodeStats:
    def __init__(self):
        self.count_total = 0
        self.count_files = 0
        self.count_dirs = 0
        self.date_oldest = None
        self.date_newest = None
        self.total_size = 0

    def process_node(self, node):
        # Init
        if not self.date_oldest:
            self.date_oldest = node.date_modified
        if not self.date_newest:
            self.date_newest = node.date_modified

        if node.is_file:
            self.count_files += 1
            self.total_size += node.size
        else:
            self.count_dirs += 1

        if node.date_modified:
            if node.date_modified > self.date_newest:
                self.date_newest = node.date_modified

        if node.date_modified:
            if node.date_modified < self.date_oldest:
                self.date_oldest = node.date_modified

        self.count_total += 1

    def get_human_readable_size(self, suffix='B'):
        num = self.total_size
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)


class FSNode:
    def __init__(self, full_path, date_modified, size):
        self.full_path = "/" + full_path
        self.date_modified = self.get_format_date(date_modified)
        self.size = int(size)
        self.path_list = self.get_path_list()
        self.basename = self.path_list[-1]
        self.children = {} # {'name': FSNode}
        self.parent = None
        self.is_directory = self.get_is_directory()
        self.is_file = not self.is_directory
        self.is_downloaded = False
        self.download_path = None
        self.item_view = None # GUI Representation

    def __repr__(self):
        if self.is_file:
            return "Name: {}, Size: {}, Created: {}  ".format(self.basename, self.get_human_readable_size(), self.date_modified or "?")
        else:
            return "Name: {}, Created: {}, No. Children: {}  ".format(self.basename, self.date_modified  or "?", len(self.children))

    def get_path_list(self):
        # Edge case for root node ("/")
        if self.full_path == "/":
            return ["/"]
        path_list = self.full_path.split("/")
        # Edge case for dir node ("/DirName/")
        if path_list[-1] == '':
            return path_list[1:-1]
        # /Dirname/FileName.txt
        return path_list[1:]

    def get_date_modified(self):
        if self.date_modified:
            return str(self.date_modified)
        return ""

    def get_human_readable_size(self, suffix='B'):
        if self.is_directory:
            return ""
        num = self.size
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def get_format_date(self, date):
        # 2017-12-11 11:56:04
        if date:
            return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        else:
            return None

    def get_is_directory(self):
        return self.size == 0 and self.full_path.endswith("/") or\
            self.size == 4096 and "." not in self.basename # this is some kind of heuristic check for linux based systems

    # Check if node exists yet
    def is_node_exists_yet(self, node):
        current_node = self
        path_list = node.path_list
        for i, path_element in enumerate(path_list):
            if path_element in current_node.children:
                current_node = current_node.children[path_element]
        return current_node.full_path == node.full_path

    def process_sub_node(self, new_node):
        new_nodes = []
        current_node = self
        path_list = new_node.path_list
        for i, path_element in enumerate(path_list):
            if path_element in current_node.children:
                current_node = current_node.children[path_element]
            else:
                if i < len(path_list)-1:
                    # We reached a new node that doesn't exist yet. We need to create it
                    #   this happens when we encounter full path of a file without seeing the directories before
                    sub_node_full_path = "/".join(path_list[:i+1])+"/" # to be compatible with all dirs which end with /
                    sub_node = FSNode(sub_node_full_path, None, 0)
                    current_node.add_child(sub_node)
                    current_node = sub_node
                    # Keep track of new nodes
                    new_nodes.append(sub_node)
                else:
                    # Must be the last part
                    current_node.add_child(new_node, special_name=path_element)
        return new_nodes

    def get_how_many_childern_are_files(self):
        count_files = 0
        for node in self.children.values():
            if node.is_file:
                count_files += 1
        return count_files

    def add_child(self, new_child, special_name=None):
        if special_name:
           self.children[special_name] = new_child
        else:
            self.children[new_child.basename] = new_child
        new_child.parent = self

    # should be called from root node
    def get_sub_node(self, full_path):
        if not full_path:
            return None
        current_node = self
        path_list = full_path.split("/")
        for i, path_element in enumerate(path_list):
            if path_element in current_node.children:
                current_node = current_node.children[path_element]
            else:
                raise Exception("Could not find '{}'".format(full_path))
        return current_node