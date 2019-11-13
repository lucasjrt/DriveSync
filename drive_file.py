class DriveFile:
    def __init__(self, parent, file_struct):
        self.parent = parent
        self.id = file_struct['id']
        self.name = file_struct['title']
        self.children = []
        self.mime = file_struct['mimeType']
        self.used_quota = file_struct['quotaBytesUsed']
        if parent:
            self.level = parent.get_level() + 1
        else:
            self.level = 0

    def add_child(self, children):
        self.children.append(children)

    def get_children(self):
        return self.children

    def get_id(self):
        return self.id

    def get_level(self):
        return self.level

    def get_mime(self):
        return self.mime

    def get_name(self):
        return self.name

    def get_parent(self):
        return self.parent

    def get_path(self):
        if not self.parent:
            return '/'
        return self.parent.get_path() + self.name + '/'

    def get_used_quota(self, recursive=True):
        if recursive:
            quota = self.used_quota
            for child in self.children:
                quota += self.get_used_quota(child)
            return quota
        return self.used_quota

    def remove_child(self, children):
        self.children.remove(children)

    def set_name(self, name):
        self.name = name
