import os, sys

APP_PATH = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
credentials_file = 'credentials.json'
client_secret_file = 'client_secrets.json'
settings_file = 'settings.yaml'
tree_cache = '.cache'
DRIVE_DIR = None
HELPS = \
{
    'list': 'List drive root or if specified, a folder'
}
COMMANDS = \
{
    'operations': 
    {
        '-d, --download': 
        {
            'help': '''Download a folder or file from drive''',
            'nargs': '+',
            'default': None,
            'type': str,
            'required': False,
            'metavar': 'FILES',
            'dest': None
        },
        '-a, --file_status': 
        {
            'help': '''Shows file status''', 
            'nargs': '+',
            'default': None,
            'type': str,
            'required': False,
            'metavar': 'FILE',
            'dest': None
        },
        '-m, --move': 
        {
            'help': '''Move a folder in drive''',
            # 'action': am.move,
            'nargs': 2,
            'default': None,
            'type': str,
            'required': False,
            'metavar': 'FILE',
            'dest': None
        },
        '-O, --open_in_drive':
        {
            'help': '''Opens a browser with the selected file or folder, root if nothing specified''',
            'nargs': '?',
            'default': '.',
            'type': str,
            'required': False,
            'metavar': 'FILE',
            'dest': None
        },
        '-s, start': 
        {
            'help': '''Start sync the specified file, if None, the current file is synced''',
            'nargs': '+',
            'default': None,
            'type': None,
            'required': False,
            'metavar': '',
            'dest': None
        },
        '-S, --stop': 
        {
            'help': '''Stop sync''',
            'nargs': '+',
            'default': None,
            'type': None,
            'required': False,
            'metavar': '',
            'dest': None
        }
    },
    'sync':
    {
        '-b, --blacklist': 
        {
            'help': '''Select specific files or folders to not sync (can't be enabled at the same time as whitelist)''', 
            'nargs': '+',
            'default': None,
            'type': str,
            'required': False,
            'metavar': 'FILES',
            'dest': None
        },
        '-F, --force_sync': 
        {
            'help': '''Forces a sync before the timing, when the command is executed, the timer resets to the settings.yaml timing''',
            'nargs': '+',
            'default': None,
            'type': None,
            'required': False,
            'metavar': '',
            'dest': None
        },
        '--get_sync_progress': 
        {
            'help': '''Display the sync status''',
            'nargs': '+',
            'default': None,
            'type': str,
            'required': False,
            'metavar': '',
            'dest': None
        },
        '-p, --pause_sync':
        {
            'help': '''Pause drive sync''',
            'nargs': '+',
            'default': None,
            'type': None,
            'required': False,
            'metavar': '',
            'dest': None
        },
        '-e, --resume_sync':
        {
            'help': '''Resume drive sync''',
            'nargs': None,
            'default': None,
            'type': None,
            'required': False,
            'metavar': '',
            'dest': None
        },
        '-A, --set_autostart':
        {
            'help': '''Set if sync will start on OS startup''',
            'nargs': '+',
            'default': None,
            'type': bool,
            'required': False,
            'metavar': None,
            'dest': None
        },
        '-d, --set_sync_delay': 
        {
            'help': '''If drive sync will start on OS startup''',
            'nargs': '+',
            'default': None,
            'type': int,
            'required': False,
            'metavar': None,
            'dest': None
        },
        '-w, --whitelist': 
        {
            'help': '''Select specific files or folders to sync (can't be enabled at the same time as blacklist)''',
            'nargs': '+',
            'default': None,
            'type': str,
            'required': False,
            'metavar': 'FILE',
            'dest': None
        }
    },
    'options':
    {

    }
}