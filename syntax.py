import argparse, sys
from defines import HELPS, credentials_file, tree_cache
from action_manager import ActionManager
from drive_session import DriveSession
from drive_file import DriveTree

class SyntaxAnalyzer:
    def __init__(self):
        main_parser = argparse.ArgumentParser(prog = 'jds', description='Syncronizes a folder with a Google Drive account', epilog='Please notice that this software is still under development', add_help=False)
        subparsers = main_parser.add_subparsers(title = 'Commands', dest='command', metavar ='')

        download_parser = subparsers.add_parser('download', help=HELPS['download'], add_help=False)
        list_parser = subparsers.add_parser('list', help=HELPS['list'], add_help = False)
        move_parser = subparsers.add_parser('move', help=HELPS['move'], add_help = False)

        self.add_download_parser(download_parser)
        self.add_list_parsers(list_parser)
        self.add_move_parsers(move_parser)
        self.add_options(main_parser)

        if len(sys.argv) == 1:
            print(main_parser.format_help())
            return

        args = main_parser.parse_args()
        session = DriveSession(credentials_file)
        drive = session.getDrive()
        root_id = drive.CreateFile({'id': 'root'})
        root_id['title'] #Just to update metadata
        am = ActionManager(drive, DriveTree(root_id['id'], drive).loadFromFile(tree_cache))

        if args.command == 'download':
            am.download(args.download_file[0], args.download_destination)
        elif args.command == 'list':
            am.list_files(args.list_file)
        elif args.command == 'move':
            am.move(args.move_origin[0], args.move_destination[0])
        elif args.show_cache:
            am.getTree().printTree()
        elif args.clear_cache:
            am.clearCache()

    def add_download_parser(self, download_parser):
        download_parser.add_argument('download_file',
                                    metavar = 'FILE',
                                    nargs = 1,
                                    help = 'File to be downloaded')
        download_parser.add_argument('download_destination',
                                    const = '.',
                                    default = '.',
                                    metavar = 'DESTINATION',
                                    nargs = '?',
                                    help = 'Location to where the downloaded file will be save')
        download_parser.add_argument('-h, --help', 
                                    action = 'help', 
                                    help = 'Lists the help menu')

    def add_list_parsers(self, list_parser):
        list_parser.add_argument('list_file', 
                                    const = 'root', 
                                    metavar = 'FILE', 
                                    nargs = '?', 
                                    default = 'root',
                                    help='File to be listed')
        list_parser.add_argument('-h, --help', 
                                    action = 'help', 
                                    help = 'Lists the help menu')


    def add_move_parsers(self, move_parser):
        move_parser.add_argument('move_origin', 
                                    action = 'store', 
                                    metavar = 'FILE', 
                                    nargs = 1, 
                                    type = str, 
                                    help = 'The origin file')
        move_parser.add_argument('move_destination', 
                                    action = 'store', 
                                    metavar = 'DESTINATION', 
                                    nargs = 1, 
                                    type = str, 
                                    help = 'The destination file')
        move_parser.add_argument('-h, --help', action = 'help', help = 'show this help message and exit')                                        
    
    def add_options(self, parser):
        options = parser.add_argument_group("JRT Drive Sync Options")

        options.add_argument('--clear-cache', 
                                action = 'store_true',
                                dest = 'clear_cache',
                                help = HELPS['clear-cache'])
        options.add_argument('-sc, --show-cache', 
                                action = 'store_true', 
                                dest = 'show_cache',
                                help = HELPS['show-cache'])
        options.add_argument('-h, --help', 
                                action = 'help', 
                                help = 'show this help message and exit')                                        

        