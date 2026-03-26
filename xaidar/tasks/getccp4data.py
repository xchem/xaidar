from xaidar.filesUtils import loadPickle, savePyObj
from pathlib import Path
import re

objStoreContent = {}
for bucket in ["xchem", "pandda"]:
    print( f"Loading Bucket {bucket} ")
    ccp4Files = {}
    fileTypesDir = Path(f"./data/s3Sizes/{bucket}/raw")
    for frag in fileTypesDir.iterdir():
        print( f"Loading fragment file: {frag.name}")
        if frag.is_file:
            fileTypes = loadPickle( frag )
            for objKey, size in list(fileTypes.items()):
                if re.search( "\.ccp4$", objKey):
                    fileName = objKey.split("/")[-1]
                    ccp4Files[objKey] = ( fileName, size )

    objStoreContent[bucket] = ccp4Files

print( "Finished Processing, starting to save")
savePath = Path( "./data/s3Sizes/ccp4Files.pkl")
savePyObj( objStoreContent, savePath )
print( "Finished saving")