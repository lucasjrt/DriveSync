from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class DriveSession:
    
    def __init__(self, credentials_file):
        authToken = GoogleAuth()
        authToken.LoadCredentialsFile(credentials_file)
        if authToken.credentials is None:
            authToken.LocalWebserverAuth()
        elif authToken.access_token_expired:
            authToken.Refresh()
        else:
            authToken.Authorize()
        authToken.SaveCredentialsFile(credentials_file)
        self.drive = GoogleDrive(authToken)
    
    def getDrive(self):
        return self.drive