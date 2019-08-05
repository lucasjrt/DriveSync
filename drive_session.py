from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from action_manager import ActionManager
from drive_file import DriveTree

SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveSession:

    def __init__(self, credentials_file):
        auth_token = GoogleAuth()
        auth_token.LoadCredentialsFile(credentials_file)
        if auth_token.credentials is None:
            auth_token.LocalWebserverAuth()
        elif auth_token.access_token_expired:
            auth_token.Refresh()
        else:
            auth_token.Authorize()
        auth_token.SaveCredentialsFile(credentials_file)

        self.drive = GoogleDrive(auth_token)
        self.service = auth_token.service

        root_id = self.drive.GetAbout()['rootFolderId']
        self.action_manager = ActionManager(self.drive, self.service,
                                            DriveTree(root_id, self.drive).load_from_file())

    def get_drive(self):
        return self.drive

    def get_service(self):
        return self.service

    def get_action_manager(self):
        return self.action_manager
