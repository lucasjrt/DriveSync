import os
import signal
import time
from fcntl import flock, LOCK_EX, LOCK_NB
from threading import Thread, Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from defines import CREDENTIALS_FILE, PID_FILE, TREE_CACHE, TREE_MIRROR
from drive_tree import DriveTree
from drive_session import DriveSession
from utils import delay_to_seconds, format_seconds, load_settings, log
from sig_handlers import SignalHandler

class Synchronizer:
    def __init__(self):
        self.is_running = True # identifies if this is running (used to kill the sync thread)
        self.drive_session = DriveSession(CREDENTIALS_FILE)
        settings = load_settings()
        # self.delay = delay_to_seconds(settings['delay-time'])
        self.delay = 20 # debug only line
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
        if not os.path.exists(self.drive_sync_directory):
            os.makedirs(self.drive_sync_directory)
        self.service = self.drive_session.get_service()
        root_file = self.service.files().get(fileId='root').execute()
        self.cache_tree = DriveTree(self.drive_session.get_service(), TREE_CACHE, root_file)
        self.mirror_tree = DriveTree(self.drive_session.service, TREE_MIRROR, root_file)

        sig_handler = SignalHandler(self)
        signal.signal(signal.SIGTERM, sig_handler.stop_handler)
        signal.signal(signal.SIGUSR1, sig_handler.signal_handler)

        self.observer = Observer()
        self.observer.schedule(FileChangedHandler(self), self.drive_sync_directory, recursive=True)
        self.observer.start()

        log('sync directory:', self.drive_sync_directory)
        log('delay:', self.delay, 'seconds')

        self.sync_running = Event()
        self.sync_running.set()

        self.sync_thread = Thread(target=self.synchronize)
        self.sync_thread.start()

        while True:
            signal.pause()

    def get_sync_thread(self):
        return self.sync_thread

    def is_syncing(self):
        return self.sync_running.is_set()

    def synchronize(self):
        '''Main method that will execute every time it's sync time'''
        while True:
            if not self.sync_running:
                log('Exiting synchronization method')
                return
            self.sync_running.wait()
            log('This should be syncrhonizing right now')
            
            self.time_left = self.delay
            while self.time_left:
                log('Time left until next sync', self.time_left)
                if not self.is_running:
                    log('Exiting synchronization method')
                    return
                self.time_left -= 1
                self.sync_running.wait()
                time.sleep(1)


    def pause(self):
        if self.sync_running.is_set():
            log('Pausing')
            self.sync_running.clear()
            return True
        return False

    def resume(self):
        if not self.sync_running.is_set():
            log('sync was false')
            self.sync_running.set()
            return True
        return False

    def status(self):
        if self.sync_running.is_set():
            log('Status:', format_seconds(self.time_left))
        else:
            log('Status: synchronization paused')
        return 'Got this as status'

    def stop(self):
        self.observer.stop()
        self.is_running = False
        self.sync_running.set()
        
class FileChangedHandler(FileSystemEventHandler):
    def __init__(self, instance):
        self.instance = instance
    
    def on_created(self, event):
        if self.instance.is_syncing():
            log('File created', event.src_path)

    def on_moved(self, event):
        if self.instance.is_syncing():
            log('File moved from', event.src_path, 'to', event.dest_path)

    def on_deleted(self, event):
        if self.instance.is_syncing():
            log('File deleted', event.src_path)

def main():
    with open(PID_FILE, 'w') as cntl:
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
