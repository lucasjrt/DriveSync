from drive_file import DriveFolder
from defines import tree_cache

class ActionManager:
    def __init__(self, drive, drive_tree):
        self.drive = drive
        self.drive_tree = drive_tree
    
    def blacklist(self):
        print('Blacklisting')
    
    def download(self):
        pass
    
    def file_status(self):
        pass

    def force_sync(self):
        pass
    
    def get_sync_progress(self):
        self
    
    def list_files(self, path='root'):
        path_list = path.split('/')
        deepness = len(path_list)
        current_search = 'root'
        if path[-1] == '/':
            deepness = deepness - 1
            path_list.remove(path_list[-1])
        
        if deepness <= 1:
            files = []
            file_list = self.drive.ListFile({'q': "'root' in parents and trashed = false"}).GetList()
            for file1 in file_list:
                if not self.drive_tree.findFolderInParent(self.drive_tree.getRoot(), file1['id']):
                    print('file was not on root')
                    print('file name:', file1['title'])
                    print('root children:')
                    for child in self.drive_tree.getRoot().getChildren():
                        print(child.getName())
                    self.drive_tree.addFolder(self.drive_tree.getRoot(), file1['id'], file1['title'])
                files.append(file1['title'])
            for file1 in sorted(files, key=lambda s: s.casefold()):
                print(file1)
            return

        file_found = None
        for i in range(deepness + 1):
            next_found = False
            file_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false" % current_search}).GetList()
            for file1 in file_list:
                #file not in tree
                if not self.drive_tree.findFolder(file1['id'], deepness=i + 1):
                    newp = self.drive_tree.findFolder(file1['parents'][0]['id'], deepness=i)
                    if newp is not None:
                        self.drive_tree.addFolder(newp, file1['id'], file1['title'])
                if file1['title'] == path_list[-1] and i == deepness - 1:
                    file_found = file1['id']
                elif i + 1< deepness:
                    if file1['title'] == path_list[i+1]:
                        current_search = file1['id']
                        next_found = True
                if file1['title'] == path_list[-1]:
                    file_found = file1['id']
            if not next_found and not file_found:
                print(path, 'not found')
                return

        if file_found:
            files = []
            file_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false" % file_found}).GetList()
            for file1 in file_list:
                if not self.drive_tree.findFolder(file1['id'], deepness=deepness + 1):
                    newp = self.drive_tree.findFolder(current_search, deepness=deepness)
                    self.drive_tree.addFolder(newp, file1['id'], file1['title'])
                files.append(file1['title'])
            
            for file1 in sorted(files, key=lambda s: s.casefold()):
                print(file1)
            self.drive_tree.saveToFile(tree_cache)
        else:
            print(path, 'not found')
    
    def move(self):
        pass

    def open_in_drive(self):
        pass
    
    def pause_sync(self):
        pass

    def resume_sync(self):
        print('Resuming sync')

    def set_autostart(self):
        pass
    
    def set_sync_delay(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def whitelist(self):
        pass