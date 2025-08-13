#Initialize Notebook Environment
from pathlib import Path
import sys
# sys.path.insert( 0, Path("../..").resolve().absolute().__str__() )

from xaidar.filesUtils import loadPickle, savePyObj
from xaidar.treeObj import convertPathtoID, findAllFolderFiles

taskDir = Path( "./data/tasks/delIndustry" )
filePath = taskDir / "lst_sessions.pkl"
lst_sessions = list( loadPickle( filePath.resolve() )  )
print(f"Loaded {len(lst_sessions)} sessions from lst_sessions.pkl")

# Filter sessions for only industry-related sessions
industry_sessions = []
industry_labels = [ "sw", "in" ]
for session in lst_sessions:
    sesh_label = session.split("/")[-1][:2]
    if sesh_label in industry_labels:
        industry_sessions.append(session)

del lst_sessions  # Clear memory
print(f"Filtered {len(industry_sessions)} industry-related sessions")

# Save the filtered sessions
savePath = taskDir / "industry_sessions.pkl"
savePyObj( industry_sessions, savePath.resolve() )

# Find and prepare tree objects for industry sessions
lst_treeObj_sessions = { "tree": [], "path": []}
for sesh in industry_sessions:
    seshPath = sesh.split("/")
    year, session = seshPath[1], seshPath[2]
    lst_treeObj_sessions[ "path" ].append( sesh )
    lst_treeObj_sessions[ "tree" ].append( f"tree_{year}_{session}.pkl")

del industry_sessions  # Clear memory
print(f"Prepared tree objects for industry sessions")

# Load tree objects and find all folder files for each industry session
numb_sessions = len(lst_treeObj_sessions["tree"])
print(f"Number of sessions with tree objects: {numb_sessions}")

for idx in range(numb_sessions):
    print(f"Processing session {idx+1}/{numb_sessions}...")
    print(f"Session Path: {lst_treeObj_sessions['path'][idx]}")
    fileName = lst_treeObj_sessions[ "tree" ][idx]
    dirPath = lst_treeObj_sessions[ "path" ][idx]
    sessionName = dirPath.split("/")[-1]
    tree = loadPickle( Path(f"./data/treeObjs/xchem/data/{ fileName }" ))
    dirID = convertPathtoID( tree["fileTree"], tree["foldersCount"], dirPath)
    results = findAllFolderFiles( tree["fileTree"], tree["foldersCount"], dirID )
    savePath = taskDir / f"{idx}_{sessionName}_delFiles.pkl"
    savePyObj( results, savePath.resolve() )
    print(f"Saved results for session {idx+1}/{numb_sessions} to {taskDir / f'{idx}_{sessionName}_delFiles.pkl'}")

