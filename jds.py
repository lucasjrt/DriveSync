import os
import sys
from syntax import SyntaxAnalyzer
from defines import APP_PATH

def main():
    sys.path.insert(0, APP_PATH)
    os.chdir(APP_PATH)
    SyntaxAnalyzer()

if __name__ == "__main__":
    main()
