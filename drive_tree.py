import os
import pickle

from mime_names import TYPES
from utils import load_settings

from drive_file import DriveFile

class DriveTree:
    def __init__(self, service, save_path, root):
        self.save_path = save_path
        if service is None:
            print('service is none')
            return
        self.root = DriveFile(None, root)
        self.service = service
        self.folders_hash = {}
        self.files_hash = {}

    def download(self, destination):
        '''Download all the files from the tree'''
        if not os.path.exists(destination):
            os.mkdir(destination)
        nodes = self.get_root().get_children()
        while nodes:
            node = nodes[0]
            nodes = nodes + node.get_children()
            path = destination + node.get_parent().get_path()
            node.download(path, self.service, recursive=False)
            print(nodes.pop(0).get_name(), 'downloaded')

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
        if not path_list or path_list[0] != 'root':
            path_list.insert(0, 'root')

        current_node = self.root
        depth = 0
        for path1 in path_list:
            last_depth = depth
            for node in current_node.get_children():
                if path1 == node.get_name():
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
                file_list = self.service.files().list(q="'%s' in parents and trashed = false"
                                                      % closest_node.get_id(),
                                                      fields='files(name, id, mimeType, parents)')\
                                                      .execute().get('files', [])
                for file1 in file_list:
                    if (file1['name'] == p or not exclusive) \
                    and not self.find_file_in_parent(closest_node, file1['id']):
                        DriveFile(closest_node, file1)
                    if file1['name'] == p:
                        next_node = self.find_file_in_parent(closest_node, file1['id'])
                if next_node == closest_node and p != 'root':
                    return None
                closest_node = next_node
        self.save_to_file()
        return closest_node

    def get_path_from_id(self, fileId):
        file1 = self.service.files().get(fileId=fileId,
                                         fields='file(mimeType, parents)').execute()
        isfolder = ''
        if file1['mimeType'] == TYPES['folder']:
            isfolder = '/'
        if not file1['parents']:
            return '?' + file1['name']
        parent = file1['parents'][0]
        if parent == self.root.get_id():
            return '/' + file1['name'] + isfolder

        return self.get_path_from_id(parent['id']) + file1['name'] + isfolder

    def get_root(self):
        return self.root

    def load_complete_tree(self, filter_enabled=True, complete=True):
        '''Creates a folder hash table and another non-folder hash table
        stores nodes in the first hash and the id is the key (e.g. /MyDrive/Books/Fiction)
        the second one simply stores the file struct and the id is the
        key (e.g. Star Wars.pdf).

        :param filter_enabled: if whitelist or blacklist is enabled.
        :type filter_enabled: bool.
        :param complete: If will link files to tree.
        :type complete: bool.
        '''
        whitelist = blacklist = None
        if filter_enabled:
            settings = load_settings()
            if settings['whitelist-enabled']:
                whitelist = settings['whitelist-files']
            elif settings['blacklist-enabled']:
                blacklist = settings['blacklist-files']

        # =========== debug code ===========
        # just to keep local query to not request files every run
        if not os.path.exists('mirror.dat'):
            print('Requesting files')
            query = 'trashed = false'
            files_metadata = []
            pageToken = None
            while True:
                result = self.service.files().list(q=query,\
                                                fields='nextPageToken, \
                                                    files(id, name, mimeType, parents)',\
                                                pageToken=pageToken,\
                                                pageSize=1000).execute()
                files_metadata = files_metadata + result.get('files', [])
                pageToken = result.get('nextPageToken')
                if not pageToken:
                    break
            with open('mirror.dat', 'wb') as f:
                pickle.dump(files_metadata, f, pickle.HIGHEST_PROTOCOL)
        else:
            with open('mirror.dat', 'rb') as f:
                files_metadata = pickle.load(f)
        # =========== debug code ===========

        # =========== real code ===========
        # print('Requesting files')
        # #TODO: improve query
        # query = 'trashed = false'
        # files_metadata = []
        # pageToken = None
        # while True:
        #     result = self.service.files().list(q=query,\
        #                                        pageToken=pageToken,\
        #                                        pageSize=1000).execute()
        #     files_metadata = files_metadata + result.get('files', [])
        #     pageToken = result.get('nextPageToken')
        #     if not pageToken:
        #         break
        # =========== real code ===========

        # just the folders vector, will be converted to hash bellow
        folders = [f for f in files_metadata\
                   if f['mimeType'] == TYPES['folder']\
                   and 'parents' in f]
        self.files_hash = {f['id']: f for f in files_metadata\
                                     if f['mimeType'] != TYPES['folder']\
                                     and 'parents' in f}
        self.root.children = [] # empty tree
        stack = [] # [metadata]
        self.folders_hash = {}
        total = len(folders)
        i = 0 # used to pin the node that is looking for a parent
        j = 0 # used to pin the next node that will look for the parent
        while folders or stack:
            current = len(folders)
            if (current % 200) == 0:
                print('\rGenerating tree: %.2f%%' % (((total - current)/total) * 100), end='')
            enqueue = None
            j = 0
            for folder in folders:
                if folders[i]['parents'][0] == folder['id']:
                    enqueue = folders[i]
                    break
                j += 1

            if enqueue:
                stack.append(enqueue)
                folders.pop(i)
                if j < i:
                    i = j
                else:
                    i = j - 1
            elif folders[i]['parents'][0] == self.root.get_id():
                title = ('/' + folders[i]['name'] + '/')
                if (blacklist and title in blacklist)\
                or (whitelist and not any(title in elem for elem in whitelist)):
                    stack = []
                    folders.pop(i)
                    i = 0
                    continue
                child = DriveFile(self.root, folders[i])
                self.folders_hash[folders[i]['id']] = child

                while stack:
                    item = stack.pop()
                    title = title + '/' + item['name'] + '/'
                    if (blacklist and (title in blacklist)) \
                    or (whitelist and not \
                    any(elem in title for elem in whitelist)):
                        stack = []
                        break
                    parent = child
                    child = DriveFile(parent, item)
                    self.folders_hash[item['id']] = child
                folders.pop(i)
                i = 0
            else:
                parent_id = folders[i]['parents'][0]
                if not parent_id in self.folders_hash:
                    stack = []
                    folders.pop(i)
                    i = 0
                    continue
                elif filter_enabled:
                    title = self.folders_hash[parent_id].get_path() + folders[i]['name'] + '/'
                    if (blacklist and (title in blacklist))\
                    or (whitelist and not\
                    any(elem in title for elem in whitelist)):
                        stack = []
                        folders.pop(i)
                        i = 0
                        continue

                child = DriveFile(self.folders_hash[parent_id], folders[i])
                self.folders_hash[child.get_id()] = child
                while stack:
                    parent = child
                    item = stack.pop()
                    if (blacklist and (title in blacklist))\
                    or (whitelist and not \
                    any(elem in title for elem in whitelist)):
                        stack = []
                        break
                    child = DriveFile(parent, item)
                    self.folders_hash[item['id']] = child
                folders.pop(i)
                i = 0
        print('\rGenerating tree: 100%     ')
        if complete:
            for file_id, metadata in list(self.files_hash.items()):
                if not metadata['parents'][0] == self.root.get_id():
                    if not metadata['parents'][0] in self.folders_hash:
                        self.files_hash.pop(file_id)
                        continue
                    else:
                        parent = self.folders_hash[metadata['parents'][0]]
                else:
                    if filter_enabled:
                        continue
                    parent = self.root
                DriveFile(parent, metadata)

    def load_from_file(self, file_path=None):
        '''Loads the tree from disk'''
        if not file_path:
            file_path = self.save_path

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        return self

    def print_folder(self, folder):
        '''Prints the folder recusrively'''
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
        '''Saves the tree to disk'''
        if not file_path:
            file_path = self.save_path
        if not os.path.exists(os.path.split(os.path.abspath(file_path))[0]):
            os.makedirs(os.path.split(os.path.abspath(file_path))[0])

        with open(file_path, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
            f.flush()
