from xaidar.filesUtils import loadPickle
from xaidar.treeObj import viewSubtree, openFolder, openFolderwPath, cumulativeCount, findAllFolderFiles, createTree, sortPaths

class sysLisTree():
    def __init__(self, fileTree, folderTree, foldersCount, treeDepth ):
        self.fileTree = fileTree
        self.folderTree = folderTree
        self.foldersCount = foldersCount
        self.treeDepth = treeDepth
        self._foldersSumCount = None

    @property
    def foldersSumCount(self):
        if self._foldersSumCount == None:
            self._foldersSumCount = cumulativeCount( self.foldersCount )
        return self._foldersSumCount
    
    def viewTree( self, itemID = None, itemPath = None, startDepth = None, endDepth = None):
        startDepth = 1
        

        if itemID: endDepth = len(itemID) + endDepth
        elif itemPath: endDepth = len( itemPath.split("/") ) + endDepth
        else: endDepth = self.treeDepth + 1

        viewSubtree( self.fileTree, self.foldersCount, startDepth, endDepth, 
                    folderID = itemID, folderPath = itemPath )

    def openFolder( self, folderID = None, folderPath = None):
        if folderID:
            return openFolder( self.fileTree, self.foldersCount, folderID )
        elif folderPath:
            return openFolderwPath(self.fileTree, self.foldersCount, folderPath )
        else:
            raise Exception( "Missing Arguments" )

    def openLevel( self):
        pass

    def getSubTree(self, folderID = None, folderPath = None):
        """Create a subtree sysLisTree Object"""
        treeFile = createTree( findAllFolderFiles( self.fileTree, self.foldersCount, folderID ) )
        return sysLisTree( treeFile[0], treeFile[1], treeFile[-2], treeFile[2])

def loadTree( treeFilePath ):
    treeFile = loadPickle( treeFilePath )
    treeObj = sysLisTree( treeFile["fileTree"], treeFile["folderTree"], 
                        treeFile["foldersCount"], treeFile["folderTreeMaxDepth"])
    return treeObj

def createLisTree( lst_paths):
    treeFile = createTree( lst_paths )
    return sysLisTree( treeFile[0], treeFile[1], treeFile[-2], treeFile[2])