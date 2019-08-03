import os, pickle

class DriveFolder:
    def __init__(self, parent, id, name):
        self.parent = parent
        self.id = id
        self.name = name
        self.children = []
        if parent:
            self.level = parent.getLevel() + 1
        else:
            self.level = 0
    
    def getParent(self):
        return self.parent
    
    def getId(self):
        return self.id
    
    def getName(self):
        return self.name
    
    def getChildren(self):
        return self.children

    def addChildren(self, children):
        self.children.append(children)

    def removeChildren(self, children):
        self.children.remove(children)

    def getLevel(self):
        return self.level

class DriveTree:
    def __init__(self, id, drive):
        self.root = DriveFolder(None, id, 'My drive')
        self.drive = drive

    def getRoot(self):
        return self.root

    def findFileInParent(self, parent, id):
        for f in parent.getChildren():
            if f.getId() == id:
                return f
            
            # ret = self.findFileInParent(f, id)

            # if ret:
            #     return ret
        return None

    def findFile(self, id, depth=None):
        if id == self.getRoot().getId():
           return self.root
        return self.findFileInParent(self.root, id)

    def addFile(self, parent, id, name):
        if not parent:
            return None

        # pnode = self.findFile(parent.getId())

        # if self.findFileInParent(pnode, id):
        # if self.findFileInParent(parent, id):
        #     return None
        
        cnode = DriveFolder(parent, id, name)
        # pnode.addChildren(cnode)
        parent.addChildren(cnode)

    def removeFolder(self, id):
        folder = self.findFile(id)
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

    def getClosestNodeFromPath(self, path):
        path_list = [p for p in path.split('/') if len(p) > 0 and p != 'root']
        current_node = self.root
        depth = 0
        for path in path_list:
            last_depth = depth
            for node in current_node.getChildren():
                if path == node.getName():
                    current_node = node
                    depth += 1
                    break
            if depth == last_depth:
                break
        return current_node, depth == len(path_list), '/'.join(path_list[depth:])
        
    def loadPath(self, path):
        closest_node, found, remaining_path = self.getClosestNodeFromPath(path)
        if found:
             return
             
        path_list = [p for p in remaining_path.split('/') if len(p) > 0 and p != 'root']

        for path in path_list:
                last = closest_node
                file_list = self.drive.ListFile({'q': "'%s' in parents and trashed = false" % closest_node.getId()}).GetList()
                for file1 in file_list:
                    if not self.findFileInParent(closest_node, file1['id']):
                        self.addFile(closest_node, file1['id'], file1['title'])
                    if file1['title'] == path:
                        closest_node = self.findFileInParent(closest_node, file1['id'])
                        break
                if last == closest_node:
                    return None
        
        return closest_node

    def printFolder(self, folder):
        depth = folder.getLevel()
        if folder != self.root:
            print('|', end = '')
        print(2 * depth * '-', folder.getName(), '\tid:', folder.getId(), sep = '')
        for child in folder.getChildren():
            self.printFolder(child)

    def printTree(self):
        self.printFolder(self.root)
