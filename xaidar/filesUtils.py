# Scritps associated with manipulation of objects into and out of files, and manipulation of files themselves

import boto3
import pickle
import os
import re
import numpy as np
from datetime import datetime
from collections import defaultdict

# from xaidar.objFileSys import createTree

def loadPickle( path ):
    with open( path, "rb") as file:
        return pickle.load( file )

def getFilesList( path ):
    """
    Return the list of file names that exist in input directory
    Args
    - path ( pathlist.Path() object)
    """
    list = [ file for file in os.listdir( path) if os.path.isfile( path / file) ]
    list.sort()
    return list 

def saveList( lstToSave, pathToSave, readMe = None):
    if readMe != None: lstToSave["ReadMe"] = readMe  
    if pathToSave != None:
        with open(pathToSave, "wb") as file:
            pickle.dump( lstToSave, file)
        print( "Saved!" )
    elif pathToSave == None:
        date = datetime.today().strftime("%Y%m%d-%H%M") 
        pathToSave = os.path.join( os.getcwd(),  f"{ date }_objectKeysDict.pkl" )
        with open(pathToSave, "wb") as file:
            pickle.dump( lstToSave, file)
        print( "Saved!" )
    else: raise Exception( "There is an error with the pathToSave argument" ) 

def savePyObj( objToSave, pathToSave): 
    if pathToSave != None:
        with open(pathToSave, "wb") as file:
            pickle.dump( objToSave, file)
        # print( "Saved!" )
    elif pathToSave == None:
        date = datetime.today().strftime("%Y%m%d-%H%M") 
        pathToSave = os.path.join( os.getcwd(),  f"{ date }.pkl" )
        with open(pathToSave, "wb") as file:
            pickle.dump( objToSave, file)
        print( "Saved!" )
    else: raise Exception( "There is an error with the pathToSave argument" ) 

def countFiles(filesDir, maxFiles = None, filesList = None ):
    """
    Count the number of elements in each pickle file containing a list
    Args:
    - filesDir -> relative path
    - maxfiles -> max number of files to count from
    - filesList -> specify the files you want to look at. Must be None or list objects

    """
    dirPath = filesDir
    lstFiles = [ file for file in os.listdir(filesDir) if os.path.isfile( os.path.join(dirPath, file) ) and  file != "mergedFiles.pkl" ] if not filesList else filesList
    dct ={"TotalCount":0, "CountPerFile":[]}
    count = 0
    for file in lstFiles:
        count+=1
        with open(os.path.join( filesDir, file), "rb" ) as dataFile:
            data = pickle.load( dataFile)
            dct["TotalCount"]+= len(data)
            dct["CountPerFile"].append( len(data) )
        if type(maxFiles) == int: 
            if count >= maxFiles: 
                continue
    
    print("In all files together there are {} elements".format( dct["TotalCount"] ))
    return dct

def mergeFiles( filesDir, maxFiles = None, filesList = None ):
    dirPath = filesDir
    lstFiles = [ file for file in os.listdir(filesDir) if os.path.isfile( os.path.join(dirPath, file) ) and  file != "mergedFiles.pkl" ]  if not filesList else filesList
    lst = []
    count = 0
    with open( os.path.join( filesDir, "mergedFiles.pkl"), "wb" ) as file:
        pickle.dump( lst, file )
    for file in lstFiles:
        count += 1
        with open(os.path.join( filesDir, file), "rb" ) as dataFile:
            data = pickle.load( dataFile)
        with open( os.path.join( filesDir, "mergedFiles.pkl"), "rb" ) as mergeFile:
            merge = pickle.load( mergeFile )
            merge.extend( data )
        with open( os.path.join( filesDir, "mergedFiles.pkl"), "wb" ) as file:
            pickle.dump( merge, file )
        
        print(f"Merge {count} file")

        if type(maxFiles) == int: 
            if count >= maxFiles: 
                continue

    print( "Finished merging")

def roundBytes( bytesSize:int ):
    """
    Rounds a size measured in bytes units to the closest upscale 
    """
    units = ['Byte', 'KB', 'MB', 'GB', 'TB']
    for n, unit in  zip( range( 0, 13, 3), units) :
        if bytesSize >= 1*10**n: roundSize = f"{ bytesSize // (1*10**n) }{unit}"
        else: break
    return roundSize

def getFragFiles( paths ):
    """
    Gets the list of frag_n.pkl files with saved objectKeys from directory
    Args:
    - paths (list)
    """
    filesDict = {}
    for path in paths:
        folder =  re.search( "[a-zA-Z]+$", path).group()
        print( folder )
        lst = []
        for content in os.listdir( path):
            if os.path.isfile( os.path.join( path, content) ): lst.append( content )
        lst.sort( key = lambda x: int( x[4:-4] )  ) 
        print( lst )
        filesDict[folder] = lst 
    return filesDict

def getPklFileNames( paths: list ):
    """
    Gets the list of frag_n.pkl files with saved objectKeys from directory
    Args:
    - paths (list): list with paths of a diretory each with 
    """
    filesDict = {}
    for path in paths:
        folder = path.split( "/")[-1]
        print( folder )
        lst = []
        for content in os.listdir( path):
            if os.path.isfile( os.path.join( path, content) ): lst.append( content )
        lst.sort( ) 
        filesDict[folder] = lst 
    return filesDict

def getRootFolders( dirPathS, pickleFilesDic):
    """
    Args:
    - dirPathS (list): each element is a string of the path of a specific directory with .pkl files of objectKeys
    - pickleFilesDic ( dict of list): a list of .pkl files for each specific directory
    Output:
    - A dictionary with a a list of root names for each 
    """
    rootS = {}
    for dirPath, bucketName in zip( dirPathS, pickleFilesDic.keys() ):
        print( bucketName, "\n")
        pklFilesLst = pickleFilesDic[bucketName]
        lstOfRootS = []

        for pklFileName in pklFilesLst:
            lstOfPathS = loadPickle( os.path.join( dirPath, pklFileName ) )[1:]
            foldersLst = list( set( [  path.split("/")[ 0 ]  for path in lstOfPathS ] ) ) 
            foldersLst.sort()
            orderedFolderLst = foldersLst
            lstOfRootS.extend( orderedFolderLst )
            print( f"Finished {pklFileName}")

        del lstOfPathS

        lstOfRootS = list( set( lstOfRootS ) )
        lstOfRootS.sort()
        print( lstOfRootS )
        rootS[bucketName] = lstOfRootS

    return rootS

def splitXChemData(xchemPath , savedFolder = None): 
    """
    Args:
    - xchemPath (list): path for directory with XChem pickle files 
    - savedFolder (list): list of subfolders to path to directory where to save data
    """
    # Get and Order Pickle File Names 
    filesLst = []
    for content in os.listdir( xchemPath):
        if os.path.isfile( os.path.join( xchemPath, content) ): filesLst.append( content )
    filesLst.sort( key = lambda x: int( x[4:-4] )  ) 
    print( filesLst)

    # Initialize
    currentProject = ["2015", "lb13308-1"] 
    projectLst = [ ]
    datasetDic = defaultdict( list )

    for fileName in filesLst:#[]:
        print(f"File Name: {fileName}")
        lstOfPathS = loadPickle( os.path.join( xchemPath, fileName ) )[1:]
        for path in lstOfPathS:
            pathParts = path.split("/")
            
            if pathParts[0] == "data":                              # For data files
                if pathParts[1] == currentProject[0] and pathParts[2] == currentProject[1]:
                    projectLst.append( path )
                else:
                    saveList( projectLst, os.path.join( savedFolder, "data", f"{currentProject[0]}_{currentProject[1]}.pkl") ) # Save Data
                    print(f"\tProject: {currentProject[0]}_{currentProject[1]}")
                    projectLst = [ ]
                    projectLst.append( path )
                    currentProject = [ pathParts[1] , pathParts[2] ]
            elif pathParts[0] == "dataset":                         # For dataset files
                datasetDic[ pathParts[2] ].append( path )
            else:
                continue
    
    for proj in datasetDic.keys(): saveList( datasetDic[proj], os.path.join( savedFolder, "dataset", f"{proj}.pkl" ) ) # Save Dataset

def splitPanDDaData( panddaPath , savedFolder = []):
    """
    Args:
    - panddaPath (list): path for directory with PanDDa pickle files 
    - savedFolder (list): list of subfolders to path to directory where to save data
    """
    # Get and Order Pickle File Names 
    filesLst = []
    for content in os.listdir( panddaPath):
        if os.path.isfile( os.path.join( panddaPath, content) ): filesLst.append( content )
    filesLst.sort( key = lambda x: int( x[4:-4] )  ) 
    print( filesLst)

    #Initialize
    currentProject = "70X" # This is the name of the first project
    projectLst = [ ]
    record = []

    for fileName in filesLst:
        lstOfPathS = loadPickle( os.path.join( panddaPath, fileName ) )[1:]
        for path in lstOfPathS:
            pathParts = path.split("/")
            if len(pathParts) == 1: # For the record and log files
                record.append( path)
            else:
                if pathParts[0] == currentProject:
                    projectLst.append( path )    
                else:
                    saveList( projectLst, os.path.join( savedFolder, currentProject) )
                    print(f"\tProject: {currentProject}")
                    projectLst = [ ]
                    projectLst.append( path )
                    currentProject = pathParts[0]                        

    saveList( record, os.path.join( savedFolder, "000-record" ) )

# def convertPathstoTree(pklDir: list, saveDir):
#     """
#     Takes a directory of pkl files with a list of paths in each, and converts and saves 
#     each to a dictionary with tree metrics (file tree, foldersCount, etc...)
#     Args:
#     - pklDir ( list ): 
#     - saveDir ( path ): path to a 
#     """ 
#     projFileNames = getPklFileNames(  [ pklDir ]  ) # Output dict with "data", and list of .pkl files
#     root = list( projFileNames.keys() )[0]
#     for projectName in projFileNames[ root ]: 
#         print( projectName)
#         projPathsLst = loadPickle( os.path.join( pklDir, projectName) )
#         fileTree, folderTree, folderTreeMaxDepth,  foldersIDS, foldersCount, foldersLst = createTree( projPathsLst )


#         keysLst = ['fileTree', 'folderTree', 'folderTreeMaxDepth', ' foldersIDS', 'foldersCount', 'foldersLst']
#         objLst = [ fileTree, folderTree, folderTreeMaxDepth,  foldersIDS, foldersCount, foldersLst ]
#         treeDic = { key: obj for key, obj in zip( keysLst, objLst ) }

#         with open( os.path.join( saveDir, f"tree_{projectName}.pkl"), "wb") as f:
#             pickle.dump( treeDic, f )
#         print(f"Saved {projectName}")