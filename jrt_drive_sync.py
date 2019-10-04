import os
import signal
import time
from fcntl import flock, LOCK_EX, LOCK_NB
from ruamel_yaml import YAML
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from defines import PID_FILE, SETTINGS_FILE, DEFAULT_SETTINGS
from utils import log
from sig_handlers import SignalHandler

class Synchronizer:
    def __init__(self):
        settings = self.load_settings()
        self.do_sync = True
        self.delay = self.delay_to_seconds(settings['delay-time'])
        self.blacklist_enabled = settings['blacklist-enabled']
        self.whitelist_enabled = settings['whitelist-enabled']
        if self.blacklist_enabled and self.whitelist_enabled:
            log('Invalid config, blacklist cannot be enabled with whitelist, stopping...')
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
