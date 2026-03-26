from pathlib import Path
from xaidar.treeUtils import sortPaths
from anytree import Node, RenderTree

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
    

    def viewTree(self, itemID = None, itemPath = None, startDepth = None, endDepth = None, root_name = None):

        if root_name:
            root_node = Node(root_name)
            dicTree = self.fileTree
        else:
            root_name = list(self.fileTree.keys())[0]
            root_node =  Node(root_name)
            dicTree = self.fileTree[root_name]

        if itemID:
            dir, node = viewIndexDict( dicTree, parent = root_node, indexLst = itemID )
        elif itemPath:
            dir, node = viewPathDict(dicTree, parent = root_node, path = itemPath )
        else:
            dir, node = dicTree, root_node
        
        viewTreeDict( dir, parent = node, targetDepth = endDepth, viewFiles = True  )
        for pre, fill, node in RenderTree(root_node):
            print("%s%s" % (pre, node.name))
        return 
    

def viewPathDict( d, parent = None, path = None):
    """
    Args:
    - path: 
        - If list(strings):
        - If empty list: passes input dictionary and None as output
    """
    if path == []:
        return [d,  parent]
    else:
        result = []
        for folderidx, (key, value) in enumerate( d.items() ):
            if key == path[0]:
                parentNode = Node( f"[{folderidx}] {key}", parent = parent)
                result.extend( viewPathDict( value, parent = parentNode, path = path[1:] ) )
    return result 


def viewIndexDict( d, parent = None, indexLst = None):
    """
    Goes through the 
    """
    if indexLst == []:
        return [d, parent]
    else:
        result = []
        for folderIdx, (key, value) in enumerate( d.items() ):
            if folderIdx == indexLst[0]:
                node = Node( f"[{folderIdx}] {key}", parent = parent)
                result.extend( viewIndexDict( value, node, indexLst = indexLst[1:]))
    return result




def viewTreeDict(d, parent=None, targetDepth = None, currentDepth = 0, viewFiles = True):
    if currentDepth == targetDepth:
        return
    
    currentDepth += 1

    for folderidx, (key, value ) in enumerate( d.items() ):
        if key == "Files":
            if viewFiles:
                # Attach files as leaf nodes
                for fileidx, file in enumerate(value):
                    Node(f"[{folderidx + fileidx }-F] {file}", parent=parent)
        else:
            node = Node( f"[{folderidx}] {key}", parent=parent)
            if isinstance(value, dict) and targetDepth == None:
                viewTreeDict(value, parent= node, currentDepth = currentDepth, 
                             targetDepth = targetDepth, viewFiles = viewFiles)
            elif isinstance(value, dict) and currentDepth < targetDepth :
                viewTreeDict(value, parent= node, currentDepth = currentDepth, 
                             targetDepth = targetDepth, viewFiles = viewFiles)
