import os
import signal
import subprocess
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN

from defines import DEFAULT_DRIVE_SYNC_DIRECTORY, LOG_FILE, TREE_MIRROR, PID_FILE, SYNC_APPLICATION
from mime_names import TYPES
from drive_tree import DriveTree

class SyncController:
    def __init__(self, drive, am):
        self.mirror_tree = DriveTree(drive, TREE_MIRROR).load_from_file()
        self.am = am

    # Remote action manager (local action manager is located at action_manager.py)
    def blacklist(self):
        print('Blacklisting')

    def clear_mirror(self):
        if os.path.exists(TREE_MIRROR):
            os.remove(TREE_MIRROR)
            print('Mirror cleared')
        else:
            print('Empty mirror')

    def download_mirror(self):
        '''Download all the files from the mirror tree'''
        path = DEFAULT_DRIVE_SYNC_DIRECTORY
        print('saving at:', path)
        if not os.path.exists(path):
            os.mkdir(path)
        nodes = self.mirror_tree.get_root().get_children()
        while nodes:
            node = nodes[0]
            nodes = nodes + node.get_children()
            if node.get_mime() == TYPES['folder']:
                if not os.path.exists(path + node.get_path()):
                    os.mkdir(path + node.get_path())
            else:
                destination = path + '/' + node.get_parent().get_path()
                self.am.download_from_node(node, destination, recursive=False)
            print(nodes.pop(0).get_name(), 'downloaded')

    def force_sync(self):
        pass

    def get_sync_progress(self):
        pass

    def pause_sync(self):
        pass

    def resume_sync(self):
        print('Resuming sync')

    def set_autostart(self):
        pass

    def set_sync_delay(self):
        pass

    def show_mirror(self):
        if os.path.exists(TREE_MIRROR):
            self.mirror_tree.print_tree()
        else:
            print('Empty mirror')

    def start(self, target_file):
        with open(PID_FILE, 'r') as sync:
            try:
                flock(sync, LOCK_EX | LOCK_NB)
                flock(sync, LOCK_UN)
                print('Starting...\nSee', LOG_FILE, 'for more information')
                subprocess.Popen(["python", SYNC_APPLICATION, target_file],
                                 stdout=open(LOG_FILE, 'a'))
            except BlockingIOError:
                print('JRT Drive Sync is already running')

    def stop(self):
        with open(PID_FILE, 'r') as pid:
            try:
                flock(pid, LOCK_EX | LOCK_NB)
                flock(pid, LOCK_UN)
                print('No instance of JRT Drive Sync is running')
            except BlockingIOError:
                print('Stopping')
                target_pid = int(pid.read())
                print('Sending signal to', target_pid)
                os.kill(target_pid, signal.SIGTERM)

    def sync_mirror(self):
        self.mirror_tree.load_complete_tree()
        self.mirror_tree.save_to_file()
        print('Mirror synced')

    def whitelist(self):
        pass
