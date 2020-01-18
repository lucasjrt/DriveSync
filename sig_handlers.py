import os
import signal

from utils import log
from defines import IPC_FILE

class SignalHandler():
    def __init__(self, instance):
        self.instance = instance

    def signal_handler(self, _, __):
        with open(IPC_FILE, 'r') as f:
            lines = f.readlines()
        pid = command = None
        for line in lines:
            pid, command = line.split(';')
            if int(pid) != os.getpid():
                lines.remove(line)
                break
        command = command[:-1] # remove '\n'
        if not command:
            return
        if command == 'pause':
            if self.instance.pause():
                log('Syncronization paused')
                lines.append(str(os.getpid()) + ';paused\n')
            else:
                lines.append(str(os.getpid()) + ';false\n')
        elif command == 'resume':
            log('resume command')
            if self.instance.resume():
                log('Synchronization resumed')
                lines.append(str(os.getpid()) + ';resumed\n')
            else:
                lines.append(str(os.getpid()) + ';false\n')
        elif command == 'status':
            lines.append(str(os.getpid()) + ';' + self.instance.status() + '\n')
        with open(IPC_FILE, 'w') as f:
            f.writelines(lines)
        os.kill(int(pid), signal.SIGUSR1) # the answer to the other process

    def stop_handler(self, _, __):
        log('Exiting JDS')
        self.instance.stop()
        self.instance.get_sync_thread().join()
        log('Effectively exiting')
        exit(0)
