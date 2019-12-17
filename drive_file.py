import io
import os

from apiclient.http import MediaIoBaseDownload
from mime_names import CONVERTS, TYPES

class DriveFile:
    def __init__(self, parent, file_struct):
        self.parent = parent
        self.id = file_struct['id']
        self.name = file_struct['name']
        self.children = []
        self.mime = file_struct['mimeType']
        if parent:
            self.level = parent.get_level() + 1
            parent.add_child(self)
        else:
            self.level = 0

    def add_child(self, children):
        self.children.append(children)

    def download(self, destination, service, recursive=True):
        destination = os.path.abspath(destination)
        file1 = service.files().get(fileId=self.id).execute()

        if file1['mimeType'] == TYPES['folder']:
            folder_path = destination + self.get_path()
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            print('Progress %s: 100%%' % self.name)
            if recursive:
                children_list =\
                    service.files().list(q="'%s' in parents and trashed = false"
                                         % file1['id'],
                                         fields='files(name, id, parents, mimeType)')\
                                         .execute().get('files', [])
                for child in children_list:
                    node = DriveFile(self, child)
                    node.download(destination, service)
                return
            return

        if file1['mimeType'] in CONVERTS:
            file1['name'] = os.path.splitext(file1['name'])[0] + \
                                CONVERTS[file1['mimeType']][1]
            mime = CONVERTS[file1['mimeType']][0]
            request = service.files().export(fileId=file1['id'], mimeType=mime)
        else:
            request = service.files().get_media(fileId=file1['id'])

        save_path = destination + self.parent.get_path()
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        fh = io.FileIO(save_path + file1['name'], 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        print("Progress %s: 0%%" % file1['name'], end='', flush=True)
        while not done:
            status, done = downloader.next_chunk()
            print("\rProgress %s: %d%%" %
                  (file1['name'], int(status.progress()*100)), end='')
        print("\rProgress %s: 100%%" % file1['name'])

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
        if self.mime == TYPES['folder']:
            is_folder = '/'
        else:
            is_folder = ''
        return self.parent.get_path() + self.name + is_folder

    def remove_child(self, children):
        self.children.remove(children)

    def set_name(self, name):
        self.name = name

    def set_parent(self, parent):
        if self.parent:
            self.parent.remove_child(self)
        parent.add_child(self)
        self.parent = parent
        self.level = parent.get_level() + 1
