import os
import pickle

from mime_names import TYPES
from utils import load_settings

class DriveFolder:
    def __init__(self, parent, file_struct):
        self.parent = parent
        self.id = file_struct['id']
        self.name = file_struct['title']
        self.children = []
        self.mime = file_struct['mimeType']
        self.used_quota = file_struct['quotaBytesUsed']
        if parent:
            self.level = parent.get_level() + 1
        else:
            self.level = 0

    def add_child(self, children):
        self.children.append(children)

    def get_children(self):
        return self.children

    def get_id(self):
        return self.id

    def get_level(self):
        return self.level

    def get_mime(self):
        return self.mime

    def get_name(self):
        return self.name

    def get_parent(self):
        return self.parent

    def get_path(self):
        if not self.parent:
            return '/'
        return self.parent.get_path() + self.name + '/'

    def get_used_quota(self, recursive=True):
        if recursive:
            quota = self.used_quota
            for child in self.children:
                quota += self.get_used_quota(child)
            return quota
        return self.used_quota

    def remove_child(self, children):
        self.children.remove(children)

    def set_name(self, name):
        self.name = name

class DriveTree:
    def __init__(self, drive, save_path):
        self.save_path = save_path
        if drive is None:
            return
        self.drive = drive
        print('Requesting root')
        root_file = drive.CreateFile({'id': drive.GetAbout()['rootFolderId']})
        self.root = DriveFolder(None, root_file)
        self.total_storage = drive.GetAbout()['quotaBytesTotal']

    def add_file(self, parent, file_struct):
        if not parent:
            return None

        cnode = DriveFolder(parent, file_struct)
        parent.add_child(cnode)
        return True

    def breadth_find_file(self, node_id):
        if node_id == self.root.get_id():
            return self.root
        return self.breadth_find_file_in_parent(self.root, node_id)

    def breadth_find_file_in_parent(self, parent, node_id):
        q = []
        discovered = []
        q.insert(0, parent)
        while q:
            v = q.pop()
            if v.get_id() == node_id:
                return v
            for child in v.get_children():
                if child not in discovered:
                    discovered.append(child)
                    q.insert(0, child)

    def find_file(self, node_id):
        if node_id == self.root.get_id():
            return self.root
        return self.find_file_in_parent(self.root, node_id, recursive=True)

    def find_file_in_parent(self, parent, node_id, recursive=False):
        for child in parent.get_children():
            if child.get_id() == node_id:
                return child

            if recursive and child.get_children():
                ret = self.find_file_in_parent(child, node_id, True)
                if ret and ret.get_id() == node_id:
                    return ret
        return None

    def get_closest_node_from_path(self, path):
        path_list = [p for p in path.split('/') if p]
        if path_list[0] != 'root':
            path_list.insert(0, 'root')

        current_node = self.root
        depth = 0
        for path in path_list:
            last_depth = depth
            for node in current_node.get_children():
                if path == node.get_name():
                    current_node = node
                    depth += 1
                    break
            if depth == last_depth:
                break
        return current_node, '/'.join(path_list[depth:])

    def get_node_from_path(self, path, exclusive=True):
        '''Creates a path to reach the node adding all the "sibblings" to the tree
        if exclusive is false'''
        closest_node, remaining_path = self.get_closest_node_from_path(path)
        if remaining_path:
            path_list = [p for p in remaining_path.split('/') if p]
            if path_list[0] != 'root':
                path_list.insert(0, 'root')

            next_node = closest_node
            for p in path_list:
                file_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                                      % closest_node.get_id()}).GetList()
                for file1 in file_list:
                    if not exclusive\
                       and not self.find_file_in_parent(closest_node, file1['id']):
                        self.add_file(closest_node, file1)
                    if file1['title'] == p:
                        if exclusive:
                            self.add_file(closest_node, file1)
                        next_node = self.find_file_in_parent(closest_node, file1['id'])
                if next_node == closest_node and p != 'root':
                    return None
                closest_node = next_node

            if not closest_node.get_children():
                children_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                                          % closest_node.get_id()}).GetList()
                for child in children_list:
                    self.add_file(closest_node, child)

        self.save_to_file()
        return closest_node

    def get_path_from_id(self, id):
        file1 = self.drive.CreateFile({'id': id})
        isfolder = ''
        if file1['mimeType'] == TYPES['folder']:
            isfolder = '/'
        if not file1['parents']:
            return '?' + file1['title']
        parent = file1['parents'][0]
        if parent['isRoot']:
            return '/' + file1['title'] + isfolder

        return self.get_path_from_id(parent['id']) + file1['title'] + isfolder

    def get_root(self):
        return self.root

    def load_from_file(self, file_path=None):
        if not file_path:
            file_path = self.save_path

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        return self

    def print_folder(self, folder):
        depth = folder.get_level()
        prefix = depth * ('  |') + '--'
        print(prefix, folder.get_name(), '\tid:', folder.get_id(), sep='')
        for child in folder.get_children():
            self.print_folder(child)

    def print_tree(self):
        self.print_folder(self.root)

    def remove_folder(self, id):
        folder = self.find_file(id)
        if folder:
            folder.get_parent.removeChildren(folder)

    def save_to_file(self, file_path=None):
        if not file_path:
            file_path = self.save_path
        if not os.path.exists(os.path.split(os.path.abspath(file_path))[0]):
            os.makedirs(os.path.split(os.path.abspath(file_path))[0])

        with open(file_path, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
            f.flush()

    # whitelist and blacklist don't need to require all the files,
    # only specific files (is it worth it? don't think so. too complex query)
    def load_complete_tree(self, filter_enabled=True):
        whitelist = blacklist = None
        if filter_enabled:
            settings = load_settings()
            if settings['whitelist-enabled']:
                whitelist = settings['whitelist-files']
            elif settings['blacklist-enabled']:
                blacklist = settings['blacklist-files']

        if os.path.exists('mirror.dat'):
            with open('mirror.dat', 'rb') as f:
                remote_files = pickle.load(f)
        else:
            print('Requesting files')
            # TODO: improve query
            query = 'trashed = false'
            remote_files = self.drive.ListFile({'q': query}).GetList()
            with open('mirror.dat', 'wb') as f:
                pickle.dump(remote_files, f, pickle.HIGHEST_PROTOCOL)

        metadata = [file1 for file1 in remote_files if file1['parents']]

        self.root.children = []
        stack = [] # [metadata]
        nodes = [] # [DriveFile]
        i = 0 # used to pin the node that is looking for a parent
        j = 0 # used to pin the next node that will look for the parent
        def insert_ordered_node(node, nodes):
            lower_bound = 0
            upper_bound = len(nodes) - 1
            # loop to find the position where to insert node
            while upper_bound - lower_bound > 1:
                half = (upper_bound + lower_bound) // 2
                if node.get_id() < nodes[half].get_id():
                    upper_bound = half
                else:
                    lower_bound = half
            # insert the node to nodes list
            if node.get_id() < nodes[lower_bound].get_id():
                nodes.insert(lower_bound, node)
            else:
                if node.get_id() < nodes[upper_bound].get_id():
                    nodes.insert(upper_bound, node)
                else:
                    nodes.insert(upper_bound + 1, node)

        total = len(metadata)
        while metadata or stack:
            current = len(metadata)
            if (current % 200) == 0:
                print('\rGenerating tree: %.2f%%' % (((total - current)/total) * 100), end='')
            enqueue = None
            j = 0
            # find the parent meta to the pinned one
            for data in metadata:
                if metadata[i]['parents'][0]['id'] == data['id']:
                    enqueue = metadata[i]
                    break
                j += 1

            # parent is not an object
            if enqueue:
                stack.append(enqueue)
                metadata.pop(i)
                if j < i:
                    i = j
                else:
                    i = j - 1
            # parent node is root
            elif metadata[i]['parents'][0]['id'] == self.root.get_id():
                title = ('/' + metadata[i]['title'] + '/')
                if not filter_enabled\
                   or (whitelist and title in whitelist)\
                   or (blacklist and title not in blacklist):
                    child = DriveFolder(self.root, metadata[i])
                    self.root.add_child(child)
                    # check if nodes is empty, to avoid 'out of bounds'
                    if not nodes:
                        nodes.append(child)
                    else:
                        insert_ordered_node(child, nodes)
                    while stack:
                        item = stack.pop()
                        title = title + '/' + item['title'] + '/'
                        if blacklist and title in blacklist:
                            stack = []
                            break
                        parent = child
                        child = DriveFolder(parent, item)
                        parent.add_child(child)
                        insert_ordered_node(child, nodes)
                metadata.pop(i)
                i = 0
            # parent object exists
            else:
                parent_id = metadata[i]['parents'][0]['id']
                lower_bound = 0
                upper_bound = len(nodes) - 1
                half = 0

                # set the position of the value to any of the bounds
                while upper_bound >= lower_bound:
                    half = (lower_bound + upper_bound) // 2
                    if nodes[half].get_id() == parent_id:
                        break
                    elif parent_id < nodes[half].get_id():
                        upper_bound = half - 1
                    else:
                        lower_bound = half + 1
                    half = (lower_bound + upper_bound) // 2

                if not nodes:
                    stack = []
                    metadata.pop(i)
                    i = 0
                    continue
                elif filter_enabled:
                    title = nodes[half].get_path() + metadata[i]['title'] + '/'
                    if (blacklist and (title in blacklist))\
                       or (whitelist and not any(elem in title for elem in whitelist)):
                        stack = []
                        metadata.pop(i)
                        i = 0
                        continue

                if nodes[half].get_id() != parent_id:
                    metadata.pop(i)
                    stack = []
                    i = 0
                    continue

                child = DriveFolder(nodes[half], metadata[i])
                nodes[half].add_child(child)
                insert_ordered_node(child, nodes)
                while stack:
                    parent = child
                    item = stack.pop()
                    child = DriveFolder(parent, item)
                    insert_ordered_node(child, nodes)
                    parent.add_child(child)
                metadata.pop(i)
                i = 0
        print('\rGenerating tree: 100%      ')
