import os
import signal
import sched
import time
from fcntl import flock, LOCK_EX, LOCK_NB
from threading import Thread
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
        settings = load_settings()
        self.do_sync = True # if is going to run the sync loop
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
        if not os.path.exists(self.drive_sync_directory):
            os.makedirs(self.drive_sync_directory)
        self.service = self.drive_session.get_service()
        root_file = self.service.files().get(fileId='root').execute()
        self.cache_tree = DriveTree(self.drive_session.get_service(), TREE_CACHE, root_file)
        self.mirror_tree = DriveTree(self.drive_session.service, TREE_MIRROR, root_file)

        sig_handler = SignalHandler(self)
        signal.signal(signal.SIGTERM, sig_handler.stop_handler)
        signal.signal(signal.SIGUSR1, sig_handler.pause_handler)
        signal.signal(signal.SIGUSR2, sig_handler.resume_handler)


        self.observer = Observer()
        self.observer.schedule(FileChangedHandler(self), self.drive_sync_directory, recursive=True)
        self.observer.start()

        self.sched = sched.scheduler(time.time, time.sleep)
        self.sched.enter(5, 1, self.synchronize, (self.sched,))


        log('sync directory:', self.drive_sync_directory)
        log('delay:', self.delay, 'seconds')

        self.sync_thread = Thread(target=self.sched.run)
        self.sync_thread.start()

        while True:
            signal.pause()

    def is_syncing(self):
        return self.do_sync

    def synchronize(self, sch):
        '''Main method that will execute every time it's sync time'''
        if self.do_sync:
            log('This should be syncrhonizing right now')
        sch.enter(5, 1, self.synchronize, (sch,))

    def pause(self):
        self.do_sync = False

    def resume(self):
        self.do_sync = True

    def status(self):
        for event in self.sched.queue:
            log(event)

    def stop(self):
        self.observer.stop()
        self.do_sync = False

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
