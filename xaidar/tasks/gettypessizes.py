from pathlib import Path
import sys
sys.path.append( Path( "../.." ).resolve().__str__() )
from collections import defaultdict
import re
import time

from xaidar.filesUtils import loadPickle, savePyObj

fileTypeSizes = defaultdict( list )
# fileSizes = 
sizesDir = Path( "../../data/s3Sizes/xchem" )
start = time.time()
print( f"Processing file types in {sizesDir}" )
for fragPath in sizesDir.iterdir():
    if fragPath.is_file() and fragPath.name[:-10] not in ["frag1", "frag2", "frag3", "frag4", "frag5"]:
        step = time.time()
        fragName = fragPath.name
        frag = loadPickle( fragPath )
        print( f"    Loaded {fragPath.name} with {len(frag)} entries" )
        for key, size in frag.items():
            if re.search( "\\.\\w*$", key ): 
                filetype = re.search( "\\.\\w*$", key.split("/")[-1]).group()
                try:
                    fileTypeSizes[filetype].append( int(size) )
                except:
                    print( f"Error processing size for {key} with size {size}" )
                    break

            # break  # Remove this line to process all files
        savePath = sizesDir.joinpath( f"filetypes/{fragName[:-10]}_filetype_sizes.pkl" )
        print( f"\tSaving file type sizes to {savePath}" )
        savePyObj( fileTypeSizes, savePath )
        print( f"\tSaved {fragName[:-10]}_filetype_sizes.pkl" )
        print( f"\tTime: {round(time.time() - step, 0)} seconds" )
    # break  # Remove this line to process all fragments
print( f"Done processing file types in {round( time.time() - start, 0)} seconds " )