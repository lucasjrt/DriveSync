import os
import signal
from fcntl import flock, LOCK_EX, LOCK_NB
from multiprocessing import Process, Lock
from ruamel_yaml import YAML
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from defines import PID_FILE, CREDENTIALS_FILE, SETTINGS_FILE, DEFAULT_SETTINGS
from drive_file import DriveTree
from drive_session import DriveSession
from mime_names import TYPES
from utils import log
from sig_handlers import SignalHandler

class Synchronizer:
    def __init__(self):
        self.drive_session = DriveSession(CREDENTIALS_FILE, is_sync=True)
        root_id = self.drive_session.drive.GetAbout()['rootFolderId']
        self.drive_tree = DriveTree(root_id, self.drive_session.drive)
        settings = self.load_settings()
        self.do_sync = True
        self.delay = self.delay_to_seconds(settings['delay-time'])
        self.blacklist_enabled = settings['blacklist-enabled']
        self.whitelist_enabled = settings['whitelist-enabled']
        if self.blacklist_enabled and self.whitelist_enabled:
            log('ERROR: blacklist and whitelist cannot be enabled simultaneously, stopping...')
            return
        if self.blacklist_enabled:
            self.blacklist_files = settings['blacklist-files']
        elif self.whitelist_enabled:
            self.whitelist_files = settings['whitelist-files']
        self.drive_sync_directory = settings['drive-sync-directory']
        log("sync directory:", self.drive_sync_directory)
        if not os.path.exists(self.drive_sync_directory):
            os.makedirs(self.drive_sync_directory)

        sig_handler = SignalHandler(self)
        signal.signal(signal.SIGTERM, sig_handler.stop_handler)

        self.observer = Observer()
        self.observer.schedule(FileChangedHandler(), self.drive_sync_directory, recursive=True)
        self.observer.start()

        #self.sync_thread = Thread

        while True:
            signal.pause()

    def load_settings(self):
        yaml = YAML()
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as settings:
                return dict(yaml.load(settings))

        with open(SETTINGS_FILE, 'w+') as settings:
            yaml.dump(DEFAULT_SETTINGS, settings)
            return DEFAULT_SETTINGS

    def delay_to_seconds(self, delay):
        total = 0
        if 'seconds' in delay:
            total += delay['seconds']
        if 'minutes' in delay:
            total += 60 * delay['minutes']
        if 'hours' in delay:
            total += 3600 * delay['hours']
        if 'days' in delay:
            total += 86400 * delay['days']
        return total

    def disable_observer(self):
        self.observer.stop()

    def sync_cache(self):
        print("syncing cache")
        mutex = Lock()
        # for each node check if it exists on drive, and if so
        # check if there's any new child
        files = self.drive_session.drive.ListFile({'q': "'root' in parents and trashed = false"
                                                  }).GetList()
        file_names = [file1['title'] for file1 in files]
        children = self.drive_tree.get_root().get_children()
        children_names = [node.get_name() for node in self.drive_tree.get_root().get_children()]

        #first remove
        for child in children:
            if child.get_name() not in file_names:
                self.drive_tree.get_root().remove_children(child)

        #then add
        for file1 in files:
            if file1['title'] not in children_names:
                self.drive_tree.add_file(self.drive_tree.get_root(), file1['id'],
                                         file1['title'], file1['mimeType'])

        mutex.acquire()
        self.drive_tree.save_to_file()
        mutex.release()

        #repeat for children recursively
        for child in children:
            t = Process(target=self._sync_cache_children, args=(child, mutex))
            t.start()

        #write update
        mutex.acquire()
        self.drive_tree.save_to_file()
        mutex.release()

    def _sync_cache_children(self, node, mutex):
        print("Requiring files from", node.get_name())
        files = self.drive_session.drive.ListFile({'q': "'%s' in parents and trashed = false"
                                                        % node.get_id()}).GetList()
        print("Recieved")
        file_names = [file1['title'] for file1 in files]
        children = node.get_children()
        children_names = [child_node.get_name() for child_node in node.get_children()]

        #first remove
        for child in children:
            if child.get_name() not in file_names:
                node.remove_children(child)

        #then add
        for file1 in files:
            if file1['title'] not in children_names:
                self.drive_tree.add_file(node, file1['id'], file1['title'], file1['mimeType'])

        mutex.acquire()
        self.drive_tree.save_to_file()
        mutex.release()

        #repeat for children recursively
        for child in children:
            if child.get_mime() == TYPES['folder']:
                t = Process(target=self._sync_cache_children, args=(child, mutex))
                t.start()


class FileChangedHandler(FileSystemEventHandler):
    def on_created(self, event):
        log('File created', event.src_path)

    def on_moved(self, event):
        log('File moved from', event.src_path, 'to', event.dest_path)

    def on_deleted(self, event):
        log('File deleted', event.src_path)

def main():
    cntl = open(PID_FILE, 'w')
    try:
        flock(cntl, LOCK_EX | LOCK_NB)
        cntl.write(str(os.getpid()))
        cntl.flush()
        Synchronizer()
    except BlockingIOError:
        print('An unexpected instance of JRT Drive Sync is running, quitting...')
        return

if __name__ == '__main__':
    main()
