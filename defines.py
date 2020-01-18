import os
import sys

APP_PATH = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
CLIENT_SECRET_FILE = APP_PATH + '/client_secrets.json'
CREDENTIALS_FILE = APP_PATH + '/credentials.json'
DEFAULT_DRIVE_SYNC_DIRECTORY = os.path.join(os.environ['HOME'], 'GoogleDrive')
DEFAULT_DOWNLOAD_PATH = os.path.join(os.environ['HOME'], 'Drive_downloads')
DEFAULT_DOWNLOAD_CACHE = APP_PATH + '/cache'
DEFAULT_DOWNLOAD_MIRROR = APP_PATH + '/mirror'
LOG_FILE = APP_PATH + '/sync.log'
PID_FILE = APP_PATH + '/.jrt_drive_sync.pid'
DEFAULT_SETTINGS_FILE = APP_PATH + '/config.yaml'
SYNC_APPLICATION = APP_PATH + '/jrt_drive_sync.py'
TREE_CACHE = APP_PATH + '/.cache'
TREE_MIRROR = APP_PATH + '/.mirror'
HELPS = \
{
    #Operations
    'download': '''Download a folder or file from drive to local
    storage (Default: ~/Drive_downloads''',
    'download-cache': '''Download the cache tree to the local machine''',
    'download-mirror': '''Download the mirror tree to the local machine''',
    'list': [
        '''List drive root or if specified, a folder''',
        '''List trash'''
    ],
    'mkdir': '''Create a specified directory in drive''',
    'move': '''Move a file between directories in drive''',
    'rename': '''Rename a file in drive''',
    'untrash': '''Untrashes a file''',
    'remove': [
        '''Move a drive file to trash (see [%(prog)s rm -h] for extra information)''',
        '''Delete the file permanently without moving to trash''',
        '''Sets the deletion to be on the trash, instead of MyDrive files'''
    ],

    #Synchronizer
    'pause': '''Pauses sync without stoping the execution of jds and can be resumed
                 with jds resume''',
    'resume': '''Return synchronizing after a pause''',
    'start': '''Starts the process that will keep the selected folder
                 synchronized with Google Drive folder''',
    'status': '''Shows current sync status''',
    'stop': '''Stops syncronizing the drive''',

    #Options
    'add-blacklist': '''Adds one or more files to the blacklist and enables blacklist if off.
                      If no files are given it toggles blacklist enabled''',
    'add-whitelist': '''Adds one or more files to the whitelist and enables whitelist if off.
                      If no files are given it toggles whitelist enabled''',
    'clear-cache': '''Clear the local cache from drive files''',
    'clear-mirror': '''Clear the local mirror from drive files''',
    'remove-blacklist': '''Removes the given files from blacklist''',
    'remove-whitelist': '''Removes the given files from whitelist''',
    'set-blacklist': '''Set blacklist to the given files. Clear filter if no files are given''',
    'set-whitelist': '''Set whitelist to the given files. Clear filter if no files are given''',
    'show-cache': '''Show the local cache tree from drive files''',
    'show-mirror': '''Show the local mirror tree from drive files''',
    'show-filter': '''Show status from filter, either blacklist or whitelist''',
    'sync-cache': '''Load the whole file tree to the local cache''',
    'sync-mirror': '''Load the whole file tree to the local mirror''',
    'help': '''Show help menu'''
}

#This will be deleted later, it's only some command ideas that are being
#moved to HELPS
COMMANDS = \
{
    'operations':
    {
        '-a, --file_status': {'help': '''Shows file status'''},
        '-O, --open_in_drive': {'help':
                                '''Opens a browser with the selected file or folder,
                                root if nothing specified'''},
    },
    'sync':
    {
        '-F, --force_sync': {'help':
                             '''Forces a sync before the timing, when the command is executed,
                             the timer resets to the settings.yaml timing'''},
        '-d, --set_sync_delay': {'help': '''If drive sync will start on OS startup'''},
    },
    'configurations':
    {
        '-A, --set_autostart': {'help': '''Set if sync will start on OS startup'''},
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
