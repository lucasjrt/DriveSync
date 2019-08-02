import argparse, sys
from defines import HELPS, credentials_file, tree_cache
from action_manager import ActionManager
from DriveSession import DriveSession
from drive_file import DriveTree

class SyntaxAnalyzer:
    def __init__(self):
        parser = argparse.ArgumentParser(prog = 'jds', 
                                        description='Syncronizes a folder with a Google Drive account', 
                                        epilog='Please notice that this software is still under development', 
                                        add_help=False)

        operations = parser.add_argument_group("Drive Operations")

        operations.add_argument('-l, --list', 
                                help = HELPS['list'],
                                nargs = '?',
                                default = 'root',
                                const = 'root',
                                type = str,
                                metavar = 'FILE',
                                dest = 'list')

        operations.add_argument('-h, --help', 
                                action = 'help', 
                                help = 'show this help message and exit')

        if len(sys.argv) == 1:
            print(parser.format_help())
            return

        args = parser.parse_args()
        session = DriveSession(credentials_file)
        drive = session.getDrive()
        root_id = drive.ListFile({'q': "'root' in parents and trashed = false"}).GetList()[0]['parents'][0]['id']
        am = ActionManager(drive, DriveTree(root_id).loadFromFile(tree_cache))

        if args.list:
            am.list_files(args.list)