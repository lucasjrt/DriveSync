import os
import pickle

from queue import Queue
from threading import Thread, Lock

from defines import TREE_CACHE
from mime_names import TYPES
from utils import load_settings

rps = 0 # requests per second (not actually, just limiting threads)

class DriveFolder:
    def __init__(self, parent, id, name, mime):
        self.parent = parent
        self.id = id
        self.name = name
        self.children = []
        self.mime = mime
        if parent:
            self.level = parent.get_level() + 1
        else:
            self.level = 0

    def get_parent(self):
        return self.parent

    def get_id(self):
        return self.id

    def get_mime(self):
        return self.mime

    def get_name(self):
        return self.name

    def get_children(self):
        return self.children

    def add_children(self, children):
        self.children.append(children)

    def remove_children(self, children):
        self.children.remove(children)

    def get_level(self):
        return self.level

    def set_name(self, name):
        self.name = name

    def get_path(self):
        if not self.parent:
            return '/'
        return self.parent.get_path() + self.name + '/'

class DriveTree:
    def __init__(self, id, drive):
        self.root = DriveFolder(None, id, 'My drive', TYPES['folder'])
        self.drive = drive

    def get_root(self):
        return self.root

    def get_path_from_id(self, id):
        file1 = self.drive.CreateFile({'id': id})
        parent = file1['parents'][0]
        if parent['isRoot']:
            return '/' + file1['title'] + '/'
        return self.get_path_from_id(parent['id']) + file1['title'] + '/'

    def breadth_find_file_in_parent(self, parent, node_id):
        q = Queue()
        discovered = []
        q.put(parent)
        while not q.empty():
            v = q.get()
            if v.get_id() == node_id:
                return v
            for child in v.get_children():
                if child not in discovered:
                    discovered.append(child)
                    q.put(child)

    def find_file_in_parent(self, parent, node_id, recursive=False):
        for child in parent.get_children():
            if child.get_id() == node_id:
                return child

            if recursive and child.get_children():
                ret = self.find_file_in_parent(child, node_id, True)
                if ret and ret.get_id() == node_id:
                    return ret
        return None

    def breadth_find_file(self, node_id):
        if node_id == self.root.get_id():
            return self.root
        return self.breadth_find_file_in_parent(self.root, node_id)

    def find_file(self, node_id):
        if node_id == self.root.get_id():
            return self.root
        return self.find_file_in_parent(self.root, node_id, recursive=True)

    def add_file(self, parent, id, name, mime):
        if not parent:
            return None

        # pnode = self.findFile(parent.get_id())

        # if self.findFileInParent(pnode, id):
        # if self.findFileInParent(parent, id):
        #     return None

        cnode = DriveFolder(parent, id, name, mime)
        # pnode.add_children(cnode)
        parent.add_children(cnode)
        return True

    def remove_folder(self, id):
        folder = self.find_file(id)
        if folder:
            folder.get_parent.removeChildren(folder)

    def load_from_file(self):
        if os.path.exists(TREE_CACHE) and os.path.isfile(TREE_CACHE):
            with open(TREE_CACHE, 'rb') as f:
                return pickle.load(f)
        return self

    def save_to_file(self):
        if not os.path.exists(os.path.split(os.path.abspath(TREE_CACHE))[0]):
            os.makedirs(os.path.split(os.path.abspath(TREE_CACHE))[0])

        with open(TREE_CACHE, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
            f.flush()

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

    def get_exclusive_node_from_path(self, path):
        '''just create the necessary path for reaching the node'''
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
                    if file1['title'] == p:
                        self.add_file(closest_node, file1['id'], file1['title'], file1['mimeType'])
                        next_node = self.find_file_in_parent(closest_node, file1['id'])
                if next_node == closest_node and p != 'root':
                    return None
                closest_node = next_node

            if not closest_node.get_children():
                children_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                                          % closest_node.get_id()}).GetList()
                for child in children_list:
                    self.add_file(closest_node, child['id'], child['title'], child['mimeType'])

        self.save_to_file()
        return closest_node

    def get_node_from_path(self, path):
        '''creates a broad path to reach the node'''
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
                    if not self.find_file_in_parent(closest_node, file1['id']):
                        self.add_file(closest_node, file1['id'], file1['title'], file1['mimeType'])
                    if file1['title'] == p:
                        next_node = self.find_file_in_parent(closest_node, file1['id'])
                if next_node == closest_node and p != 'root':
                    return None
                closest_node = next_node

            if not closest_node.get_children():
                children_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                                          % closest_node.get_id()}).GetList()
                for child in children_list:
                    self.add_file(closest_node, child['id'], child['title'], child['mimeType'])

        self.save_to_file()
        return closest_node

    def print_folder(self, folder):
        depth = folder.get_level()
        prefix = depth * ('  |') + '--'
        print(prefix, folder.get_name(), '\tid:', folder.get_id(), sep='')
        for child in folder.get_children():
            self.print_folder(child)

    def print_tree(self):
        self.print_folder(self.root)

    def test_sync_cache(self):
        if os.path.exists('mirror.dat'):
            with open('mirror.dat', 'rb') as f:
                print('loading')
                metadata = pickle.load(f)
        else:
            print('requesting files')
            query = "trashed = false"
            remote_files = self.drive.ListFile({'q': query}).GetList()
            metadata = [file1 for file1 in remote_files if file1['parents']]
            with open('mirror.dat', 'wb') as f:
                pickle.dump(metadata, f, pickle.HIGHEST_PROTOCOL)
        self.root.children = []
        stack = [] # [return]
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

        while metadata or stack:
            if (len(metadata) % 100) == 0:
                print(len(metadata))
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
                child = DriveFolder(self.root,
                                    metadata[i]['id'],
                                    metadata[i]['title'],
                                    metadata[i]['mimeType'])
                self.root.add_children(child)
                # check if nodes is empty, to avoid 'out of bounds'
                if not nodes:
                    nodes.append(child)
                else:
                    insert_ordered_node(child, nodes)
                while stack:
                    parent = child
                    item = stack.pop()
                    child = DriveFolder(parent, item['id'], item['title'], item['mimeType'])
                    parent.add_children(child)
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
                if nodes[half].get_id() != parent_id:
                    metadata.pop(i)
                    stack = []
                    i = 0
                    continue
                child = DriveFolder(nodes[half],
                                    metadata[i]['id'],
                                    metadata[i]['title'],
                                    metadata[i]['mimeType'])
                nodes[half].add_children(child)
                insert_ordered_node(child, nodes)
                while stack:
                    parent = child
                    item = stack.pop()
                    child = DriveFolder(parent, item['id'], item['title'], item['mimeType'])
                    insert_ordered_node(child, nodes)
                    parent.add_children(child)
                metadata.pop(i)
                i = 0
        self.print_tree()

    def sync_cache(self):
        mutex = Lock()
        requestmutex = Lock()
        print("syncing cache")
        # for each node check if it exists on drive, and if so
        # check if there's any new child
        files = self.drive.ListFile({'q': "'root' in parents and trashed = false"
                                    }).GetList()
        file_names = [file1['title'] for file1 in files]
        children = self.root.get_children()
        children_names = [node.get_name() for node in self.root.get_children()]

        # verify if is blacklist or whitelist enabled
        # if so, load only one of them
        settings = load_settings()
        if settings is None:
            print('Failed to load settings file, read the log file for more info')
            return
        if settings['whitelist-enabled']:
            blacklist = None
            whitelist = settings['whitelist-files']
        elif settings['blacklist-enabled']:
            blacklist = settings['blacklist-files']
            whitelist = None

        #first remove
        for child in children:
            if (child.get_name() not in file_names)\
            or (blacklist and (child.get_path() in blacklist))\
            or (whitelist and (child.get_path() not in whitelist)):
                print('removing', child.get_name())
                self.root.remove_children(child)

        #then add (if in whitelist or not in blacklist or none are enabled)
        if not whitelist:
            print('whitelist disabled')
            for file1 in files:
                file1_path = self.get_path_from_id(file1['id'])
                if file1['title'] not in children_names:
                    if (whitelist and (file1_path not in whitelist))\
                    or (blacklist and (file1_path in blacklist)):
                        print(file1_path, 'not in', whitelist)
                        continue
                    self.add_file(self.root, file1['id'], file1['title'], file1['mimeType'])

            # repeat for children recursively
            for child in children:
                if settings['whitelist-enabled'] and child.get_path() not in whitelist\
                or settings['blacklist-enabled'] and child.get_path() in blacklist:
                    t = Thread(target=self._sync_cache_children,
                               args=(child, mutex, requestmutex, whitelist, blacklist))
                    t.start()
        else:
            print('whitelist enabled')
            for path in whitelist:
                print('calling recursively', path)
                print('saving the following tree:')
                self.print_tree()
                t = Thread(target=self._sync_cache_children,
                           args=(self.get_exclusive_node_from_path(path), mutex,
                                 requestmutex, whitelist, blacklist, True))
                t.start()
                # self._sync_cache_children(self.get_exclusive_node_from_path(path), mutex,
                #                           requestmutex, whitelist, blacklist, True)

        self.save_to_file()

    # TODO: improve threading to sync faster
    # for now it can get request refused for too many request at once
    # and then it starts making about one request at a time
    # TODO: request all the files metadata and work locally with it
    # instead of making requisitions all the time
    # (whitelist and blacklist don't need to require all the files,
    # only specific files, but all in one querry)
    def _sync_cache_children(self, node, mutex, rqmutex, whitelist=None, blacklist=None,\
                             recursion=False):
        global rps
        print("at node", node.get_name())
        mutex.acquire()
        if rps >= 4:
            mutex.release()
            rqmutex.acquire()
            files = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                              % node.get_id()}).GetList()
            rqmutex.release()
        else:
            rps += 1
            mutex.release()
            files = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                              % node.get_id()}).GetList()
            mutex.acquire()
            rps -= 1
            mutex.release()

        file_names = [file1['title'] for file1 in files]
        children = node.get_children()
        children_names = [child_node.get_name() for child_node in node.get_children()]

        mutex.acquire()
        print('taking decision')
        # first remove
        print('files:', file_names)
        for child in children:
            if child.get_name() not in file_names:
                print('removing', child.get_name())
                node.remove_children(child)
                continue
            if not recursion\
            and ((blacklist and child.get_path() in blacklist)\
            or (whitelist and child.get_path() not in whitelist)):
                print('removing', child.get_name())
                node.remove_children(child)

        # then add
        for file1 in files:
            if recursion or (blacklist and file_path not in blacklist):
                if file1['title'] not in children_names:
                    file_path = self.get_path_from_id(file1['id'])
                    print('adding', file1['title'])
                    self.add_file(node, file1['id'], file1['title'], file1['mimeType'])
        # else: #if whitelist
        #     for path in whitelist:
        #         print('adding', path)
        #         node = self.get_node_from_path(path)

        self.save_to_file()
        mutex.release()
        #repeat for children recursively
        if recursion:
            print('recursion here')
            for child in children:
                print('child:', child.get_name())
                if child.get_mime() == TYPES['folder']:
                    print('is a folder')
                    print('calling recursively for', child.get_name())
                    if (blacklist and child.get_path() in blacklist):
                        continue
                    t = Thread(target=self._sync_cache_children,
                               args=(child, mutex, rqmutex, whitelist, blacklist, True))
                    t.start()
# lower_bound = 0
                    # upper_bound = len(nodes) - 1
                    # # loop to find the position where to insert node
                    # while upper_bound - lower_bound > 1:
                    #     half = (upper_bound + lower_bound) // 2
                    #     if child.get_id() < nodes[half].get_id():
                    #         upper_bound = half
                    #     else:
                    #         lower_bound = half
                    # # insert the node to nodes list
                    # if child.get_id() < nodes[lower_bound].get_id():
                    #     nodes.insert(lower_bound, child)
                    # else:
                    #     if child.get_id() < nodes[upper_bound].get_id():
                    #         nodes.insert(upper_bound, child)
                    #     else:
                    #         nodes.insert(upper_bound + 1, child)
