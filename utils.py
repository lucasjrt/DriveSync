import sys
from datetime import datetime

def log(*message):
    print("[", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "]: ", *message, sep='')
    sys.stdout.flush()
