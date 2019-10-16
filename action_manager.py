import io
import os
import pickle

from apiclient.http import MediaIoBaseDownload
from defines import TREE_CACHE, DEFAULT_DOWNLOAD_PATH
from mime_names import TYPES, CONVERTS

from drive_file import DriveTree

class ActionManager:
    # Local action manager (remote action manager is located at sync_controller.py)
    def __init__(self, drive_session):
        if drive_session is None:
            self.drive_tree = DriveTree(None).load_from_file()
            return
        self.drive_session = drive_session
        self.drive = drive_session.drive
        self.service = drive_session.service
        self.drive_tree = DriveTree(drive_session.drive)
        print('Loading cache', end=' ')
        self.drive_tree = self.drive_tree.load_from_file()
        print('done')

    def clear_cache(self):
        if os.path.exists(TREE_CACHE):
            os.remove(TREE_CACHE)
            print('Cache cleared')
        else:
            print('There is no cache to delete')

    # does not work for folder with multiple files with same name (which is allowed in drive)
    def download(self, path, destination=DEFAULT_DOWNLOAD_PATH, recursive=True):
        node = self.drive_tree.get_node_from_path(path)
        if not node:
            print(path, 'not found')
            return

        destination = os.path.abspath(destination)

        if not os.path.exists(destination):
            os.makedirs(destination)

        file1 = self.drive.CreateFile({'id': node.get_id()})
        print('Downloading', file1['title'])

        if file1['mimeType'] == TYPES['folder']:
            folder_path = destination + '/' + file1['title']
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            if recursive:
                children_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                                          % file1['id']}).GetList()
                for child in children_list:
                    self.download(path + '/' + child['title'], folder_path)
                return

        if file1['mimeType'] in CONVERTS:
            file1['title'] = os.path.splitext(file1['title'])[0] + \
                                CONVERTS[file1['mimeType']][1]
            file1['mimeType'] = CONVERTS[file1['mimeType']][0]

        save_path = destination + '/' + file1['title']

        request = self.service.files().get_media(fileId=file1['id'])
        fh = io.FileIO(save_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print("\rProgress %s: %3d%%." %
                  (file1['title'], int(status.progress()*100)), end='')
        print()

    def file_status(self):
        pass

    def get_drive(self):
        return self.drive

    def get_files_to_file(self):
        ''' stupid function that is still being thought about '''
        files = self.drive.ListFile({'q': '"root" in parents and trashed = false'}).GetList()
        with open("Files.dat", "wb") as f:
            pickle.dump(files, f, pickle.HIGHEST_PROTOCOL)
            # files = pickle.load(f)
            # print(files)

    def get_service(self):
        return self.get_service

    def get_storage(self):
        return self.drive_session.get_storage()

    def get_tree(self):
        return self.drive_tree

    def list_files(self, path, list_trash):
        files = []
        if list_trash:
            file_list = self.drive.ListFile({'q': "trashed = true"}).GetList()

            for file1 in file_list:
                files.append(file1['title'])

            for file1 in sorted(files, key=lambda s: s.casefold()):
                print(file1)
            return

        node = self.drive_tree.get_node_from_path(path)
        if not node:
            print('File not found')
            return

        files = [node.get_name() for node in node.get_children()]


        for file1 in sorted(files, key=lambda s: s.casefold()):
            print(file1)

    def mkdir(self, file_path):
        dir_path, dir_name = os.path.split(file_path)

        if not dir_path:
            dir_path = '/'

        print('Making directory with name "%s" in %s' %(dir_name, dir_path))

        node = self.drive_tree.get_node_from_path(dir_path)
        if not node:
            print(dir_path, 'not found')

        file1 = self.drive.CreateFile({'title': dir_name,
                                       'mimeType': TYPES['folder'],
                                       'parents': [{'id': node.get_id()}]})
        file1.Upload()
        self.drive_tree.add_file(node, file1['id'], dir_name)

    def move(self, origin, dest):
        print('Moving', origin, 'to', dest)

    def open_in_drive(self):
        pass

    def rename(self, file_path, new_name):
        print('Renaming', file_path, 'to', new_name)
        node = self.drive_tree.get_node_from_path(file_path)
        if not node:
            print('File not found')
            return

        file1 = self.drive.CreateFile({'id': node.get_id()})
        file1.Upload()
        file1['title'] = new_name
        print(file1['title'])
        file1.Upload()
        print(file1['title'])
        node.set_name(new_name)
        print('Renamed')

    def rm(self, file_list, force_remove=False):
        print('Removing files:', ', '.join(file_list))
        for file_name in file_list:
            node = self.drive_tree.get_node_from_path(file_name)
            if not node:
                print(file_name, 'not found')
                continue
            file1 = self.drive.CreateFile({'id': node.get_id()})
            if force_remove:
                file1.Delete()
            else:
                file1.Trash()

    def restore(self, restore_files):
        print('Restoring', ', '.join(restore_files))
        file_list = self.drive.ListFile({'q': 'trashed = true'}).GetList()
        for title in restore_files:
            found = False
            for file1 in file_list:
                if file1['title'] == title:
                    restored_file = self.drive.CreateFile({'id': file1['id']})
                    restored_file.UnTrash()
                    print(restored_file['title'], 'restored')
                    found = True
            if not found:
                print(title, 'not found')

    def sync_cache(self):
        self.drive_tree.load_complete_tree()
        self.drive_tree.save_to_file()
        print('Cache synced')
