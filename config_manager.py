from ruamel_yaml import YAML

from defines import DEFAULT_SETTINGS_FILE

from utils import add_slashes, load_settings

class ConfigManager:
    def __init__(self):
        self.settings = load_settings()

    def append_blacklist_files(self, blacklist_files):
        self.settings['blacklist-files'] = \
            self.settings['blacklist-files'] + add_slashes(blacklist_files)
        print(len(blacklist_files), 'files added to blacklist')
        self.save_settings()

    def append_files_to_filter(self, files):
        files = add_slashes(files)
        if self.settings['blacklist-enabled']:
            filter_name = 'blacklist'
            self.settings['blacklist-files'] = self.settings['blacklist-files'] + files
        elif self.settings['whitelist-enabled']:
            filter_name = 'whitelist'
            self.settings['whitelist-files'] = self.settings['whitelist-files'] + files
        else:
            return None
        print(len(files), 'files added to', filter_name)
        self.save_settings()
        return True

    def append_whitelist_files(self, whitelist_files):
        self.settings['whitelist-files'] = \
            self.settings['whitelist-files'] + add_slashes(whitelist_files)
        self.save_settings()

    def get_blacklist_enabled(self):
        return self.settings['blacklist-enabled']

    def get_filter_enabled(self):
        if self.settings['blacklist-enabled'] or self.settings['whitelist-enabled']:
            return True
        return False

    def get_whitelist_enabled(self):
        return self.settings['whitelist-enabled']

    def get_blacklist_files(self):
        return self.settings['blacklist-files']

    def get_whitelist_files(self):
        return self.settings['whitelist-files']

    def remove_from_blacklist(self, files):
        total = 0
        for file1 in add_slashes(files):
            try:
                self.settings['blacklist-files'].remove(file1)
                total += 1
            except ValueError:
                print(file1[1:-1], 'not in blacklist')
        print(total, 'files removed from blacklist')
        self.save_settings()

    def remove_from_filter(self, files):
        files = add_slashes(files)
        total = 0
        if self.settings['blacklist-enabled']:
            filter_name = 'blacklist'
            for file1 in files:
                try:
                    self.settings['blacklist-files'].remove(file1)
                    total += 1
                except ValueError:
                    print(file1[1:-1], 'not in', filter_name)
        elif self.settings['whitelist-enabled']:
            filter_name = 'whitelist'
            for file1 in files:
                try:
                    self.settings['whitelist-enabled'].remove(file1)
                    total += 1
                except ValueError:
                    print(file1[1:-1], 'not in', filter_name)
        else:
            return None

        print(total, 'files removed from', filter_name)
        self.save_settings()
        return True

    def remove_from_whitelist(self, files):
        total = 0
        for file1 in add_slashes(files):
            try:
                self.settings['whitelist-files'].remove(file1)
                total += 1
            except ValueError:
                print(file1[1:-1], 'not in whitelist')
        print(total, 'files removed from whitelist')
        self.save_settings()

    def set_autostart(self, autostart):
        pass

    def set_sync_delay(self):
        pass

    def switch_blacklist_enabled(self):
        self.settings['blacklist-enabled'] = not self.settings['blacklist-enabled']
        if self.settings['blacklist-enabled'] and self.settings['whitelist-enabled']:
            print('Whitelist disabled')
            self.settings['whitelist-enabled'] = False
        if self.settings['blacklist-enabled']:
            print('Blacklist enabled')
        else:
            print('Blacklist disabled')
        self.save_settings()

    def switch_whitelist_enabled(self):
        self.settings['whitelist-enabled'] = not self.settings['whitelist-enabled']
        if self.settings['whitelist-enabled'] and self.settings['blacklist-enabled']:
            print('Blacklist disabled')
            self.settings['blacklist-enabled'] = False
        if self.settings['whitelist-enabled']:
            print('Whitelist enabled')
        else:
            print('Whitelist disabled')
        self.save_settings()

    def set_blacklist_files(self, blacklist_files):
        self.settings['blacklist-files'] = add_slashes(blacklist_files)
        self.save_settings()

    def set_whitelist_files(self, whitelist_files):
        self.settings['whitelist-files'] = add_slashes(whitelist_files)
        self.save_settings()

    def show_filter_status(self):
        if self.settings['whitelist-enabled']:
            print('Whitelist enabled:')
            if not self.settings['whitelist-files']:
                print('Empty whitelist')
                return
            for file1 in self.settings['whitelist-files']:
                print(file1[1:-1])
        elif self.settings['blacklist-enabled']:
            print('Blacklist enabled:')
            if not self.settings['blacklist-files']:
                print('Empty blacklist')
                return
            for file1 in self.settings['blacklist-files']:
                print(file1[1:-1])
        else:
            print('No filter set')

    def save_settings(self):
        with open(DEFAULT_SETTINGS_FILE, 'wb') as f:
            YAML().dump(self.settings, f)
