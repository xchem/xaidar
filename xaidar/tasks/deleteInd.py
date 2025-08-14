# #Initialize Notebook Environment
# from pathlib import Path
# import sys
# # sys.path.insert( 0, Path("../..").resolve().absolute().__str__() )

# from xaidar.filesUtils import loadPickle, savePyObj
# from xaidar.treeObj import convertPathtoID, findAllFolderFiles

# taskDir = Path( "./data/tasks/delIndustry" )
# filePath = taskDir / "lst_sessions.pkl"
# lst_sessions = list( loadPickle( filePath.resolve() )  )
# print(f"Loaded {len(lst_sessions)} sessions from lst_sessions.pkl")

# # Filter sessions for only industry-related sessions
# industry_sessions = []
# industry_labels = [ "sw", "in" ]
# for session in lst_sessions:
#     sesh_label = session.split("/")[-1][:2]
#     if sesh_label in industry_labels:
#         industry_sessions.append(session)

# del lst_sessions  # Clear memory
# print(f"Filtered {len(industry_sessions)} industry-related sessions")

# # Save the filtered sessions
# savePath = taskDir / "industry_sessions.pkl"
# savePyObj( industry_sessions, savePath.resolve() )

# # Find and prepare tree objects for industry sessions
# lst_treeObj_sessions = { "tree": [], "path": []}
# for sesh in industry_sessions:
#     seshPath = sesh.split("/")
#     year, session = seshPath[1], seshPath[2]
#     lst_treeObj_sessions[ "path" ].append( sesh )
#     lst_treeObj_sessions[ "tree" ].append( f"tree_{year}_{session}.pkl")

# del industry_sessions  # Clear memory
# print(f"Prepared tree objects for industry sessions")

# # Load tree objects and find all folder files for each industry session
# numb_sessions = len(lst_treeObj_sessions["tree"])
# print(f"Number of sessions with tree objects: {numb_sessions}")

# for idx in range(numb_sessions):
#     print(f"Processing session {idx+1}/{numb_sessions}...")
#     print(f"Session Path: {lst_treeObj_sessions['path'][idx]}")
#     fileName = lst_treeObj_sessions[ "tree" ][idx]
#     dirPath = lst_treeObj_sessions[ "path" ][idx]
#     sessionName = dirPath.split("/")[-1]
#     tree = loadPickle( Path(f"./data/treeObjs/xchem/data/{ fileName }" ))
#     dirID = convertPathtoID( tree["fileTree"], tree["foldersCount"], dirPath)
#     results = findAllFolderFiles( tree["fileTree"], tree["foldersCount"], dirID )
#     savePath = taskDir / f"{idx}_{sessionName}_delFiles.pkl"
#     savePyObj( results, savePath.resolve() )
#     print(f"Saved results for session {idx+1}/{numb_sessions} to {taskDir / f'{idx}_{sessionName}_delFiles.pkl'}")

# ### Delete Files in S3 Bucket
# import os
# from pathlib import Path

# from xaidar.filesUtils import loadPickle, savePyObj
# from xaidar.s3Utils import decryptCredentials, initialize, iterateObjStore, lstAllKeys

# # 
# credKey = "" #### !!! Must fill this for code to work !!! ####
# # credKey = os.getenv( "CRED_KEY" )
# credPath =  Path( "./credentials.enc").resolve()
# credDict = decryptCredentials( credKey, credPath )
# client = initialize( "XChem", cred_dict=credDict)

# totalSize = 0 
# size_failedAPICalls = []
# del_failedAPICalls = []

# bucket = "xchem"
# taskDir = Path( "./data/tasks/delIndustry" )

# # for file in taskDir.glob("[0-9]*.pkl"):#  # [0-9]*.pkl
# file = taskDir / "6_sw26557-1_delFiles.pkl"  # Example file, replace with your actual file
# lst_paths = loadPickle( file ) # file
# print(f"Processing file: {file.name}, Number of paths: {len(lst_paths)}")
# for path in lst_paths:
#     print(f"Processing path: {path}")
#     try:
#         response = client.head_object(Bucket=bucket, Key=path)
#         if not "ContentLength" in list(response.keys()):
#             size_failedAPICalls.append(path)
#         else:
#             totalSize += response['ContentLength']
#     except Exception as e:
#         pass

#     try:
#         client.delete_object(Bucket=bucket, Key=path)
#     except Exception as e:
#         print(f"Failed to delete {path}: {e}")
#         del_failedAPICalls.append(path)

# print(f"Total size of deleted files: {totalSize} bytes")
# print(f"Failed API calls for size retrieval: {len(size_failedAPICalls)}")
# if size_failedAPICalls:
#     print("Failed to retrieve sizes for the following paths:")
#     for path in size_failedAPICalls:
#         print(path)
# print(f"Failed API calls for deletion: {len(del_failedAPICalls)}")



# Mass deletion of files in S3 bucket
from pathlib import Path

from xaidar.filesUtils import loadPickle
from xaidar.s3Utils import decryptCredentials, initialize, massDeletion

credKey = "v6Q2ZQB7FlFgpI_-8OpC-4g7LZA34JKWesfZsYng7Wg="
# credKey = "" #### !!! Must fill this for code to work !!! ####
# credKey = os.getenv( "CRED_KEY" )
credPath =  Path( "./credentials.enc").resolve()
credDict = decryptCredentials( credKey, credPath )
client = initialize( "XChem", cred_dict=credDict)

bucket = "xchem"
taskDir = Path( "./data/tasks/delIndustry" )
for file in taskDir.glob("[0-9][0-9]*.pkl"):#  # [0-9]*.pkl
    lst_paths = loadPickle(file)
    print(f"Processing file: {file.name}, Number of paths: {len(lst_paths)}")
    massDeletion(client, bucket, lst_paths, fileName=file.name)


for file in taskDir.glob("[89]*.pkl"):#  # [0-9]*.pkl
    lst_paths = loadPickle(file)
    print(f"Processing file: {file.name}, Number of paths: {len(lst_paths)}")
    massDeletion(client, bucket, lst_paths, fileName=file.name)

# # Test to see if any files remain in the bucket

# bucket = "xchem"

# deletedFilesCount = 0
# def foo():
#     for file in taskDir.glob("[0-9]*.pkl"):
#         lst_paths = loadPickle( file )
#         print(f"Processing file: {file.name}, Number of paths: {len(lst_paths)}")
#         for path in lst_paths:
#             try:
#                 response = client.head_object(Bucket=bucket, Key=path)
#                 print(f"Successfully accessed {key} in bucket {bucket}")
#                 return

#             except Exception as e:
#                 # print(f"Error accessing {key} in bucket {bucket}: {e}")
#                 deletedFilesCount += 1
# foo()