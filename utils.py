import os
import sys

from datetime import datetime
from ruamel_yaml import YAML

from defines import DEFAULT_SETTINGS, DEFAULT_SETTINGS_FILE

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
            if settings['whitelist-enabled']:
                # Starting path with '/'
                settings['whitelist-files'] = \
                    [w.replace(w, '/' + w) for w in settings['whitelist-files'] if w[0] != '/']

                # Closing path with '/'
                settings['whitelist-files'] = \
                    [w.replace(w, w + '/') for w in settings['whitelist-files'] if w[-1] != '/']
            elif settings['blacklist-enabled']:
                # Starting path with '/'
                settings['blacklist-files'] = \
                    [w.replace(w, '/' + w) for w in settings['blacklist-files'] if w[0] != '/']

                # Closing path with '/'
                settings['blacklist-files'] = \
                    [w.replace(w, w + '/') for w in settings['blacklist-files'] if w[-1] != '/']
            return settings

    with open(DEFAULT_SETTINGS_FILE, 'w+') as f:
        yaml.dump(DEFAULT_SETTINGS, f)
        return DEFAULT_SETTINGS

def log(*message):
    print("[", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "]: ", *message, sep='')
    sys.stdout.flush()
