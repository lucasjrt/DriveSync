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
        self.sequence_number = None # this will treat the multiple files with the same name problem
        if parent:
            self.level = parent.get_level() + 1
            parent.add_child(self)
        else:
            self.level = 0

    def add_child(self, child):
        greatest_sequence = 0
        for node in self.children:
            if node.get_name() == child.get_name()\
            and node.get_id() != child.get_id():
                sequence = node.get_sequence()
                if sequence:
                    if greatest_sequence < sequence:
                        greatest_sequence = sequence
                else:
                    node.set_sequence(0)
                child.set_sequence(greatest_sequence + 1)
        self.children.append(child)

    def download(self, destination, service, recursive=True):
        destination = os.path.abspath(destination)
        if self.mime == TYPES['folder']:
            folder_path = destination + self.get_path()
            if self.namesakes():
                if self.sequence_number and self.sequence_number > 0:
                    folder_path = folder_path[:-1] + ' (' + str(self.sequence_number) + ')/'
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            print('Progress %s: 100%%' % self.name)
            if recursive:
                file1 = service.files().get(fileId=self.id).execute()
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

        file1 = service.files().get(fileId=self.id).execute()

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

        file_name = save_path + file1['name']
        if self.namesakes():
            file_name += ' (' + str(self.sequence_number) + ')'
        fh = io.FileIO(file_name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        print("Progress %s: 0%%" % file1['name'], end='', flush=True)
        while not done:
            status, done = downloader.next_chunk()
            print("\rProgress %s: %d%%" %
                  (file1['name'], int(status.progress()*100)), end='')
        print("\rProgress %s: 100%%" % file1['name'])

    def get_children(self):
        self.children.sort(key=lambda s: s.get_name())
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

    def get_sequence(self):
        return self.sequence_number

    def namesakes(self):
        '''Return the amount of files in the same parent
        that has the same name self does
        '''
        namesakes = 0
        for sibling in self.parent.get_children():
            if sibling.get_name() == self.name and sibling is not self:
                namesakes += 1
        return namesakes

    def remove_child(self, child):
        self.children.remove(child)

    def set_name(self, name):
        self.name = name

    def set_parent(self, parent):
        if self.parent:
            self.parent.remove_child(self)
        parent.add_child(self)
        self.parent = parent
        self.level = parent.get_level() + 1

    def set_sequence(self, number):
        self.sequence_number = number

    def update_children(self, service):
        '''Updates the children of a node with the drive files'''
        children = service.files().list(q='"%s" in parents and trashed = false' % self.id,
                                        fields='files(name, parents, mimeType, id)')\
                                        .execute().get('files', [])
        remote_ids = [f['id'] for f in children]
        local_ids = [child.get_id() for child in self.children]
        for child in self.children:
            if child.get_id() not in remote_ids:
                self.children.remove(child)

        for metadata in children:
            if metadata['id'] not in local_ids:
                DriveFile(self, metadata)

    def __str__(self):
        return self.name + ' <-> ' + self.id

    def __repr__(self):
        return self.name + ' <-> ' + self.id
