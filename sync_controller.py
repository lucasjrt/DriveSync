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
        def handler(self, _, __):
            pass
        signal.signal(signal.SIGUSR1, handler)

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
                    print('Pausing syncrhonization')
                    with open(IPC_FILE, 'a') as f:
                        f.write(str(os.getpid()) + ';pause\n')
                    os.kill(target_pid, signal.SIGUSR1)
                    returned = signal.sigtimedwait([signal.SIGUSR1], 3.0)
                    if returned:
                        with open(IPC_FILE, 'r') as f:
                            lines = f.readlines()
                        for line in lines:
                            pid, answer = line.split(';')
                            if int(pid) == target_pid:
                                lines.remove(line)
                                break
                        answer = answer[:-1]
                        if answer == 'paused':
                            print('Synchronization paused')
                        else:
                            print('Synchronization already paused')
                        with open(IPC_FILE, 'w') as f:
                            f.writelines(lines)
                    else:
                        print('Didn\'t get any answer from JDS')
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
                    print('Resuming synchronization')
                    with open(IPC_FILE, 'a') as f:
                        f.write(str(os.getpid()) + ';resume\n')
                    os.kill(target_pid, signal.SIGUSR1)
                    returned = signal.sigtimedwait([signal.SIGUSR1], 3.0)
                    if returned:
                        with open(IPC_FILE, 'r') as f:
                            lines = f.readlines()
                        for line in lines:
                            pid, answer = line.split(';')
                            if int(pid) == target_pid:
                                lines.remove(line)
                                break
                        answer = answer[:-1]
                        if answer == 'resumed':
                            print('Synchronization resumed')
                        else:
                            print('Synchronization is not paused')
                        with open(IPC_FILE, 'w') as f:
                            f.writelines(lines)
                    else:
                        print('Didn\'t get any answer from JDS')
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
                try:
                    pid = int(sync.read())
                    os.kill(pid, 0)
                    print('Unexpected instance of JDS running, killing it before starting another one')
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
                subprocess.Popen(["python", SYNC_APPLICATION, target_file],
                                stdout=open(LOG_FILE, 'a'))
                print('JDS is now running\nSee', LOG_FILE, 'for more information')
            except BlockingIOError:
                print('JRT Drive Sync is already running')
            except ValueError:
                print('Unexpected error')
                os.remove(PID_FILE)
    
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
                    returned = signal.sigtimedwait([signal.SIGUSR1], 3.0)
                    if returned:
                        with open(IPC_FILE, 'r') as f:
                            lines = f.readlines()
                        for line in lines:
                            pid, answer = line.split(';')
                            if int(pid) == target_pid:
                                lines.remove(line)
                                break
                        answer = answer[:-1]
                        with open(IPC_FILE, 'w') as f:
                            f.writelines(lines)
                        print('Status:', answer)
                    else:
                        print('Status not received')
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
