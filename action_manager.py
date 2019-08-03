import os
from drive_file import DriveFolder
from defines import tree_cache

class ActionManager:
    def __init__(self, drive, drive_tree):
        self.drive = drive
        self.drive_tree = drive_tree
    
    def blacklist(self):
        print('Blacklisting')
    
    def clearCache(self):
        if os.path.exists(tree_cache):
            os.remove(tree_cache)
            print('Cache cleared')
        else:
            print('There is no cache to delete')

    def download(self, path, destination):
        closest_node, found, remaining_path = self.drive_tree.getClosestNodeFromPath(path)
        if not found:
            closest_node = self.drive_tree.loadPath(remaining_path)
            if not closest_node:
                print('File not found')
                return
        destination = os.path.abspath(destination)
        if not os.path.exists(destination):
            os.makedirs(destination)
        
        file1 = self.drive.CreateFile({'id': closest_node.getId()})
        save_path = destination + '/' + file1['title']
        print('Downloading', path, 'to', save_path)
        file1.GetContentFile(save_path)


    
    def file_status(self):
        pass

    def force_sync(self):
        pass
    
    def get_sync_progress(self):
        self
    
    def list_files(self, path='root'):
        closest_node, found, remaining_path = self.drive_tree.getClosestNodeFromPath(path)
        files = []
        if not found:
            closest_node = self.drive_tree.loadPath(remaining_path)
            if not closest_node:
                print('File not found')
                return
        file_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false" % closest_node.getId()}).GetList()
        for file1 in file_list:
            if not self.drive_tree.findFileInParent(closest_node, file1['id']):
                self.drive_tree.addFile(closest_node, file1['id'], file1['title'])
            files.append(file1['title'])
        
        for file1 in sorted(files, key=lambda s: s.casefold()):
            print(file1)

        self.drive_tree.saveToFile(tree_cache)
    
    def move(self, origin, dest):
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

    def getTree(self):
        return self.drive_tree
    
    def getDrive(self):
        return self.drive