import os

from defines import DEFAULT_DOWNLOAD_CACHE, DEFAULT_DOWNLOAD_PATH, TREE_CACHE
from mime_names import TYPES
from utils import bytes_to_human, error, rfc3339_to_human, warn

from drive_tree import DriveTree
from drive_file import DriveFile

class ActionManager:
    # Local action manager (remote action manager is located at sync_controller.py)
    def __init__(self, service, root):
        if service is None:
            self.drive_tree = DriveTree(None, TREE_CACHE, root).load_from_file()
            return
        self.service = service
        self.drive_tree = DriveTree(service, TREE_CACHE, root)
        self.drive_tree = self.drive_tree.load_from_file()

    def clear_cache(self):
        if os.path.exists(TREE_CACHE):
            os.remove(TREE_CACHE)
            print('Cache cleared')
        else:
            print('Empty cache')

    def download(self, file1, destination=DEFAULT_DOWNLOAD_PATH):
        nodes = self.drive_tree.get_nodes_from_path(file1)
        parent_path, file_name = os.path.split(file1)
        if not nodes:
            if not parent_path:
                parent_path = 'MyDrive'
            print('No file "{}" in {}'.format(file_name, parent_path))
            return
        if len(nodes) > 1:
            if not parent_path:
                parent_path = 'MyDrive'
            print('More than one file called "{}" was found in {}.'
                  .format(file_name, parent_path))
            target = self.__multiple_options(nodes)
            target.download(destination, self.service)
        else:
            nodes[0].download(destination, self.service)

    def download_cache(self):
        self.drive_tree.download(DEFAULT_DOWNLOAD_CACHE)

    def file_status(self):
        pass

    def get_service(self):
        return self.service

    def get_storage(self):
        pass

    def get_tree(self):
        return self.drive_tree

    def list_files(self, path, list_trash=False):
        files = []
        if list_trash:
            file_list = self.service.files().list(q='trashed = true',
                                                  fields='files(name, mimeType)')\
                                                  .execute()\
                                                  .get('files', [])
            for file1 in file_list:
                is_file = ''
                if file1['mimeType'] == TYPES['folder']:
                    is_file = '/'
                files.append(file1['name'] + is_file)

            for file1 in sorted(files, key=lambda s: s.casefold()):
                print(file1)
            return

        nodes = self.drive_tree.get_nodes_from_path(path, exclusive=False)
        if not nodes:
            print('File not found')
            return

        multiple = False
        if len(nodes) > 1:
            multiple = True


        for i, node in enumerate(nodes):
            if node.get_mime() != TYPES['folder']:
                print(node.get_name(), 'is not listable')
                return
            query = '"%s" in parents and trashed = false' %node.get_id()
            fields = 'files(name, id, parents, mimeType)'
            files = self.service.files().list(q=query,
                                              fields=fields)\
                                              .execute().get('files', [])

            modified = False
            for f in files:
                if not self.drive_tree.find_file_in_parent(node, f['id']):
                    if not modified:
                        modified = True
                    DriveFile(node, f)

            if modified:
                self.drive_tree.save_to_file()

            print_files = []
            for file1 in list(files):
                is_file = ''
                if file1['mimeType'] == TYPES['folder']:
                    is_file = '/'
                print_files.append(file1['name'] + is_file)
                
            if multiple:
                print('{}) {}:'.format(i + 1, node.get_path()))
                node.update_children(self.service)
                self.drive_tree.print_folder(node)
            else:
                for file1 in sorted(print_files, key=lambda s: s.casefold()):
                    print(file1)
            print()

    def mkdir(self, file_path):
        dir_path, dir_name = os.path.split(file_path)

        if not dir_path:
            dir_path = '/'

        parents = self.drive_tree.get_nodes_from_path(dir_path)
        if not parents:
            print(dir_path, 'not found')
            return
        if len(parents) > 1:
            parent = self.__multiple_options(parents)
        else:
            parent = parents[0]


        file_metadata = {'name': dir_name,
                         'mimeType': TYPES['folder'],
                         'parents': [parent.get_id()]}
        file1 = self.service.files().create(body=file_metadata,
                                            fields='id, name, mimeType, parents').execute()
        DriveFile(parent, file1)

    def move(self, origin, dest):
        print('Moving', origin, 'to', dest)
        origin_node = self.drive_tree.get_nodes_from_path(origin)
        if not origin_node:
            print('"', origin, '" not found', sep='')
            return
        dest_node = self.drive_tree.get_nodes_from_path(dest)
        if not dest_node:
            print('"', dest, '" not found', sep='')
            return
        self.service.files().update(fileId=origin_node.get_id(),
                                    addParents=dest_node.get_id(),
                                    removeParents=origin_node.get_parent().get_id(),
                                    fields='id, parents').execute()
        origin_node.set_parent(dest_node)
        self.drive_tree.save_to_file()

    def __multiple_options(self, nodes):
        index = 'd'
        depth = 1
        children = list(nodes)
        while index == 'd':
            for i, node in enumerate(nodes):
                if node.get_mime() == TYPES['folder']:
                    print('\n{}) {}'.format(str(i + 1), node.get_path()))    
                    self.drive_tree.print_folder(node, depth=depth)
                else:
                    infos = self.service.files().get(fileId=node.get_id(),
                                                    fields='size, modifiedTime').execute()
                    print('\n{}) {}\tSize: {}\t Last modified: {}'.format(str(i + 1), 
                                                      node.get_path(), 
                                                      bytes_to_human(infos['size']),
                                                      rfc3339_to_human(infos['modifiedTime'])))
            index = input('\nWhich of them is your target? ([1..%d]/d) ' % len(nodes))
            if index == 'd':
                for i in range(depth):
                    for node in list(children):
                        if node.get_mime() != TYPES['folder']:
                            continue
                        node.update_children(self.service)
                        for child in node.get_children():
                            children.append(child)
                        children.remove(node)
                depth += 1
                if not children:
                    warn('Max deepth reached')
            else:
                try:
                    index = int(index)
                    if not 0 < index <= len(nodes):
                        raise ValueError
                except ValueError:
                    error('Invalid choice')
                    index = 'd'
            self.drive_tree.save_to_file()
        return nodes[index - 1]

    def __multiple_trash_options(self, candidate_files):
        index = 'd'
        while index == 'd':
            for i, candidate in enumerate(candidate_files):
                print('\n{}) "{}"\t Last modified: {}'
                      .format(str(i + 1), candidate['name'],
                              rfc3339_to_human(candidate['modifiedTime'])))
            index = input('\nWhich of them is your target? ([1..%d]) '
                          % len(candidate_files))
            try:
                index = int(index)
                if not 0 < index <= len(candidate_files):
                    raise ValueError
                return candidate_files[index - 1]
            except ValueError:
                error('Invalid choice')
                index = 'd'

    def open_in_browser(self):
        pass

    def rename(self, file_path, new_name):
        print('Renaming', file_path, 'to', new_name)
        node = self.drive_tree.get_nodes_from_path(file_path)
        if not node:
            print('File not found')
            return

        self.service.files().update(fileId=node.get_id(),
                                    body={'name': new_name}).execute()
        node.set_name(new_name)
        self.drive_tree.save_to_file()

    def rm(self, file_name, force_remove=False, trash_remove=False):
        '''Function that deletes or move to trash a the File "file_name".
        :param file_name: name of the file under operation.
        :type file_name: str.
        :param force_remove: If True, the file is just deleted permanently without
        being sent to trash.
        :type force_remove: bool.
        :param trash_remove: Sets the removing to happen in trash instead of MyDrive
        (Removing from trash deletes the file permanently).
        :type trash_remove: bool.
        '''
        if not trash_remove:
            nodes = self.drive_tree.get_nodes_from_path(file_name)

            if not nodes:
                print('"{}" not found'.format(file_name))
                return
            if len(nodes) > 1:
                node = self.__multiple_options(nodes)
                if force_remove:
                    sure = input('Are you sure you want do delete "{}" permanently (y/N)? ')
                    if sure.lower() == 'y':
                        node.delete(service=self.service, permanent=True)
                else:
                    node.trash(self.service)
            else:
                nodes[0].trash(self.service)
        else:
            fields = 'files(name, id, modifiedTime)'
            trashed_files = self.service.files().list(q='trashed = true',
                                                      fields=fields).execute()\
                                                      .get('files', [])
            candidate_files = []
            for file1 in trashed_files:
                if file1['name'] == file_name:
                    candidate_files.append(file1)
            if not candidate_files:
                print('"%s" not found in trash' % file_name)
                return
            if len(candidate_files) > 1:
                target = self.__multiple_trash_options(candidate_files)
                sure = input('Are you sure you want to delete "%s" permanenlty? (y/N) '
                             % target['name'])
                if sure.lower() == 'y':
                    self.service.files().delete(fileId=target['id']).execute()
            else:
                sure = input('Are you sure you want to delete "%s" permanenlty? (y/N) '
                             % candidate_files[0]['name'])
                if sure.lower() == 'y':
                    self.service.files().delete(fileId=candidate_files[0]['id']).execute()
            self.drive_tree.save_to_file()

    def untrash(self, untrash_file):
        fields = 'files(name, id, parents, mimeType, modifiedTime)'
        trashed_files = self.service.files().list(q='trashed = true',
                                                  fields=fields)\
                                                  .execute().get('files', [])
        candidate_files = []
        for file1 in trashed_files:
            if file1['name'] == untrash_file:
                candidate_files.append(file1)
        if not candidate_files:
            print('"%s" not found' % untrash_file)
            return
        if len(candidate_files) > 1:
            target = self.__multiple_trash_options(candidate_files)
        else:
            target = candidate_files[0]
        self.service.files().update(fileId=target['id'],
                                    body={'trashed': False}).execute()
        parent = self.drive_tree.get_node_from_id(target['id'])
        DriveFile(parent, target)

    def show_cache(self):
        if os.path.exists(TREE_CACHE):
            self.get_tree().print_tree()
        else:
            print('Empty cache')

    def sync_cache(self):
        self.drive_tree.load_complete_tree(filter_enabled=False)
        self.drive_tree.save_to_file()
        print('Cache synced')
