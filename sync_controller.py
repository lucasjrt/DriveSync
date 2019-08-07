import os
import signal
import subprocess
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
from defines import LOG_FILE

from defines import PID_FILE, SYNC_APPLICATION

class SyncController:
    def start(self, target_file):
        with open(PID_FILE, 'r') as sync:
            try:
                flock(sync, LOCK_EX | LOCK_NB)
                flock(sync, LOCK_UN)
                print('Starting')
                subprocess.Popen(["python", SYNC_APPLICATION, target_file],
                                 stdout=open(LOG_FILE, 'a'))
            except BlockingIOError:
                print('JRT Drive Sync is already running')

    def stop(self):
        print('Stopping')
        with open(PID_FILE, 'r') as pid:
            try:
                flock(pid, LOCK_EX | LOCK_NB)
                flock(pid, LOCK_UN)
                print('No instance of JRT Drive Sync is running')
            except BlockingIOError:
                target_pid = int(pid.read())
                print('Sending signal to', target_pid)
                os.kill(target_pid, signal.SIGTERM)
