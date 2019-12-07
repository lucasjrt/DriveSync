import os
import signal
from fcntl import flock, LOCK_EX, LOCK_NB
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from defines import CREDENTIALS_FILE, PID_FILE, TREE_CACHE, TREE_MIRROR
from drive_tree import DriveTree
from drive_session import DriveSession
from utils import log, load_settings, delay_to_seconds
from sig_handlers import SignalHandler

class Synchronizer:
    def __init__(self):
        self.drive_session = DriveSession(CREDENTIALS_FILE)
        self.cache_tree = DriveTree(self.drive_session.drive, TREE_CACHE)
        self.mirror_tree = DriveTree(self.drive_session.drive, TREE_MIRROR)
        settings = load_settings()
        self.do_sync = True
        self.delay = delay_to_seconds(settings['delay-time'])
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

    def disable_observer(self):
        self.observer.stop()


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
