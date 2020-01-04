import io
import os

from apiclient.http import MediaIoBaseDownload
from defines import DEFAULT_DOWNLOAD_CACHE, DEFAULT_DOWNLOAD_PATH, TREE_CACHE
from mime_names import TYPES, CONVERTS

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
            index = 'd'
            depth = 1
            children = list(nodes)
            while index == 'd':
                for i, node in enumerate(nodes):
                    print('\n{}) {}'.format(str(i + 1), node.get_path()))
                    self.drive_tree.print_folder(node, depth=depth)
                index = input('\nWhich of them would you like to download? (1..%d/d) '
                              % len(nodes))
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
                        print('Max deepth reached')
                else:
                    try:
                        index = int(index)
                        if index < 1 or index > len(nodes):
                            print('Invalid choice')
                            index = 'd'
                    except ValueError:
                        print('Invalid choice')
                        index = 'd'
                self.drive_tree.save_to_file()
            nodes[index - 1].download(destination, self.service)
        else:
            nodes[0].download(destination, self.service)

    def download_cache(self):
        self.drive_tree.download(DEFAULT_DOWNLOAD_CACHE)

    def download_from_node(self, node, destination, recursive=True):
        print('Save path:', destination)
        destination = os.path.abspath(destination)
        if not os.path.exists(destination):
            os.mkdir(destination)

        file1 = self.service.files().get(fileId=node.get_id(),\
                                         fields='files(id, name, mimeType, parents)')
        print('Downloading', file1['name'])

        if file1['mimeType'] == TYPES['folder']:
            folder_path = destination + '/' + file1['name']
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            if recursive:
                children_list = self.service.files().\
                                list(q='"%s" in parents and trashed = false' % file1['id'],\
                                     fields='files(id, name, mimeType, parents)').execute
                for child in children_list:
                    self.download_from_path(node.get_path() + '/' + child['name'], folder_path)
                return
            return

        if file1['mimeType'] in CONVERTS:
            file1['name'] = os.path.splitext(file1['name'])[0] + \
                                CONVERTS[file1['mimeType']][1]
            mime = CONVERTS[file1['mimeType']][0]
            request = self.service.files().export(fileId=file1['id'], mimeType=mime)
        else:
            file1.UpdateMetadata()
            request = self.service.files().get_media(fileId=file1['id'])

        save_path = destination + '/' + file1['name']
        fh = io.FileIO(save_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print("\rProgress %s: %3d%%." %
                  (file1['name'], int(status.progress()*100)), end='')
        print()

    # TODO: set this to allow multiple files with the same name
    def download_from_path(self, drive_path, destination, recursive=True):
        node = self.drive_tree.get_nodes_from_path(drive_path)
        if not node:
            print(drive_path, 'not found')
            return

        self.download_from_node(node, destination, recursive)

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
                                                  fields='files(name)').execute()\
                                                  .get('files', [])
            for file1 in file_list:
                files.append(file1['name'])

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

            files = [f['name'] for f in files]
            if multiple:
                print('{}) {}:'.format(i + 1, node.get_path()))
                node.update_children(self.service)
                self.drive_tree.print_folder(node)
            else:
                for file1 in sorted(files, key=lambda s: s.casefold()):
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
            print('More than one file was found with the path %s:' % dir_path)
            i = 1
            for parent in list(parents):
                if parent.get_mime() != TYPES['folder']:
                    print('"{}" is not a directory.')
                    parents.remove(parent)
                    continue
                self.drive_tree.print_folder(parent)

            index = input('Which of them would you want to create the file (1..%d)? ' % len(parents))
            parent = parents[int(index) - 1]
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
                print('More than one file was found with the path "{}":'.format(file_name))

                input()
            # if force_remove:
            #     sure = input('Are you sure you want to delete "%s" permanenlty? (y/N)'
            #                  % (node.get_name()))
            #     if sure.lower() == 'y':
            #         self.service.files().delete(fileId=node.get_id()).execute()
            #         print('File deleted')
            #     else:
            #         print('Aborted')
            # else:
            #     self.service.files().update(fileId=node.get_id(),
            #                                 body={'trashed': True}).execute()
        else:
            trashed_files = self.service.files().list(q='trashed = true',
                                                      fields='files(name, id)').execute()\
                                                      .get('files', [])
            deleting_file = None
            for file1 in trashed_files:
                if file1['name'] == file_name:
                    if deleting_file:
                        # TODO: Fix this to choose which files wants to delete
                        print('More than one file were found with the name of', file_name)
                        print('(This will be fixed in a future release)')
                        return
                    deleting_file = (file1['name'], file1['id'])
            if deleting_file:
                sure = input('Are you sure you want to delete %s permanenlty? (y/N)'
                             % (deleting_file[0]))
                if sure.lower() == 'y':
                    self.service.files().delete(fileId=deleting_file[1]).execute()
                    print('File deleted')
                else:
                    print('Aborted')
            else:
                print('"{}" not found in trash'.format(file_name))

    def restore(self, restore_file):
        trashed_files = self.service.files().list(q='trashed = true',
                                                  fields='files(name, id)')\
                                                  .execute().get('files', [])
        found = False
        for file1 in trashed_files:
            if file1['name'] == restore_file:
                found = True
                self.service.files().update(fileId=file1['id'],
                                            body={'trashed': False}).execute()
        if not found:
            print('"', restore_file, '" not found', sep='')
            return
        print(restore_file, 'restored')

    def show_cache(self):
        if os.path.exists(TREE_CACHE):
            self.get_tree().print_tree()
        else:
            print('Empty cache')

    def sync_cache(self):
        self.drive_tree.load_complete_tree(filter_enabled=False)
        self.drive_tree.save_to_file()
        print('Cache synced')
