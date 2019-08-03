import os, sys

APP_PATH = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
credentials_file = 'credentials.json'
client_secret_file = 'client_secrets.json'
settings_file = 'settings.yaml'
tree_cache = '.cache'
DRIVE_DIR = None
HELPS = \
{   
    'download': '''Download a folder or file from drive to local storage''',
    'list': '''List drive root or if specified, a folder''',
    'move': '''File between directories in drive''',
    'clear-cache': '''Clears the local cache from drive files''',
    'show-cache': '''Show the local cached tree from drive files'''
}
COMMANDS = \
{
    'operations': 
    {
        '-d, --download':  {'help': '''Download a folder or file from drive'''},
        '-a, --file_status': { 'help': '''Shows file status'''},
        '-m, --move': { 'help': '''Move a folder in drive'''},
        '-O, --open_in_drive': { 'help': '''Opens a browser with the selected file or folder, root if nothing specified'''},
    },
    'sync':
    {
        '-b, --blacklist': { 'help': '''Select specific files or folders to not sync (can't be enabled at the same time as whitelist)'''},
        '-F, --force_sync': { 'help': '''Forces a sync before the timing, when the command is executed, the timer resets to the settings.yaml timing'''},
        '--get_sync_progress': { 'help': '''Display the sync status'''},
        '-p, --pause_sync': { 'help': '''Pause drive sync'''},
        '-e, --resume_sync': { 'help': '''Resume drive sync'''},
        '-d, --set_sync_delay': { 'help': '''If drive sync will start on OS startup'''},
        '-s, start': { 'help': '''Start sync the specified file, if None, the current file is synced'''},
        '-S, --stop': { 'help': '''Stop sync'''},
        '-w, --whitelist': { 'help': '''Select specific files or folders to sync (can't be enabled at the same time as blacklist)'''}
    },
    'configurations':
    {
        '-A, --set_autostart': { 'help': '''Set if sync will start on OS startup'''},
        '-h, --help': {'help': '''Shows the help menu'''}
    }
}