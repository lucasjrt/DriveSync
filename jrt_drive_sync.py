import hashlib
import io
import os
import signal
import time
from apiclient.http import MediaIoBaseDownload
from fcntl import flock, LOCK_EX, LOCK_NB
from threading import Thread, Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from defines import CREDENTIALS_FILE, PID_FILE, TREE_CACHE, TREE_MIRROR
from drive_tree import DriveTree
from drive_session import DriveSession
from mime_names import CONVERTS, TYPES
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
        self.listening = True

        log('sync directory:', self.drive_sync_directory)
        log('delay:', self.delay, 'seconds')

        self.sync_running = Event()
        self.sync_running.set()

        self.sync_thread = Thread(target=self.synchronize)
        self.sync_thread.start()

        self.time_left = 0
        self.cdown_name = ''
        self.cdown_status = 100

        while True:
            signal.pause()
    
    def download_file(self, node, destination):
        self.cdown_name = node.get_name()
        self.cdown_status = 0
        destination = os.path.abspath(destination)
        if node.get_mime() == TYPES['folder']:
            folder_path = destination + node.get_path()
            if node.namesakes():
                if node.get_sequence() and node.get_sequence() > 0:
                    folder_path = folder_path[:-1] + ' (' + str(node.get_sequence()) + ')/'
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                log('Progress %s: 100%%' % node.get_name())
            else:
                log('Skipping', node.get_name())
            return
        file1 = self.service.files().get(fileId=node.get_id()).execute()
        if file1['mimeType'] in CONVERTS:
            file1['name'] = os.path.splitext(file1['name'])[0] + \
                                CONVERTS[file1['mimeType']][1]
            mime = CONVERTS[file1['mimeType']][0]
            request = self.service.files().export(fileId=file1['id'], mimeType=mime)
        else:
            request = self.service.files().get_media(fileId=file1['id'])
        save_path = destination + node.get_parent().get_path()
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        file_name = save_path + file1['name']
        if node.namesakes():
            file_name += ' (' + str(node.get_sequence()) + ')'
        if os.path.exists(file_name):
            if node.get_md5() and node.get_md5() == self.get_hash(file_name):
                log('Skipping', node.get_name())
                return
        fh = io.FileIO(file_name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        log('Downloading', node.get_name())
        while not done:
            self.sync_running.wait()
            self.cdown_status, done = downloader.next_chunk()

    def get_sync_thread(self):
        return self.sync_thread
    
    def get_hash(self, file_path):
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def is_listening(self):
        return self.listening

    def is_syncing(self):
        return self.sync_running.is_set()

    def sync_local(self):
        pass

    def sync_remote(self):
        if not os.path.exists(self.drive_sync_directory):
            os.makedirs(self.drive_sync_directory)
        nodes = self.mirror_tree.get_root().get_children()
        while nodes:
            if not self.is_running:
                return
            self.sync_running.wait()
            node = nodes.pop(0)
            nodes = nodes + node.get_children()
            self.download_file(node, self.drive_sync_directory)

    def synchronize(self):
        '''Main method that will execute every time it's sync time'''
        while True:
            if not self.sync_running:
                return
            self.sync_running.wait()
            
            #Do sync
            log('Loading files info')
            self.mirror_tree.load_complete_tree()
            log(self.mirror_tree.get_file_count(), 'files info received')
            if not self.sync_running:
                return
            self.sync_running.wait()
            self.sync_remote()
            log('Synchronization finished')
            
            self.time_left = self.delay
            while self.time_left:
                if not self.is_running:
                    return
                self.time_left -= 1
                self.sync_running.wait()
                time.sleep(1)


    def pause(self):
        if self.sync_running.is_set():
            self.sync_running.clear()
            self.listening = False
            return True
        return False

    def resume(self):
        if not self.sync_running.is_set():
            self.sync_running.set()
            self.listening = True
            return True
        return False

    def status(self):
        if self.sync_running.is_set():
            if self.time_left:
                status = format_seconds(self.time_left) + ' until next sync'
            else:
                status = 'Downloading ' + self.cdown_name + ': ' + str(self.cdown_status) + '%'
        else:
            status = 'synchronization paused'
        return status

    def stop(self):
        self.observer.stop()
        self.is_running = False
        self.sync_running.set()
        
class FileChangedHandler(FileSystemEventHandler):
    def __init__(self, instance):
        self.instance = instance
    
    def on_created(self, event):
        if not self.instance.is_syncing() and self.instance.is_listening():
            log('File created', event.src_path)

    def on_moved(self, event):
        if not self.instance.is_syncing() and self.instance.is_listening():
            log('File moved from', event.src_path, 'to', event.dest_path)

    def on_deleted(self, event):
        if not self.instance.is_syncing() and self.instance.is_listening():
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
