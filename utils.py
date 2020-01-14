from datetime import datetime, timezone
import os
import dateutil.parser as parser
from dateutil.tz import tzlocal

from ruamel_yaml import YAML

from defines import DEFAULT_SETTINGS, DEFAULT_SETTINGS_FILE

def add_slashes(files):
    for i, w in enumerate(files):
        if w[0] != '/':
            files[i] = '/' + files[i]
        if w[-1] != '/':
            files[i] = files[i] + '/'

    for i in range(len(files)):
        pass
    return files

def bytes_to_human(bytes1, binary=False):
    magnitude = 0
    name = 'B'
    bytes1 = int(bytes1)
    if binary:
        unit = 1024
    else:
        unit = 1000

    while bytes1 > unit:
        magnitude += 1
        bytes1 /= unit

    if magnitude == 1:
        name = 'KB'
    elif magnitude == 2:
        name = 'MB'
    elif magnitude == 3:
        name = 'GB'
    elif magnitude == 4:
        name = 'TB'
    elif magnitude == 5:
        name = 'PB'
    else:
        if magnitude != 0:
            name = '10^' + str(3 * magnitude) + ' B'

    if binary and magnitude > 0:
        name = name[:-1] + 'i' + name[-1]
    return ('%.2f' % bytes1) + name

def delay_to_seconds(delay):
    total = 0
    if 'seconds' in delay:
        total += delay['seconds']
    if 'minutes' in delay:
        total += 60 * delay['minutes']
    if 'hours' in delay:
        total += 3600 * delay['hours']
    if 'days' in delay:
        total += 86400 * delay['days']
    return total

def load_settings():
    yaml = YAML()
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, 'r') as f:
            settings = dict(yaml.load(f))
            if settings['whitelist-enabled'] and settings['blacklist-enabled']:
                log('whitelist and blacklist cannot be enabled simultaneously')
                return None
            # Paths starting and ending with '/'
            for i, w in enumerate(settings['whitelist-files']):
                if w[0] != '/':
                    settings['whitelist-files'][i] = '/' + w
                if w[-1] != '/':
                    settings['whitelist-files'][i] = settings['whitelist-files'][i] + '/'

            for i, w in enumerate(settings['blacklist-files']):
                if w[0] != '/':
                    settings['blacklist-files'][i] = '/' + w
                if w[-1] != '/':
                    settings['blacklist-files'][i] = settings[i] + '/'

            return settings

    with open(DEFAULT_SETTINGS_FILE, 'w+') as f:
        yaml.dump(DEFAULT_SETTINGS, f)

    return DEFAULT_SETTINGS

def rfc3339_to_human(time_string):
    '''Converts RFC 3339 time format to better readable time format'''
    now = datetime.now()
    converting_time = parser.parse(time_string).astimezone(tzlocal())
    if now.date() != converting_time.date():
        return converting_time.date().strftime('%b %d, %Y')
    return converting_time.time().strftime('%I:%M %p')

# <GRAPHICAL OUTPUT>
def log(*message):
    print("[{}]: ".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print(*message, flush=True)

def warn(*message, verbose=False, sep=' '):
    if verbose:
        verb = '[WARNING]: '
    else:
        verb = ''
    print(Colors.YELLOW + verb + sep.join(map(str, message)) + Colors.RESET)

def error(*message, verbose=False, sep=' '):
    if verbose:
        verb = '[ERROR]: '
    else:
        verb = ''
    print(Colors.RED + verb + sep.join(map(str, message)) + Colors.RESET)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    YELLOW = '\033[93m'

    def disable(self):
        self.GREEN = ''
        self.RED = ''
        self.RESET = ''
        self.YELLOW = ''

    def enable(self):
        self.GREEN = '\033[92m'
        self.RED = '\033[91m'
        self.RESET = '\033[0m'
        self.YELLOW = '\033[93m'
#</GRAPHICAL OUTPUT>
