import os
import sys
import pickle
from collections import defaultdict
import re
from copy import deepcopy
from anytree import Node, RenderTree

from xaidar.filesUtils import getPklFileNames, loadPickle
### Sort the list of paths into hierarchical alphabetical order

def sortPaths(pathsLst):
    """
    Sorts a list of paths in a hierarchical manner, ensuring that parent directories are ordered first before their subdirectories.
    Args:
    - pathsLst (list): Each element corresponds to a string path of format "root/Dir1/SubDir2/...".
    Note:
    Make sure the formating of each path is so that it is divided by "/" and that there are no "/" at the beginning or end
    """

    # Split into steps of the path
    foldersLst = [ ( len( path.split("/")) , path.split("/") ) for path in pathsLst ]

    # Sort by size so that the larger paths come first
    foldersLst.sort( reverse = True, key= lambda x: x[0])

    # Get a Dict with the sizes of paths and number of corresponding paths in descending order
    # to match 
    foldersSizes = [ path[0] for path in foldersLst ]
    foldersUniqSizes = list(set(foldersSizes))
    foldersUniqSizes.sort(reverse=True)
    foldersSizesDic = { size : foldersSizes.count( size ) for size in foldersUniqSizes }
    foldersLst = [ path[1] for path in foldersLst ]


    largestPath = list( foldersSizesDic.keys() )[ 0 ]
    orderedFolderLst = foldersLst
    currentNumberofPaths = 0 
    lstAllPathSizes = list( foldersSizesDic.keys() )
    for size in range( largestPath, 0, -1 ):
        if size in lstAllPathSizes:
            currentNumberofPaths += foldersSizesDic[size] 

        startSubList = orderedFolderLst[ : currentNumberofPaths]
        endSubList = orderedFolderLst[currentNumberofPaths: ]

        startSubList.sort(key = lambda x: x[ size - 1] )

        orderedFolderLst = startSubList + endSubList

    orderedFolderLst = [  "/".join( path ) for path in orderedFolderLst ]

    return orderedFolderLst


### Ways Open a nested list

# Iteratively
def get_item_depth( lst, depth):
    """
    Gets all the items in a specific tree depth
    Args:
    - Depth (int): Represents the non-zero indexed level
    """
    for _ in range( depth - 1): # -1 bc it already start at level one, and at the return it opens one extra level
        lst = lst[-1]
    return lst[:-1]

# Recursively
def openNestedLst(lst, maxDepth , depth = 0  ):
    """
    Tool used to open nested lists in the form: [ ..., [nested list] ]
    """
    depth += 1
    if depth == maxDepth:
        return lst[:-1]
    return openNestedLst( lst[-1], maxDepth, depth = depth )

# Uses get_item_depth
def pinchLevel(tree, depth : int, flat = False ):
    """
    Get the names of all the folders and files present in a specific level of the file system
    Args:
    - tree:
    - depth: Level to extract folders from
    - flat (bool): If True - gives you a list of all folders, If False - gives you a list of lists, each list
                    representing a folder from the preceding level
    Note:
    - This is not zero indexed, to the first depth = 1, which represents the root, or the first tree[:-1] without going down a level (tree[-1])
    """
    def flatten_list( lstLst):
        """Flatten a list of lists"""
        return [item for lst in lstLst for item in lst ]

    if flat: return flatten_list( get_item_depth( tree, depth  ) )
    else: return get_item_depth( tree, depth  ) 






##############################################

## Create File System Nested Lists
# def createFolderTree(lstFolderPaths, delimiter = "/")
def createFolderTree( orderedFolderPathS, delimiter = "/"): #
    """
    Args:
    - treeMaxDepth: Max number of directories to tresspass to reach a file
    """
    folderTree = [ [], [ [] ] ] 
    treeMaxDepth = 0
    folderIDS = []
    for path in orderedFolderPathS:
        parts = path.split( delimiter)   #  "root/subDir11/subDir21".split("/")
        if len( parts ) > treeMaxDepth: # Get Tree Size Dynamically
            treeMaxDepth = len( parts )

        tree = folderTree
        folderID = []
        for part in  parts :     
            if part not in tree[ -2 ]:  # Since it is in alphabetical order, it will either exist in the last folder or a new folder must be created
                tree[-2].append( part)
                tree[ -1 ].insert( -1, [] )
                if tree[ -1 ][-1] == []: # This means that this level ( tree[-1] )have not yet been reached
                    tree[ -1 ][-1].append( [] ) # Dynamically increase the tree
            else: pass
            folderID.append( len( tree[-2] ) - 1 )
            tree =  tree[ -1 ] # Peel one layer of the nested list
        
        folderIDS.append( folderID ) #( folderID ) -> accounts for root | (folderID[1:]) -> Does not take root representation

    return folderTree, treeMaxDepth, folderIDS

def countFolders(folderTree, folderTreeMaxDepth):
    """
    Outputs a count of how many subfolders exist for each folder at each level
    - I.e. [ [1] , [2], [1, 1] , ... ] -> The supraroot has 1 folder (root), which has 2 folders with one folder each
    """
    foldersCount = []

    tree = folderTree
    for _ in range( folderTreeMaxDepth + 1 ):
        foldersCount.append( [ len( lst) for lst in tree[ :-1] ] )
        tree = tree[-1] # Peel one layer of the nested list
    return foldersCount # foldersCount[1:] -> does NOT take the root representation

def getGamma(foldersCount, folderID):
    """
    Get Gamma Based on the folderID, where 1st index represents NOT the root but the first subfolder
    Args:
    - foldersCount
    - folderID: 
    """
    folderID = folderID #[1:]-> does not take the root representation # [] = 0 (supra root), [0] = 0 (root), [0, ]
    gamma = 0
    for count, ID in zip( foldersCount, folderID):
        gamma = sum( count[ : gamma] ) + ID
    return gamma
    

def createFileTree( lstOfPath, orderedFoldersLst, folderTree, folderIDS, foldersCount ):
    """
    Args:
    - lstOfPath (list): list of path strings with the right formatting
    - orderedFoldersLst (list): list of folders ordered in alphabetical order hierarchically
    - folderTree( list ): Nested list representing a file system expressed in the lstOfPaths
    - folderIDS ( list ): ID locating each folder in the file system (w/o root representation )
    - foldersCount ( list): List represent the number of folders found inside each parent folder for each level

    """
    # Get a sorted folderID : list( Files )  Dictionary
    folderFileDict = defaultdict( list )
        # Get Folder Path for each File:
    for folderPath, fileName in zip(  [ "/".join( path.split("/")[:-1])  for path in lstOfPath], [path.split("/")[-1] for path in lstOfPath ] ):
        folderFileDict[ folderPath].append( fileName)
        # Sort the files according to an already sorted orderedFolderLst
    sortedFolderFileDict = { key: folderFileDict[key] for key in orderedFoldersLst }
        # Assign the Folder IDs to the ordered Folders with corresponding files
    folderIDFileDict = { tuple( ID ) : path for ID, path in zip( folderIDS, sortedFolderFileDict.values( ) )}

    fileTree = deepcopy( folderTree )
    for folderID, fileNameS in folderIDFileDict.items():
        gamma = getGamma( foldersCount, folderID ) #[1:] )
        for fileName in fileNameS:
            pinchLevel( fileTree, len(folderID) + 1 , flat = False )[gamma].append( fileName ) # level + 1

    return fileTree

def createTree(lstOfPathS):
    """
    Takes a list of paths as input and outputs a nested list representing a file system tree structure
    both for only the folders and for the folders and files.
    Args:
    - lstOfPath :
    """
    foldersLst = list( set( [ "/".join( path.split("/")[ :-1 ] ) for path in lstOfPathS ] ) ) 
    orderedFolderLst = sortPaths( foldersLst )
    # print("success")
    folderTree, folderTreeMaxDepth, foldersIDS = createFolderTree( orderedFolderLst ) # 1 min
    # print("success")
    foldersCount = countFolders(  folderTree, folderTreeMaxDepth ) 
    # print("success")
    fileTree = createFileTree(lstOfPathS, orderedFolderLst, folderTree, foldersIDS, foldersCount) # 7 min 
    # print("success")
    return fileTree, folderTree, folderTreeMaxDepth,  foldersIDS, foldersCount, foldersLst


def convertPathstoTree(pklDir: list, saveDir):
    """
    Takes a directory of pkl files with a list of paths in each, and converts and saves 
    each to a dictionary with tree metrics (file tree, foldersCount, etc...)
    Args:
    - pklDir ( list ): 
    - saveDir ( path ): path to a 
    """ 
    projFileNames = getPklFileNames(  [ pklDir ]  ) # Output dict with "data", and list of .pkl files
    root = list( projFileNames.keys() )[0]
    for projectName in projFileNames[ root ]: 
        print( projectName)
        projPathsLst = loadPickle( os.path.join( pklDir, projectName) )
        fileTree, folderTree, folderTreeMaxDepth,  foldersIDS, foldersCount, foldersLst = createTree( projPathsLst )


        keysLst = ['fileTree', 'folderTree', 'folderTreeMaxDepth', ' foldersIDS', 'foldersCount', 'foldersLst']
        objLst = [ fileTree, folderTree, folderTreeMaxDepth,  foldersIDS, foldersCount, foldersLst ]
        treeDic = { key: obj for key, obj in zip( keysLst, objLst ) }

        with open( os.path.join( saveDir, f"tree_{projectName}.pkl"), "wb") as f:
            pickle.dump( treeDic, f )
        print(f"Saved {projectName}")
###################################################

# Extra Tools


def getGammawPath(path, tree, foldersCount, ):

    pathParts = path.split("/") 

    pointer = {"gamma": 0, "id": 0 }  # gamma represents the index location of which supra folder does the target folder live in | id represents the index of where the folder is within the supra folder

    for levelFoldersCount, currentDir in zip( foldersCount,  pathParts ):
        
        if currentDir in tree[:-1][ pointer["gamma"] ]:
            pointer["id"] = tree[:-1][ pointer["gamma"] ].index( currentDir ) # Find id for current folder
            pointer["gamma"] = sum( levelFoldersCount[ : pointer[ "gamma" ]  ] ) + pointer["id"] # Update gamma for next level based on foldersCount
            
            tree = tree[-1]
        else:
            print( f"Could not find \"{currentDir}\" directory.")
            
            return None


    return  pointer["gamma"] 

def convertIDtoPath( tree, foldersCount, ID  ):
    """
    This takes any  folder or file ID (where first element represents root - 0), 
    and outputs the path (which matches the object key)
    """
    path = ""
    gamma = 0
    for currentLevelID, currentLevelCount in zip( ID, foldersCount):

        path = path + "/" + tree[:-1][gamma][ currentLevelID ]
        gamma = sum( currentLevelCount[ : gamma] ) + currentLevelID
        tree = tree[-1]

    return path[1:] # remove initial "/"

def convertPathtoID(tree, foldersCount, path):

    pathParts = path.split("/") 

    pointer = {"gamma": 0, "id": 0 }  # gamma represents the index location of which supra folder does the target folder live in | id represents the index of where the folder is within the supra folder
    folderID = [ ]

    for levelFoldersCount, currentDir in zip( foldersCount,  pathParts ):
        
        if currentDir in tree[:-1][ pointer["gamma"] ]:
            pointer["id"] = tree[:-1][ pointer["gamma"] ].index( currentDir ) # Find id for current folder
            pointer["gamma"] = sum( levelFoldersCount[ : pointer[ "gamma" ]  ] ) + pointer["id"] # Update gamma for next level based on foldersCount
            
            tree = tree[-1]
            folderID.append( pointer["id"] )

        else:
            print( f"Could not find \"{currentDir}\" directory.")
            
            return None

    return folderID

################

# Traverse Tree
def openFolder( treeLst, foldersCount, folderID: list ):
    """
    Visualize folder content based on folder ID.
    FolderID [0] represents the content of the root folder.
    Args:
    - treeLst
    - foldersCount
    - folderID: The first index represents opening the contents of root, so it should always be 0 [0, ... ]
    Notes:
    - Works with both file and folder Trees
    """
    targetDepth = len( folderID ) + 1 # bc [] shows the root, and [0] opens root and shows its content
    directory = pinchLevel( treeLst, targetDepth, flat = False)
    gamma = getGamma( foldersCount, folderID) 
    return directory[gamma]

def openFolderwPath(tree, foldersCount, path):

    pathParts = path.split("/") 

    pointer = {"gamma": 0, "id": 0 }  # gamma represents the index location of which supra folder does the target folder live in | id represents the index of where the folder is within the supra folder

    for levelFoldersCount, currentDir in zip( foldersCount,  pathParts ):
        
        if currentDir in tree[:-1][ pointer["gamma"] ]:
            pointer["id"] = tree[:-1][ pointer["gamma"] ].index( currentDir ) # Find id for current folder
            pointer["gamma"] = sum( levelFoldersCount[ : pointer[ "gamma" ]  ] ) + pointer["id"] # Update gamma for next level based on foldersCount
            
            tree = tree[-1]
        else:
            print( f"Could not find \"{currentDir}\" directory.")
            
            return None

    return tree[ pointer["gamma"] ] 



#########################

# Visualize the Trees
def viewLstPathS(paths, maxlevel = 10):
    """
    By chatGPT
    Allows to visualize the tree-like structure of a file system based on a list of paths.
    """
    # Root node
    root = Node("root")

    # List of paths (simulating file system paths)
    # paths = lstObjectKeys

    # Dictionary to track created nodes
    nodes = {"": root}

    # Loop through paths to build the tree
    for path in paths:
        parts = path.split("/")
        current_path = ""

        for part in parts:
            current_path = f"{current_path}/{part}".strip("/")
            if current_path not in nodes:
                parent_path = "/".join(current_path.split("/")[:-1])
                nodes[current_path] = Node(part, parent=nodes[parent_path])

    # Display tree
    for pre, fill, node in RenderTree(root, maxlevel = maxlevel): 
        print(f"{pre}{node.name}")

def visualizeTree(tree, depth = 0, minMaxDepth = (0, 20) ):
    """
    Tool used to open nested lists in the form: [ ..., [nested list] ]
    Args:
    - tree
    - depth: This is an internal variable that changes throughout the recursions.
    - minMaxDepth (tuple): [0] - Minimum Depth to print, [1] - maximum depth to output
    """
    depth += 1
    if len( tree ) <= 0 or depth > minMaxDepth[1] :
        return None
    if minMaxDepth[0] <= depth <= minMaxDepth[1]: print( f"  {depth}\t| {tree[:-1]}" )
    return visualizeTree( tree[-1], depth = depth, minMaxDepth = minMaxDepth )


def viewTree(tree, treeDepth, foldersCount, viewFiles = True ):
    """
    Get a tree diagram
    Args:
    - Tree depth: can select how deep to open the tree
    - viewFiles: can select whether to see files or only the folders
    """
    rootName = pinchLevel( tree,  1, flat = False)[0][0]

    root = Node(rootName)
    lstParentNodes = [ root ]
    foldersCount = [ None ] + [None] + foldersCount # So that can use level to access the right 
    for level in range( treeDepth - 1 ):
        level += 2      # Level starts at 2 and ends at treeDepth + 2 - 1 (not included in range [) ]) - 1 (inside range)
        childNodes = []
        fileNodes = []
        for parentFolderID, parentFolder in enumerate( pinchLevel( tree,  level, flat = False) ):                    
            for childFolderIdx, childFolder in enumerate( parentFolder):
                if childFolderIdx <  foldersCount[ level ][parentFolderID]:
                    childNodes.append( Node( childFolder, parent = lstParentNodes[ parentFolderID ]) )
                elif childFolderIdx >= foldersCount[ level ][parentFolderID]:                               # This filters folders that only contain files or the sections of a folder that are files
                    if viewFiles: fileNodes.append( Node( childFolder, parent = lstParentNodes[ parentFolderID ] ) ) # In this case, child folder is the name of a file
                    elif not viewFiles: pass

        lstParentNodes = childNodes


    for pre, fill, node in RenderTree(root):
        print(f"{pre}{node.name}")


def viewSubtree(tree,  foldersCount, startDepth, treeDepth, folderID = None, folderPath = None, 
                viewFiles  = True, getFileIDS = False, getFilePathS = False, showIndex = True):
    """
    Args:
    - startDepth: Minimum is 1
    - folderID: Smallest is [ 0 ] -> root 
    """
    if folderPath != None:
        folderID =  convertPathtoID( tree, foldersCount,  folderPath)
        if folderID == None: 
            return None

    # Get Root Name
    rootFolderID = [ folderID[ : startDepth - 1 ] ] # zero index
    rootFolderGamma =  [ getGamma( foldersCount, rootFolderID[0] ) ]
    rootName = pinchLevel( tree,  startDepth, flat = False)[ rootFolderGamma[0] ][ folderID[ startDepth - 1  ] ] # folderID is zero-indexed 
    root = Node(rootName)

    # Initalize for loop
    parentFoldersIDS = [ folderID[ : startDepth ] ] 
    parentFolderGammas =  [ getGamma( foldersCount, parentFoldersIDS[0] ) ]

    lstParentNodes = [ root ]
    fileIDS =[]
    for parentFolderLevel in range( startDepth + 1, treeDepth ): # Bc startDepth was already taken by root Node
        if parentFolderLevel <= len( folderID ):
        
            childNodes = []
            childName = pinchLevel( tree,  parentFolderLevel , flat = False)[ parentFolderGammas[0] ][ folderID[ parentFolderLevel - 1 ] ]       
            childNodes.append( Node( childName, parent = lstParentNodes[ 0 ] ) )

            parentFoldersIDS = [ folderID[ : parentFolderLevel  ] ] # Parent for new level
            parentFolderGammas =  [ getGamma( foldersCount, parentFoldersIDS[0] ) ] # Use [1:]  in parentFoldersIDS[0][1:] bc getGamma does not require root index element
            lstParentNodes = childNodes        
                    
        else:
            # Find how many child folders in each parent folder
            childFoldersIDS = []
            childFoldersGammaS = []
            childNodeS = []


            fileNodeS = []
            for parentFolderID, parentFolderGamma, parentNode in  zip( parentFoldersIDS, parentFolderGammas, lstParentNodes ): # parentfolderID > childFolderID > childGamma & new level > newParentGamma | parentFolderGamma > childfolders and files names
                childFoldersNameS = [] 
                filesNameS = []


                numberChildrenFolderS = foldersCount[ parentFolderLevel  - 1 ][parentFolderGamma] # zero-index, Number of children subfolders in parent folder. IF 0, only get folders in fileNames,
                childFoldersNameS.extend( pinchLevel( tree,  parentFolderLevel , flat = False)[parentFolderGamma][ :numberChildrenFolderS] ) # Get IDS for each subfolder | levelFolderLives + 1 = level child folders lives
                childFoldersIDS.extend( [parentFolderID + [ childID ] for childID in range( numberChildrenFolderS ) ] )
                               
                for idx, childFolderName in enumerate( childFoldersNameS):
                    if showIndex:
                        childNodeS.append( Node( f"[{idx}] {childFolderName}", parent = parentNode ) )
                    else:
                        childNodeS.append( Node( childFolderName, parent = parentNode ) )


                directory = pinchLevel( tree,  parentFolderLevel , flat = False)[parentFolderGamma]
                numberFiles = len( directory[ numberChildrenFolderS: ] ) 
                fileIDS.extend( [parentFolderID + [ fileID ] for fileID in range( numberChildrenFolderS, numberChildrenFolderS + numberFiles ) ] )
                
                filesNameS.extend( pinchLevel( tree,  parentFolderLevel , flat = False)[parentFolderGamma][ numberChildrenFolderS: ] )   
                if viewFiles: 
                    for idx, fileName in enumerate( filesNameS):
                        if showIndex:
                            fileNodeS.append( Node( f"[{numberChildrenFolderS + idx}-f] {fileName}", parent = parentNode ) ) # In this case, child folder is the name of a file
                        else:
                            fileNodeS.append( Node( fileName, parent = parentNode ) )
                elif not viewFiles: pass

            childFoldersGammaS = [ getGamma( foldersCount, folderID ) for folderID in  childFoldersIDS ]
            parentFoldersIDS, parentFolderGammas, lstParentNodes = childFoldersIDS, childFoldersGammaS, childNodeS

    for pre, fill, node in RenderTree(root):
        print(f"{pre}{node.name}")

    if getFileIDS:
        if getFilePathS:
            return fileIDS, [ convertIDtoPath(tree, foldersCount, fileID ) for fileID in fileIDS]
        else:
            return fileIDS
    elif getFilePathS: return [ convertIDtoPath(tree, foldersCount, fileID ) for fileID in fileIDS]
    elif not getFileIDS: return None

################

# Filter and summarise

def getFileTypes( lstFilePaths, regexFilterS = None):
    """
    Args:
    - lstFilePaths:
    - regexFilterS (None / list(lists) ): If list, each element corresponds to one regexFilter to apply. If none, it does not
        - I.e. ["not", regex] -> accept files that do NOT match regex | ["match", regex] -> accept files that MATCH regex
    """
    regex = "\\.\\w*$"
    lstSplitPaths = [ path.split("/") for path in lstFilePaths]
    lstAllFilesTypes = [ path[-1][re.search( regex,  path[-1] ).start() :   ]  if 
                    re.search( regex, path[-1] ) else idx for idx, path in enumerate( lstSplitPaths )  ]
        
    failedFileTypes = [ lstSplitPaths[  idx ][-1]   for idx in lstAllFilesTypes if type(idx) == int ]
    failedFileTypes = list( set( failedFileTypes) )
    failedFileTypes.sort()
    failedFilesDict = {f"Failed_{regex}": failedFileTypes}

    lstFileTypes = [  fileType  for fileType in lstAllFilesTypes if type(fileType) != int ]
    lstFileTypes = list( set( lstFileTypes ) )
    lstFileTypes.sort( )
    filteredFilesDict = {f"Pass_{regex}": lstFileTypes }
    
    if type(regexFilterS) == list:
        for match, regex in regexFilterS:
            matchFileS = [ file for file in lstFileTypes if re.search( "[0-9][0-9][0-9][0-9]$", file)]
            matchFileS.sort()
            notMatchFileS = [ file for file in lstFileTypes if not re.search( "[0-9][0-9][0-9][0-9]$", file)]
            notMatchFileS.sort()
            if match == "match": filteredFilesDict[f"Pass_{regex}"], failedFilesDict[f"Failed_{regex}"] =  matchFileS, notMatchFileS
            elif match == "not": filteredFilesDict[f"Pass_{regex}"], failedFilesDict[f"Failed_{regex}"] =  notMatchFileS, matchFileS
            else: print( "Match must either equal match or not")
            lstFileTypes = filteredFilesDict[f"Pass_{regex}"]

    return filteredFilesDict, failedFilesDict

#########################

# Find Folders and Files Tools : Output their IDs and Paths


def findTargetIdxs(targetItem, tree,startDepth = 1, endDepth = 10, regexpression = None  ):
    
    """
    Args:
    - targetFolder
    - tree: tree object (folder or file - folder is recommended) used to identify where the folder of interest lives
    - startDepth: Can be used to narrow the search scope
    - endDepth: Can be used to narrow the search scope
    - regexpression: To be added in the future, to allow more complex searches
    
    Output:
    - supraFolderIdx: Zero-Index of suprafolder which target folder / file lives in (aka gamma)
    - folderIdx: zero-Index of where the folder / file lives
    - targetLevel: Level (in non-zero index) that identified folder / live  lives in
    """

    targetLevel, supraFolderIdx, folderIdx = None, None, None
    for depth in range( 1, endDepth): # startDepth,
        if depth >= startDepth:
            flatFoldersList = [ item for lst in tree[:-1]  for item in lst ]
            if targetItem in flatFoldersList and not regexpression:                              # Use re.search() for regex
                foldersList = tree[:-1] # pinchLevel( tree, depth, flat = False )  # List of list representing the folders with subfolders in the current level
                IDSlst = [ ( idx, listOfFolders.index( targetItem) ) for idx, listOfFolders in enumerate( foldersList ) if targetItem in  listOfFolders ] # listOfFolders.index( targetFolder) -> Get the zero-index for the target folder inside its suprafolder | 
                supraFolderIdx, folderIdx = IDSlst[0] # 
                targetLevel = depth
                # print(f"Depth: {depth}")
                break
            elif regexpression:
                matchRegex = [ True if re.search( regexpression, item ) else False for item in flatFoldersList  ]
                if any( matchRegex):
                    foldersList = tree[:-1]
                    targetItem = flatFoldersList[ matchRegex.index( True) ]
                    print(f"Target Item: {targetItem}")
                    IDSlst = [ ( idx, listOfFolders.index( targetItem) ) for idx, listOfFolders in enumerate( foldersList ) if targetItem in  listOfFolders ]
                    supraFolderIdx, folderIdx = IDSlst[0]
                    targetLevel = depth
                    break                                  
                
        if depth == endDepth - 1: 
            print(f"Could not find \"{targetItem}\"")
            return None
        
        tree = tree[-1]
    return supraFolderIdx, folderIdx, targetLevel 

def findAllTargetIdxs(targetItem, tree,startDepth = 1, endDepth = 10, regexpression = None  ):

    allTargetIdxs = []
    targetLevel, supraFolderIdx, folderIdx = None, None, None
    for depth in range( 1, endDepth): # startDepth,
        if depth >= startDepth:
            
            flatFoldersList = [ item for lst in tree[:-1]  for item in lst ]

            if targetItem in flatFoldersList and not regexpression:                              # Use re.search() for regex
                foldersList = tree[:-1] # pinchLevel( tree, depth, flat = False )  # List of list representing the folders with subfolders in the current level
                IDSlst = [ ( idx, listOfFolders.index( targetItem ) ) for idx, listOfFolders in enumerate( foldersList ) if targetItem in  listOfFolders ] # listOfFolders.index( targetFolder) -> Get the zero-index for the target folder inside its suprafolder | 
                for IDS in IDSlst:
                    supraFolderIdx, folderIdx = IDS # 
                    targetLevel = depth
                    allTargetIdxs.append( (supraFolderIdx, folderIdx, targetLevel ) )
                    
            elif regexpression:
                
                matchRegex = [ item if re.search( regexpression, item ) else False for item in flatFoldersList  ]
                lstRegexMatches = list( set(  filter( lambda x: x, matchRegex ) ) )

                for matchItem in lstRegexMatches:
                
                    foldersList = tree[:-1]
                    targetItem = matchItem
                    IDSlst = [ ( idx, listOfFolders.index( targetItem) ) for idx, listOfFolders in enumerate( foldersList ) if targetItem in  listOfFolders ]
            
                    for IDS in IDSlst:
                        supraFolderIdx, folderIdx = IDS # 
                        targetLevel = depth
                        allTargetIdxs.append( (supraFolderIdx, folderIdx, targetLevel ) )

        tree = tree[-1]


    return allTargetIdxs


def cumulativeCount( foldersCount):
    finalCount = []
    for levelCount in foldersCount:
        levelRecord = [0]
        for idx, value in enumerate( levelCount ):
            levelRecord.append( levelRecord[idx] + value )
        finalCount.append( levelRecord[1:])
    return finalCount

def getGammaID(supraFolderIdx, folderIdx, targetLevel, folderSumCount ):
    """
    GammaID would be similar to folder ID, but each element represents the gamma 
    for the correspondent level to select the right folder.
    """
    gammaFolderID = [ supraFolderIdx, folderIdx] # It represents the gamma of which folder to open in each level with pinchLevel with exception of the last element which identifies the folder / file


    for _level in range( targetLevel - 1, 0, -1): # level - 1 matches the suprafolder level w/o zero indexing OR the folder level with zero indexing 
        for idx, sumCount in enumerate( folderSumCount[ _level - 1] ):
            if  gammaFolderID[0] + 1 <= sumCount: # If True, it means that we reached the level
                gammaFolderID.insert( 0, idx)
                break
    return gammaFolderID

def convertGammaIDtoFolderID(gammaFolderID, foldersCount):
    folderID = []
    foldersBefore = 0 # Initialize for the root which has o folders
    for idx in range( len( gammaFolderID[:-2] ) ) : # Note that final 2 level is not accounted bc the last element is not a gamma but the actual index, and the one before is accounted with idx + 1
        _level = idx + 1 # Make it non-zero index

        currentGamma = gammaFolderID[idx]
        nextGamma = gammaFolderID[idx+1]

        foldersBefore = sum( foldersCount[ _level - 1][:currentGamma] ) # Get the number of folders before the folder of interest at the specific level
        folderID.append( nextGamma - foldersBefore )

    folderID = folderID + gammaFolderID[-1:]
    return folderID

def traceBackPath(targetItem, tree, foldersCount, treeMaxDepth, startDepth = 1):
    try:
        supraFolderIdx, folderIdx, targetLevel = findTargetIdxs(targetItem, tree, startDepth = startDepth, endDepth= treeMaxDepth+2  )
    except:
        return None
    folderSumCount = cumulativeCount( foldersCount )
    gammaFolderID = getGammaID(supraFolderIdx, folderIdx, targetLevel, folderSumCount )
    folderID = convertGammaIDtoFolderID( gammaFolderID, foldersCount )
    folderPath = convertIDtoPath( tree, foldersCount, folderID)
    return folderPath, folderID



def completeTraceBackPath(targetItem, tree, foldersCount, treeMaxDepth):
    resultPaths = []
    allTargetIdxs = findAllTargetIdxs(targetItem, tree, startDepth = 1, endDepth= treeMaxDepth+2  )

    if allTargetIdxs == []: 
        return None
    else:
        for targetIdx in allTargetIdxs:
            supraFolderIdx, folderIdx, targetLevel = targetIdx
            folderSumCount = cumulativeCount( foldersCount )
            gammaFolderID = getGammaID(supraFolderIdx, folderIdx, targetLevel, folderSumCount )
            folderID = convertGammaIDtoFolderID( gammaFolderID, foldersCount )
            folderPath = convertIDtoPath( tree, foldersCount, folderID)
            resultPaths.append( ( folderPath, folderID ) )
        return resultPaths


def getFiles(tree,  foldersCount, folderID = None, folderPath = None):
    """
    Args:
    - startDepth: Minimum is 1
    - folderID: Smallest is [ 0 ] -> root 
    """
    if folderPath != None:
        print( folderPath )
        folderID =  convertPathtoID( tree, foldersCount,  folderPath)

    fileIDS = []
    filesNameS = []

    fileLevel = len( folderID ) + 1 
    folderGamma = getGamma( foldersCount, folderID )
    directory = pinchLevel( tree,  fileLevel , flat = False)[folderGamma]
    
    numberChildrenFolderS = foldersCount[ fileLevel  - 1 ][folderGamma]
    numberFiles = len( directory[ numberChildrenFolderS: ] )     
    fileIDS.extend( [folderID + [ fileID ] for fileID in range( numberChildrenFolderS, numberChildrenFolderS + numberFiles ) ] )
    if folderPath != None:
        filesNameS.extend( pinchLevel( tree,  fileLevel , flat = False)[folderGamma][ numberChildrenFolderS: ] )   
        filePaths = [ folderPath + "/" + fileName for fileName in filesNameS ]

    if folderPath != None:
        return fileIDS, filePaths
    else:
        return fileIDS, [ convertIDtoPath(tree, foldersCount, fileID ) for fileID in fileIDS]



def canonicalExtract( projName, subProjName, treeObj):
    
    projTree = treeObj
    obtainedPaths = { "session": f"{projName}-{subProjName}", "metadata":[], "datasets":{} }
    
    walkPath = None
    try:
        projFolderPath = traceBackPath( f"{projName}-{subProjName}", projTree["fileTree"], projTree["foldersCount"], 4, startDepth = 3 )[0]
    except:
        print( f"Could not find \"{projName}-{subProjName}\" at depth 3.")

    walkPath = projFolderPath
    projFolderContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"],  projFolderPath )

    if "processing" in projFolderContent:
        walkPath = walkPath + "/processing"
        projFolderContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"],  walkPath )

        if "analysis" in projFolderContent:
            analysisPath = walkPath + "/analysis"
            analysisContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"],  analysisPath )

            if ("initial_model" in analysisContent) != ("model_building" in analysisContent) : # XOR condition

                modelPath = analysisPath + "/initial_model" if "initial_model" in analysisContent else analysisPath + "/model_building"
                modelContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"],  modelPath )
                
                for dataset in modelContent:
                    datasetFilePaths = { "compound.pdb": [], "compound.cif": [], "compound.smiles": [], "dimple.mtz": [], "dimple.pdb": [],
                    "mean-map":[], "z_map" : [], "events": [] ,"pandda-model": [], }
                    
                    datasetPath = modelPath +f"/{dataset}"
                    datasetContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"],  datasetPath )

                    for item in datasetContent:
                        if item == "dimple.mtz": datasetFilePaths["dimple.mtz"].append(datasetPath +"/dimple.mtz" )
                        if re.search( "-pandda-input.mtz$", item): datasetFilePaths["dimple.mtz"].append(datasetPath + f"/{item}" )
                        if item == "dimple.pdb": datasetFilePaths["dimple.pdb"].append(datasetPath +"/dimple.pdb" )
                        if re.search( "-pandda-input.pdb$", item): datasetFilePaths["dimple.pdb"].append( datasetPath + f"/{item}" )
                        if re.search( "pandda-model.pdb$", item ): datasetFilePaths["pandda-model"].append(  datasetPath + f"/{item}" )
                        if re.search( "ground-state-average-map.native.ccp4$", item ): datasetFilePaths["mean-map"].append( datasetPath + f"/{item}" )
                        if re.search( "-ground-state-mean-map.native.ccp4$", item ): datasetFilePaths["mean-map"].append( datasetPath + f"/{item}" )
                        if re.search( "z_map.native.ccp4$", item ): datasetFilePaths["z_map"].append( datasetPath + item)
                        if re.search( ".+-event_.+-BDC_.+_map.native.ccp4$", item ): datasetFilePaths["events"].append( datasetPath + f"/{item}" )
                        if item == "compound":
                            compoundPath = datasetPath + "/compound"
                            compoundContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"], compoundPath )
                            for compoundItem in compoundContent:
                                if re.search( ".+pdb$", compoundItem): datasetFilePaths["compound.pdb"].append( compoundPath + f"/{compoundItem}" )
                                if re.search( ".+cif$", compoundItem): datasetFilePaths["compound.cif"].append( compoundPath + f"/{compoundItem}" )
                                if re.search( ".+smiles$", compoundItem): datasetFilePaths["compound.smiles"].append( compoundPath + f"/{compoundItem}" )
                
                    obtainedPaths["datasets"][f"{dataset}"] = datasetFilePaths



            elif "initial_model" in projFolderContent and "model_building" in projFolderContent:
                print(f"There is \"initial_model\" and \"model_building\" folders inside { analysisPath }")
            
            else: 
                print(f"There is NO \"initial_model\" NOR \"model_building\" folders inside { analysisPath }")
        else:
            print(f"There is no \"analysis\" folder inside { walkPath }")
        
        if "database" in projFolderContent:
            dbPath = walkPath + "/database"
            dbContent = openFolderwPath( projTree["fileTree"], projTree["foldersCount"],  dbPath )
            for item in dbContent:
                if re.search( ".sqlite$", item): obtainedPaths["metadata"].append( dbPath + f"/{item}" )

        else:
            print(f"There is no \"database\" folder inside {walkPath}")

    else:
        print(f"There is no \"processing\" folder inside {walkPath}")
    
    return obtainedPaths

if __name__ == "__main__":

    pass
