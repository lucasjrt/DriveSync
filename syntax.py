import argparse
import sys

from action_manager import ActionManager
from config_manager import ConfigManager
from defines import HELPS, CREDENTIALS_FILE, DEFAULT_DOWNLOAD_PATH, \
                    DEFAULT_DRIVE_SYNC_DIRECTORY
from drive_session import DriveSession
from sync_controller import SyncController

class SyntaxAnalyzer:
    def __init__(self):
        parser_description = 'Syncronizes a folder with a Google Drive account'
        parser_epilog = 'Please notice that this software is still under development'
        main_parser = argparse.ArgumentParser(prog='jds',
                                              description=parser_description,
                                              epilog=parser_epilog,
                                              add_help=False)
        subparsers = main_parser.add_subparsers(title='Commands', dest='command', metavar='')

        # Basic ops
        download_parser = subparsers.add_parser('download', help=HELPS['download'][0],
                                                add_help=False)
        list_parser = subparsers.add_parser('list', help=HELPS['list'][0], add_help=False)
        mkdir_parser = subparsers.add_parser('mkdir', help=HELPS['mkdir'][0], add_help=False)
        move_parser = subparsers.add_parser('move', help=HELPS['move'][0], add_help=False)
        rename_parser = subparsers.add_parser('rename', help=HELPS['rename'][0], add_help=False)
        rm_parser = subparsers.add_parser('remove', help=HELPS['remove'][0], add_help=False)
        restore_parser = subparsers.add_parser('restore', help=HELPS['restore'][0], add_help=False)

        # Sync ops
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
        # Just need drive session if performing any task
        if args.command is not None\
           or args.sync_cache\
           or args.sync_mirror:
            session = DriveSession(CREDENTIALS_FILE)
            print('Drive session started')
            am = ActionManager(session)
            sc = SyncController(session.drive)
        else:
            am = ActionManager(None)
            sc = SyncController(None)

        config_manager = ConfigManager()
        print('Settings loaded\n')

        #Operations
        if args.command == 'download':
            for file1 in args.download_files:
                am.download(file1, destination=args.download_destination)
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
            am.download_tree()
            #sync_controller.start(args.start_target)
        elif args.command == 'stop':
            sc.stop()

        #Options
        if args.show_cache:
            am.show_cache()
        if args.clear_cache:
            am.clear_cache()
        if args.sync_cache:
            am.sync_cache()
        if args.sync_mirror:
            sc.sync_mirror()
        if args.show_mirror:
            sc.show_mirror()
        if args.add_blacklist is not None:
            if args.add_blacklist:
                config_manager.append_blacklist_files(args.add_blacklist)
            else:
                config_manager.switch_blacklist_enabled()
        elif args.add_whitelist is not None:
            if args.add_whitelist:
                config_manager.append_whitelist_files(args.add_whitelist)
            else:
                config_manager.switch_whitelist_enabled()
        elif args.remove_blacklist is not None:
            config_manager.remove_from_blacklist(args.remove_blacklist)
        elif args.remove_whitelist is not None:
            config_manager.remove_from_whitelist(args.remove_whitelist)
        elif args.set_blacklist is not None:
            config_manager.set_blacklist_files(args.set_blacklist)
        elif args.set_whitelist is not None:
            if args.set_whitelist:
                config_manager.set_whitelist_files(args.set_whitelist)
                if not config_manager.get_whitelist_enabled():
                    config_manager.switch_whitelist_enabled()
            else:
                config_manager.switch_whitelist_enabled()
        elif args.show_filter:
            config_manager.show_filter_status()

    def add_download_parser(self, download_parser):
        download_parser.add_argument('download_files',
                                     metavar='FILE',
                                     nargs='+',
                                     help='File to be downloaded')
        download_parser.add_argument('-o',
                                     default=DEFAULT_DOWNLOAD_PATH,
                                     dest='download_destination',
                                     metavar='DESTINATION',
                                     type=str,
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
        mutex = options.add_mutually_exclusive_group()

        mutex.add_argument('-B',
                           dest='set_blacklist',
                           metavar='FILE',
                           nargs='*',
                           type=str,
                           help=HELPS['set-blacklist'][0])
        mutex.add_argument('-b',
                           dest='add_blacklist',
                           metavar='FILE',
                           nargs='*',
                           type=str,
                           help=HELPS['add-blacklist'][0])
        options.add_argument('-cc',
                             action='store_true',
                             dest='clear_cache',
                             help=HELPS['clear-cache'][0])
        mutex.add_argument('-rb',
                           dest='remove_blacklist',
                           metavar='FILE',
                           nargs='+',
                           type=str,
                           help=HELPS['remove-blacklist'][0])
        mutex.add_argument('-rw',
                           dest='remove_whitelist',
                           metavar='FILE',
                           nargs='+',
                           type=str,
                           help=HELPS['remove-whitelist'][0])
        options.add_argument('-sf',
                             action='store_true',
                             dest='show_filter',
                             help=HELPS['show-filter'][0])
        options.add_argument('-sc',
                             action='store_true',
                             dest='show_cache',
                             help=HELPS['show-cache'][0])
        options.add_argument('-sm',
                             action='store_true',
                             dest='show_mirror',
                             help=HELPS['show-mirror'][0])
        options.add_argument('-syc',
                             action='store_true',
                             dest='sync_cache',
                             help=HELPS['sync-cache'][0])
        options.add_argument('-sym',
                             action='store_true',
                             dest='sync_mirror',
                             help=HELPS['sync-mirror'][0])
        mutex.add_argument('-W',
                           dest='set_whitelist',
                           metavar='FILE',
                           nargs='*',
                           type=str,
                           help=HELPS['set-whitelist'][0])
        mutex.add_argument('-w',
                           dest='add_whitelist',
                           metavar='FILE',
                           nargs='*',
                           type=str,
                           help=HELPS['add-whitelist'][0])
        options.add_argument('-h', action='help', help=HELPS['help'][0])
