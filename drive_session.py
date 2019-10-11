from httplib2 import ServerNotFoundError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from action_manager import ActionManager
from drive_file import DriveTree

SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveSession:

    def __init__(self, credentials_file, is_sync=False):
        try:
            print('Starting session')
            auth_token = GoogleAuth()
            auth_token.LoadCredentialsFile(credentials_file)
            self.auth_token = auth_token
            if auth_token.credentials is None:
                print('Requiring token')
                auth_token.LocalWebserverAuth()
            elif auth_token.access_token_expired:
                print('Refreshing token')
                auth_token.Refresh()
            else:
                print('Valid token found')
                auth_token.Authorize()
        except ServerNotFoundError:
            print('Error on internet connection')
            exit()
        auth_token.SaveCredentialsFile(credentials_file)

        print('Authenticating')
        self.drive = GoogleDrive(auth_token)
        self.service = auth_token.service
        print('Session started')

        root_id = self.drive.GetAbout()['rootFolderId']
        if not is_sync:
            self.action_manager = ActionManager(self.drive, self.service,
                                                DriveTree(root_id, self.drive).load_from_file())

    def get_drive(self):
        return self.drive

    def get_service(self):
        return self.service

    def get_action_manager(self):
        return self.action_manager
