import os
import sys

APP_PATH = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
CLIENT_SECRET_FILE = APP_PATH + '/client_secrets.json'
CREDENTIALS_FILE = APP_PATH + '/credentials.json'
DEFAULT_DRIVE_SYNC_DIRECTORY = APP_PATH + '/drive_sync/'
DEFAULT_DOWNLOAD_PATH = os.path.join(os.environ['HOME'], 'Drive_downloads')
LOG_FILE = APP_PATH + '/sync.log'
PID_FILE = APP_PATH + '/.jrt_drive_sync.pid'
DEFAULT_SETTINGS_FILE = APP_PATH + '/config.yaml'
SYNC_APPLICATION = APP_PATH + '/jrt_drive_sync.py'
TREE_CACHE = APP_PATH + '/.cache'
HELPS = \
{
    #Operations
    'download': ['''Download a folder or file from drive to local
    storage (Default: ~/Drive_download'''],
    'list': [
        '''List drive root or if specified, a folder''',
        '''List trash'''
    ],
    'mkdir': ['''Create a specified directory in drive'''],
    'move': ['''Move a file between directories in drive'''],
    'rename': ['''Rename a file in drive'''],
    'restore': ['''Restores a file from trash'''],
    'remove': [
        '''Move a drive file to trash (see [%(prog)s rm -h] for extra information)''',
        '''Delete the file permanently without moving to trash'''
    ],

    #Synchronizer
    'start': ['''Starts the process that will keep the selected folder \
                 synchronized with Google Drive folder'''],
    'stop': ['''Stops syncronizing the drive'''],

    #Options
    'clear-cache': ['''Clear the local cache from drive files'''],
    'blacklist': ['''Enables blacklist to the given files. If no files are given, enables blacklist\
                     and load files from the config file. (If whitelist is enabled, automatically\
                     disables it.)'''],
    'show-cache': ['''Show the local cached tree from drive files'''],
    'show-filter': ['''Show status from filter, either blacklist or whitelist.'''],
    'sync-cache': ['''Load the whole file tree to the local cache'''],
    'whitelist': ['''Enables whitelist to the given files. If no files are given, enables whitelist\
                     and load files from the config file. (If blacklist is enabled, automatically\
                     disables it.)'''],
    'help': ['''Show help menu''']
}
COMMANDS = \
{
    'operations':
    {
        '-d, --download': {'help': '''Download a folder or file from drive'''},
        '-a, --file_status': {'help': '''Shows file status'''},
        '-m, --move': {'help': '''Move a folder in drive'''},
        '-O, --open_in_drive': {'help':
                                '''Opens a browser with the selected file or folder,\
                                root if nothing specified'''},
    },
    'sync':
    {
        '-b, --blacklist': {'help':
                            '''Select specific files or folders to not sync \
                            (can't be enabled at the same time as whitelist)'''},
        '-F, --force_sync': {'help':
                             '''Forces a sync before the timing, when the command is executed,\
                             the timer resets to the settings.yaml timing'''},
        '--get_sync_progress': {'help': '''Display the sync status'''},
        '-p, --pause_sync': {'help': '''Pause drive sync'''},
        '-e, --resume_sync': {'help': '''Resume drive sync'''},
        '-d, --set_sync_delay': {'help': '''If drive sync will start on OS startup'''},
        '-s, start': {'help':
                      '''Start sync the specified file, if None, the current file is synced'''},
        '-S, --stop': {'help': '''Stop sync'''},
        '-w, --whitelist': {'help':
                            '''Select specific files or folders to sync \
                            (can't be enabled at the same time as blacklist)'''}
    },
    'configurations':
    {
        '-A, --set_autostart': {'help': '''Set if sync will start on OS startup'''},
        '-h, --help': {'help': '''Shows the help menu'''}
    }
}

DEFAULT_SETTINGS = \
{
    'delay-time': {'days': 0, 'hours': 0, 'minutes': 10, 'seconds': 0},
    'blacklist-enabled': False,
    'whitelist-enabled': False,
    'blacklist-files': [],
    'whitelist-files': [],
    'drive-sync-directory': DEFAULT_DRIVE_SYNC_DIRECTORY,
    'client_config_file': 'client_secrets.json'
}
