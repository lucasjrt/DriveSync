import os, pickle

class DriveFolder:
    def __init__(self, parent, id, name):
        self.parent = parent
        self.id = id
        self.name = name
        self.children = []

        if parent is not None:
            self.path = self.parent.getPath() + self.name + '/'
            self.level = parent.getLevel() + 1
        else:
            self.path = 'root/'
            self.level = 0
    
    def getParent(self):
        return self.parent
    
    def getId(self):
        return self.id
    
    def getName(self):
        return self.name
    
    def getChildren(self):
        return self.children

    def getLevel(self):
        return self.level

    def addChildren(self, children):
        self.children.append(children)

    def removeChildren(self, children):
        self.children.remove(children)
        
    def getPath(self):
        return self.path


class DriveTree:
    def __init__(self, id):
        self.root = DriveFolder(None, id, 'Google Drive root')
        self.root_id = id

    def getRoot(self):
        return self.root

    def findFolderInParent(self, parent, id, maxDeepness=None, currentDeepness=None):
        for f in parent.getChildren():
            if f.getId() == id:
                return f
            
            ret = None
            if maxDeepness is not None and currentDeepness is not None:
                if currentDeepness < maxDeepness:
                    ret = self.findFolderInParent(f, id, maxDeepness=maxDeepness, currentDeepness=currentDeepness + 1)
            else:
                ret = self.findFolderInParent(f, id)

            if ret:
                return ret
        return None

    def findFolder(self, id, deepness=None):
        if id == self.getRoot().getId():
            return self.root
        return self.findFolderInParent(self.root, id, currentDeepness= 0, maxDeepness=deepness)

    def addFolder(self, parent, id, name):
        if not parent:
            return None

        pnode = self.findFolder(parent.getId())

        if self.findFolderInParent(pnode, id):
            return None
        
        cnode = DriveFolder(parent, id, name)
        pnode.addChildren(cnode)

    def removeFolder(self, id):
        folder = self.findFolder(id)
        if folder:
            folder.getParent.removeChildren(folder)
    
    def loadFromFile(self, path):
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return self
                
    def saveToFile(self, path):
        if not os.path.exists(os.path.split(os.path.abspath(path))[0]):
            os.makedirs(os.path.split(os.path.abspath(path))[0])
        
        with open(path, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    def printFolder(self, folder, deepness = 0):
        if folder != self.root:
            print('|', end = '')
        print(2 * deepness * '-', folder.getName(), '\tid:', folder.getId(), sep = '')
        for child in folder.getChildren():
            self.printFolder(child, deepness+1)
        
    def printTree(self):
        self.printFolder(self.root)