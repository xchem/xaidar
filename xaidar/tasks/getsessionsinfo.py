
from pathlib import Path
import sys
sys.path.insert(0, Path("../.."))

from xaidar.filesUtils import loadPickle, savePyObj

xchemRawKeysDir = Path("../../data/s3Sizes/xchem/raw")

lookExample = True
rootDirNames = ["data", "dataset"]
rootDirContent = { dir : {"year": [], "session": [], "size": [] } for dir in rootDirNames}
for fragPath in xchemRawKeysDir.iterdir(): 
    if fragPath.is_file():
        frag = loadPickle( fragPath )
        for key, value in frag.items():
            objPath = key.split("/")
            rootDir = objPath[0]
            
            if rootDir in rootDirNames:
                rootDirContent[rootDir]["year"].append( objPath[1])
                rootDirContent[rootDir]["session"].append( objPath[2])
                if type( value) == int:
                    rootDirContent[rootDir]["size"].append( value )
                else:
                    rootDirContent[rootDir]["size"].append( None)
            else:
                print( f"New root Dir in xchem: {rootDir}")


savePyObj( rootDirContent, Path( "./xchemSeshs.pkl"))
print( "Done")