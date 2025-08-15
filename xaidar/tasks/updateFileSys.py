from pathlib import Path

from xaidar.filesUtils import loadPickle, savePyObj
from xaidar.s3Utils import decryptCredentials, initialize, iterateObjStore, lstAllKeys

credKey = "v6Q2ZQB7FlFgpI_-8OpC-4g7LZA34JKWesfZsYng7Wg="
# credKey = "" #### !!! Must fill this for code to work !!! ####
# credKey = os.getenv( "CRED_KEY" )
credPath =  Path( "./credentials.enc").resolve()
credDict = decryptCredentials( credKey, credPath )
client = initialize( "XChem", cred_dict=credDict)

saveDirPath = Path( "./data/s3ObjKeys/xchem/new-raw")
buckets = ["xchem"]
for bucket in buckets:
    iterateObjStore(bucket, client, save = True, function = lstAllKeys, savePath = None, saveDir = "ObjStoreContent", fragSize = 1000, maxLen = None, frag = True, saveObjContent = None)
print("Done iterating over S3 bucket objects.")


# Get list of all session IDs
import re
from collections import defaultdict

dictSessionDirs = defaultdict( set )
rawXCDir = Path( "../../../data/s3ObjKeys/xchem/new-raw")
sessionRegex = "^[a-z][a-z][0-9]+-[0-9]+$"

for fragFile in rawXCDir.iterdir():
    if fragFile.is_file():
        print( f"Loading file: {fragFile.name}")
        frag = loadPickle( fragFile)
        keys = frag["Content"][1:]
        for objKey in keys:
            pathLst = objKey.split("/")
            path = ""
            for item in pathLst:
                path += "/" + item
                if re.search( sessionRegex, item):
                    dictSessionDirs[item].add( path[1:] )

# Save the session directories
savePath = Path( "./data/tasks/analys-sessions/sessionDirs.pkl").resolve()
savePath.parent.mkdir(parents=True, exist_ok=True)
savePyObj( dictSessionDirs, savePath )
print(f"Found {len(dictSessionDirs)} unique session directories in xchem bucket.")
print(f"Saved session directories to {savePath}")


