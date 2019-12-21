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
        subparsers.add_parser('pause', help=HELPS['pause'][0])

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
        # Just need drive session if performing any task with session
        if args.command is not None\
           or args.sync_cache\
           or args.sync_mirror:
            session = DriveSession(CREDENTIALS_FILE)
            print('Drive session started')
            root_file = session.get_service().files().get(fileId='root').execute()
            am = ActionManager(session.get_service(), root_file)
            sc = SyncController(session.get_service(), am, root_file)
        else:
            am = ActionManager(None, None)
            sc = SyncController(None, am, None)

        config_manager = ConfigManager()
        print('Settings loaded\n')

        #Operations
        if args.command == 'download':
            for file1 in args.download_files:
                am.download(file1, destination=args.download_destination)
        elif args.command == 'list':
            if args.list_file == 'root':
                am.list_files('root', args.list_trash)
            else:
                for file1 in args.list_file:
                    if len(args.list_file) > 1:
                        print(file1, ':', sep='')
                    am.list_files(file1)
        elif args.command == 'mkdir':
            for file1 in args.mkdir_file:
                am.mkdir(file1)
        elif args.command == 'move':
            am.move(args.move_origin, args.move_destination[0])
        elif args.command == 'rename':
            am.rename(args.rename_file, args.rename_name[0])
        elif args.command == 'remove':
            for file1 in args.rm_files:
                am.rm(file1, args.force_remove, args.trash_remove)
        elif args.command == 'restore':
            for file1 in args.restore_files:
                am.restore(file1)

        #Sync
        elif args.command == 'start':
            sc.start(args.start_target)
        elif args.command == 'stop':
            sc.stop()
        elif args.command == 'pause':
            sc.pause()

        #Options
        # -sc
        if args.show_cache:
            am.show_cache()
        # -cc
        if args.clear_cache:
            am.clear_cache()
        # -syc
        if args.sync_cache:
            am.sync_cache()
        # -sym
        if args.sync_mirror:
            sc.sync_mirror(filter_enabled=config_manager.get_filter_enabled())
        # -sm
        if args.show_mirror:
            sc.show_mirror()
        # -cm
        if args.clear_mirror:
            sc.clear_mirror()

        # filter settings

        # -b
        if args.add_blacklist is not None:
            if args.add_blacklist:
                config_manager.append_blacklist_files(args.add_blacklist)
                if not config_manager.get_blacklist_enabled():
                    config_manager.switch_blacklist_enabled()
            else:
                config_manager.switch_blacklist_enabled()
        # -w
        elif args.add_whitelist is not None:
            if args.add_whitelist:
                config_manager.append_whitelist_files(args.add_whitelist)
                if not config_manager.get_whitelist_enabled():
                    config_manager.switch_whitelist_enabled()
            else:
                config_manager.switch_whitelist_enabled()
        # -rb
        elif args.remove_blacklist is not None:
            config_manager.remove_from_blacklist(args.remove_blacklist)
        # -rw
        elif args.remove_whitelist is not None:
            config_manager.remove_from_whitelist(args.remove_whitelist)
        # -B
        elif args.set_blacklist is not None:
            config_manager.set_blacklist_files(args.set_blacklist)
            if not config_manager.get_blacklist_enabled():
                config_manager.switch_blacklist_enabled()
        # -W
        elif args.set_whitelist is not None:
            config_manager.set_whitelist_files(args.set_whitelist)
            if not config_manager.get_whitelist_enabled():
                config_manager.switch_whitelist_enabled()
        # -sf
        if args.show_filter:
            config_manager.show_filter_status()

        # -dc
        if args.download_cache:
            am.download_cache()

        # -dm
        if args.download_mirror:
            sc.download_mirror()

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
                           default='root',
                           metavar='FILE',
                           nargs='*',
                           help='File to be listed')
        group.add_argument('-t',
                           action='store_true',
                           dest='list_trash',
                           help=HELPS['list'][1])
        group.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_mkdir_parsers(self, mkdir_parser):
        mkdir_parser.add_argument('mkdir_file',
                                  metavar='FILE',
                                  nargs='*',
                                  help='Directory path')
        mkdir_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_move_parsers(self, move_parser):
        move_parser.add_argument('move_origin',
                                 metavar='FILE',
                                 help='The origin file')
        move_parser.add_argument('move_destination',
                                 metavar='DESTINATION',
                                 nargs=1,
                                 help='The destination file')
        move_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_rename_parsers(self, rename_parser):
        rename_parser.add_argument('rename_file',
                                   metavar='FILE',
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
        rm_parser.add_argument('-t',
                               action='store_true',
                               dest='trash_remove',
                               help=HELPS['remove'][2])
        rm_parser.add_argument('-h', action='help', help=HELPS['help'][0])

    def add_restore_parsers(self, restore_parser):
        restore_parser.add_argument('restore_files',
                                    metavar='FILE',
                                    nargs='*',
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
        options.add_argument('-cm',
                             action='store_true',
                             dest='clear_mirror',
                             help=HELPS['clear-mirror'][0])
        options.add_argument('-dc',
                             action='store_true',
                             dest='download_cache',
                             help=HELPS['download-cache'][0])
        options.add_argument('-dm',
                             action='store_true',
                             dest='download_mirror',
                             help=HELPS['download-mirror'][0])
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
