from ruamel_yaml import YAML

from defines import DEFAULT_SETTINGS_FILE

from utils import load_settings

class ConfigManager:
    def __init__(self):
        self.settings = load_settings()

    def get_blacklist_enabled(self):
        return self.settings['blacklist-enabled']

    def get_whitelist_enabled(self):
        return self.settings['whitelist-enabled']

    def get_blacklist_files(self):
        return self.settings['blacklist-files']

    def get_whitelist_files(self):
        return self.settings['whitelist-files']

    def switch_blacklist_enabled(self):
        self.settings['blacklist-enabled'] = not self.settings['blacklist-enabled']
        if self.settings['blacklist-enabled'] and self.settings['whitelist-enabled']:
            print('Whitelist disabled')
            self.settings['whitelist-enabled'] = False
        with open(DEFAULT_SETTINGS_FILE, 'wb') as f:
            YAML().dump(self.settings, f)
        if self.settings['blacklist-enabled']:
            print('Blacklist enabled')
        else:
            print('Blacklist disabled')

    def switch_whitelist_enabled(self):
        self.settings['whitelist-enabled'] = not self.settings['whitelist-enabled']
        if self.settings['whitelist-enabled'] and self.settings['blacklist-enabled']:
            print('Blacklist disabled')
            self.settings['blacklist-enabled'] = False
        with open(DEFAULT_SETTINGS_FILE, 'wb') as f:
            YAML().dump(self.settings, f)
        if self.settings['whitelist-enabled']:
            print('Whitelist enabled')
        else:
            print('Whitelist disabled')

    def set_blacklist_files(self, blacklist_files):
        # Paths starting and ending with '/'
        for i, w in enumerate(blacklist_files):
            if w[0] != '/':
                blacklist_files[i] = '/' + w
            if w[-1] != '/':
                blacklist_files[i] = blacklist_files[i] + '/'

        self.settings['blacklist-files'] = blacklist_files

        with open(DEFAULT_SETTINGS_FILE, 'wb') as f:
            YAML().dump(self.settings, f)

    def set_whitelist_files(self, whitelist_files):
        # Paths starting and ending with '/'
        for i, w in enumerate(whitelist_files):
            if w[0] != '/':
                whitelist_files[i] = '/' + w
            if w[-1] != '/':
                whitelist_files[i] = whitelist_files[i] + '/'

        self.settings['whitelist-files'] = whitelist_files

        with open(DEFAULT_SETTINGS_FILE, 'wb') as f:
            YAML().dump(self.settings, f)

    def show_lists_status(self):
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

    # TODO: add the possibility to change the lists without having to completely
    # substitute it
