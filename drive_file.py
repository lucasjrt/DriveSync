import os
import pickle
from mime_names import TYPES
from defines import TREE_CACHE

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

class DriveTree:
    def __init__(self, id, drive):
        self.root = DriveFolder(None, id, 'My drive', TYPES['folder'])
        self.drive = drive

    def get_root(self):
        return self.root

    def find_file_in_parent(self, parent, id):
        for f in parent.get_children():
            if f.get_id() == id:
                return f

            # ret = self.findFileInParent(f, id)

            # if ret:
            #     return ret
        return None

    def find_file(self, id):
        if id == self.get_root().get_id():
            return self.root
        return self.find_file_in_parent(self.root, id)

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

    def get_node_from_path(self, path):
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
        # if folder != self.root:
        #     print('|', end='')
        prefix = depth * ('  |') + '--'
        print(prefix, folder.get_name(), '\tid:', folder.get_id(), sep='')
        for child in folder.get_children():
            self.print_folder(child)

    def print_tree(self):
        self.print_folder(self.root)
