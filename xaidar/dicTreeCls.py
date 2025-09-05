from pathlib import Path
from xaidar.treeUtils import sortPaths

class sysDicTree():
    def __init__(self, folderTree = None, fileTree = None, lst_Paths = None):
        self.folderTree = folderTree
        self.fileTree = fileTree

        if lst_Paths and folderTree == None and fileTree == None :
            self._createTree( lst_Paths )
        
    @staticmethod
    def createdFolderDict( sortedPaths ):
        lst_lstsortedPaths = [ path.split( "/") for path in sortedPaths ]
        treeDict = {}
        for path in lst_lstsortedPaths:
            walkTree = treeDict
            pathLen = len( path)
            for idx, item in enumerate(path):
                if item not in walkTree.keys(): walkTree[item] = {}
                if idx == pathLen - 1: 
                    walkTree[item]["Files"] = [] 
                walkTree = walkTree[item]
        return treeDict

    @staticmethod
    def createFileDict(foldersTreeDict, filePaths):

        fileTreeDict = foldersTreeDict
        for filePath in filePaths:
            pathItems = filePath.split( "/")
            pathLen = len( pathItems)
            walkDict = fileTreeDict
            for idx, item in enumerate( pathItems ):
                if idx == pathLen - 1:
                    walkDict["Files"].append( item)
                else:
                    walkDict = walkDict[item]

        return fileTreeDict
    
    def _createTree( self, lst_Paths):
        sortedPaths = sortPaths( lst_Paths , filesPath = True)
        self.folderTree = sysDicTree.createdFolderDict( sortedPaths )
        self.fileTree = sysDicTree.createFileDict( self.folderTree, lst_Paths )
        return 
    
    @classmethod
    def createTree(cls, lst_Paths):
        """
        This method creates folderTreeDict and a fileTreeDict,
        from a given list of paths
        """
        sortedPaths = sortPaths( lst_Paths , filesPath = True)
        folderTreeDict = sysDicTree.createdFolderDict( sortedPaths )
        fileTreeDict = sysDicTree.createFileDict( folderTreeDict, lst_Paths )
        return cls( folderTree = folderTreeDict, fileTree = fileTreeDict)
    

