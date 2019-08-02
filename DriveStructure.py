class Folder:
    def __init(self, parent, id, name, data=None):
        self.children = []
        self.parent = parent
        self.id = id
        self.name = name
        self.data = data

class FileTree:
    def __init__(self):
        self.root_node = Folder(None, 'root', 'Google Drive')
