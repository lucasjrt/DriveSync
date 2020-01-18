import os
import signal
import subprocess
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN

from defines import DEFAULT_DOWNLOAD_MIRROR, IPC_FILE, LOG_FILE, TREE_MIRROR, PID_FILE, SYNC_APPLICATION
from drive_tree import DriveTree

class SyncController:
    def __init__(self, service, am, root):
        self.mirror_tree = DriveTree(service, TREE_MIRROR, root).load_from_file()
        self.am = am

    # Remote action manager (local action manager is located at action_manager.py)
    def clear_mirror(self):
        if os.path.exists(TREE_MIRROR):
            os.remove(TREE_MIRROR)
            print('Mirror cleared')
        else:
            print('Empty mirror')

    def download_mirror(self):
        # '''Download all the files from the mirror tree'''
        self.mirror_tree.download(DEFAULT_DOWNLOAD_MIRROR)

    def get_service(self):
        return self.am.get_service()

    def force_sync(self):
        pass

    def get_sync_progress(self):
        pass

    def pause(self):
        with open(PID_FILE, 'r') as pid:
            try:
                flock(pid, LOCK_EX | LOCK_NB)
                flock(pid, LOCK_UN)
                print('No instance of JRT Drive Sync is running')
            except BlockingIOError:
                try:
                    target_pid = int(pid.read())
                    print('Pausing syncrhonization', target_pid)
                    with open(IPC_FILE, 'a') as f:
                        f.write(str(os.getpid()) + ';pause\n')
                    os.kill(target_pid, signal.SIGUSR1)
                    # returned = signal.sigtimedwait([signal.SIGUSR1], 3.0)
                    # print(signal.sigwait([signal.SIGUSR1]))
                    # print('anything in here')
                    # print('sigusr1:', signal.SIGUSR1)
                    # signal.signal(signal.SIGUSR1, None)
                    # signal.sigwait([signal.SIGUSR1])
                    # if returned:
                    #     print('Synchronizaton paused')
                    # else:
                    #     print('Unable to pause the sync')
                except ValueError:
                    print('ERROR: The PID file is invalid, can\'t send signal to the sync process.')

    def resume(self):
        with open(PID_FILE, 'r') as pid:
            try:
                flock(pid, LOCK_EX | LOCK_NB)
                flock(pid, LOCK_UN)
                print('No instance of JRT Drive Sync is running')
            except BlockingIOError:
                try:
                    target_pid = int(pid.read())
                    with open(IPC_FILE, 'a') as f:
                        f.write(str(os.getpid()) + ';resume\n')
                    os.kill(target_pid, signal.SIGUSR1)
                    print('Synchronization is no longer paused')
                except ValueError:
                    print('ERROR: The PID file is invalid, can\'t send signal to the sync process.')
                    

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
                subprocess.Popen(["python", SYNC_APPLICATION, target_file],
                                 stdout=open(LOG_FILE, 'a'))
                print('JDS is now running\nSee', LOG_FILE, 'for more information')
            except BlockingIOError:
                print('JRT Drive Sync is already running')
    
    def status(self):
        with open(PID_FILE, 'r') as pid:
            try:
                flock(pid, LOCK_EX | LOCK_NB)
                flock(pid, LOCK_UN)
                print('JDS is not running')
            except BlockingIOError:
                try:
                    target_pid = int(pid.read())
                    with open(IPC_FILE, 'a') as f:
                        f.write(str(os.getpid()) + ';status\n')
                    os.kill(target_pid, signal.SIGUSR1)
                except ValueError:
                    print('ERROR: The PID file is invalid, can\'t send signal to the sync process.')

    def stop(self):
        with open(PID_FILE, 'r') as pid:
            try:
                flock(pid, LOCK_EX | LOCK_NB)
                flock(pid, LOCK_UN)
                print('No instance of JRT Drive Sync is running')
            except BlockingIOError:
                print('Stopping')
                try:
                    target_pid = int(pid.read())
                    os.kill(target_pid, signal.SIGTERM)
                    print('JRT Drive Sync is no longer running')
                except ValueError:
                    print('ERROR: The PID file is invalid, can\'t send signal to the sync process.')

    def sync_mirror(self, filter_enabled=True):
        self.mirror_tree.load_complete_tree(filter_enabled=filter_enabled)
        self.mirror_tree.save_to_file()

    def whitelist(self):
        pass
