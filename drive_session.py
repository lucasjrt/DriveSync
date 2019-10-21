from httplib2 import ServerNotFoundError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveSession:

    def __init__(self, credentials_file):
        try:
            print('Starting session')
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile(credentials_file)
            self.gauth = gauth
            print('Requesting authorization in drive')
            if gauth.credentials is None:
                print('Requesting access permission')
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                print('Refreshing token')
                gauth.Refresh()
            else:
                gauth.Authorize()
        except ServerNotFoundError:
            print('No internet connection')
            exit(-1)
        gauth.SaveCredentialsFile(credentials_file)

        self.drive = GoogleDrive(gauth)
        self.service = gauth.service

    def get_drive(self):
        return self.drive

    def get_storage(self):
        info = self.drive.GetAbout()
        storage = {'total': info['quotaBytesTotal'],
                   'used': info['quotaBytesUsedAggregate'],
                   'trash': info['quotaBytesUsedInTrash']}
        return storage

    def get_service(self):
        return self.service
