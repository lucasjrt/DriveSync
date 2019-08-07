import argparse
import sys
from defines import HELPS, CREDENTIALS_FILE, DEFAULT_DOWNLOAD_PATH, DEFAULT_DRIVE_SYNC_DIRECTORY
from drive_session import DriveSession

class SyntaxAnalyzer:
    def __init__(self):
        parser_description = 'Syncronizes a folder with a Google Drive account'
        parser_epilog = 'Please notice that this software is still under development'
        main_parser = argparse.ArgumentParser(prog='jds',
                                              description=parser_description,
                                              epilog=parser_epilog,
                                              add_help=False)
        subparsers = main_parser.add_subparsers(title='Commands', dest='command', metavar='')

        download_parser = subparsers.add_parser('download', help=HELPS['download'][0],
                                                add_help=False)
        list_parser = subparsers.add_parser('list', help=HELPS['list'][0], add_help=False)
        mkdir_parser = subparsers.add_parser('mkdir', help=HELPS['mkdir'][0], add_help=False)
        move_parser = subparsers.add_parser('move', help=HELPS['move'][0], add_help=False)
        rename_parser = subparsers.add_parser('rename', help=HELPS['rename'][0], add_help=False)
        rm_parser = subparsers.add_parser('remove', help=HELPS['remove'][0], add_help=False)
        restore_parser = subparsers.add_parser('restore', help=HELPS['restore'][0], add_help=False)

        start_parser = subparsers.add_parser('start', help=HELPS['start'][0], add_help=False)
        subparsers.add_parser('stop', help=HELPS['stop'][0])

        self.add_download_parser(download_parser)
        self.add_list_parsers(list_parser)
        self.add_move_parsers(move_parser)
        self.add_mkdir_parsers(mkdir_parser)
        self.add_rename_parsers(rename_parser)
        self.add_rm_parsers(rm_parser)
        self.add_restore_parsers(restore_parser)

        self.add_start_parsers(start_parser)

        self.add_options(main_parser)

        if len(sys.argv) == 1:
            print(main_parser.format_help())
            return

        args = main_parser.parse_args()
        session = DriveSession(CREDENTIALS_FILE)
        am = session.get_action_manager()
        sync_controller = session.get_sync_controller()

        #Operations
        if args.command == 'download':
            am.download(args.download_files, destination=args.download_destination[0])
        elif args.command == 'list':
            am.list_files(args.list_file, args.list_trash)
        elif args.command == 'mkdir':
            am.mkdir(args.mkdir_file[0])
        elif args.command == 'move':
            am.move(args.move_origin[0], args.move_destination[0])
        elif args.command == 'rename':
            am.rename(args.rename_file[0], args.rename_name[0])
        elif args.command == 'remove':
            am.rm(args.rm_files, args.force_remove)
        elif args.command == 'restore':
            am.restore(args.restore_files)

        #Sync
        elif args.command == 'start':
            sync_controller.start(args.start_target)
        elif args.command == 'stop':
            sync_controller.stop()

        #Options
        if args.show_cache:
            am.get_tree().print_tree()
        if args.clear_cache:
            am.clear_cache()

    def add_download_parser(self, download_parser):
        download_parser.add_argument('download_files',
                                     metavar='FILE',
                                     nargs='+',
                                     help='File to be downloaded')
        download_parser.add_argument('-o',
                                     default=DEFAULT_DOWNLOAD_PATH,
                                     dest='download_destination',
                                     metavar='DESTINATION',
                                     nargs=1,
                                     help='Location to where the downloaded file will be save')
        download_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_list_parsers(self, list_parser):
        group = list_parser.add_mutually_exclusive_group()
        group.add_argument('list_file',
                           const='root',
                           default='root',
                           metavar='FILE',
                           nargs='?',
                           help='File to be listed')
        group.add_argument('-t',
                           action='store_true',
                           dest='list_trash',
                           help=HELPS['list'][1])
        group.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_mkdir_parsers(self, mkdir_parser):
        mkdir_parser.add_argument('mkdir_file',
                                  metavar='FILE',
                                  nargs=1,
                                  help='Directory path')
        mkdir_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_move_parsers(self, move_parser):
        move_parser.add_argument('move_origin',
                                 metavar='FILE',
                                 nargs=1,
                                 help='The origin file')
        move_parser.add_argument('move_destination',
                                 metavar='DESTINATION',
                                 nargs=1,
                                 help='The destination file')
        move_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_rename_parsers(self, rename_parser):
        rename_parser.add_argument('rename_file',
                                   metavar='FILE',
                                   nargs=1,
                                   help='File to be renamed')

        rename_parser.add_argument('rename_name',
                                   metavar='NAME',
                                   nargs=1,
                                   help='New name')
        rename_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_rm_parsers(self, rm_parser):
        rm_parser.add_argument('rm_files',
                               metavar='FILE',
                               nargs='+',
                               help='The file to be moved to trash')

        rm_parser.add_argument('-f',
                               action='store_true',
                               dest='force_remove',
                               help=HELPS['remove'][1])
        rm_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_restore_parsers(self, restore_parser):
        restore_parser.add_argument('restore_files',
                                    metavar='FILE',
                                    nargs='+',
                                    help='File(s) to be restored from trash')
        restore_parser.add_argument('-h', action='help', help=HELPS['help'][0])

############################################Sync options############################################

    def add_start_parsers(self, start_parser):
        start_parser.add_argument('-t',
                                  default=DEFAULT_DRIVE_SYNC_DIRECTORY,
                                  dest='start_target',
                                  metavar='TARGET',
                                  nargs='?',
                                  help='The target folder to synchronize with drive (Default:' +
                                  DEFAULT_DRIVE_SYNC_DIRECTORY + ')')
        start_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_options(self, parser):
        options = parser.add_argument_group("JRT Drive Sync Options")

        options.add_argument('-cc',
                             action='store_true',
                             dest='clear_cache',
                             help=HELPS['clear-cache'][0])
        options.add_argument('-sc',
                             action='store_true',
                             dest='show_cache',
                             help=HELPS['show-cache'][0])
        options.add_argument('-h', action='help', help=HELPS['help'][0])
