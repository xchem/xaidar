from pathlib import Path
import sys
sys.path.append( Path( "." ).resolve().__str__() )

# import os
# import pickle
# import time

# from xaidar.filesUtils import loadPickle, savePyObj
# from xaidar.s3Utils import decryptCredentials, initialize

# import boto3
# from concurrent.futures import ThreadPoolExecutor, as_completed
# credKey = os.getenv( "CRED_KEY" )
# credDic = decryptCredentials( credKey, Path( "./credentials.enc") )
# # Initialize boto3 client
# s3 = initialize("XChem", credDic)

# def get_object_size(bucket_name, key):
#     try:
#         response = s3.head_object(Bucket=bucket_name, Key=key)
#         return key, response['ContentLength']  # Size in bytes
#     except Exception as e:
#         return key, f"Error: {e}"

# def fetch_sizes_parallel(bucket_name, keys, max_workers=20):
#     sizes = {}

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         future_to_key = {executor.submit(get_object_size, bucket_name, key): key for key in keys}
#         for future in as_completed(future_to_key):
#             key, size = future.result()
#             sizes[key] = size
#     return sizes

# for bucket_name in [ "xchem", ]:# "pandda",
#     # bucket_name = "xchem"
#     for frag in Path( f"./data/s3ObjKeys/{bucket_name}" ).iterdir():
#         if frag.is_file():
#             if frag.name == "frag4.pkl":
#                 pass
#             else:
#                 keys = loadPickle( frag )[1:]
#                 start = time.time()
#                 print(f"Started with {frag.name[:-4]} for {bucket_name}")
#                 sizes = fetch_sizes_parallel( bucket_name, keys, max_workers=40 )
#                 print( f"Fetched sizes in {time.time() - start} seconds")

#                 savePath = Path("./data/s3Sizes").joinpath( bucket_name, f"{frag.name[:-4]}_sizes.pkl" ).resolve()
#                 print( "Saved Path: {}".format( savePath ) )    
#                 savePath.parent.mkdir( parents=True, exist_ok=True )
#                 savePyObj( sizes, savePath ) 
#                 print( f"Saved {bucket_name}-{frag.name[:-4]}_sizes.pkl: { time.time() - start }" )
#     #         break
    #     break
    # break


# # Get frag sizes files #################
# import os
# from pathlib import Path
# from xaidar.s3Utils import decryptCredentials, initialize

# credKey = os.getenv( "CRED_KEY" ) 
# credPath =  Path( "../../credentials.enc").resolve()
# credDict = decryptCredentials( credKey, credPath )
# client = initialize( "XChem", cred_dict=credDict  )

# from xaidar.s3Utils import iterateObjStore, getAllObjSizes
# for bucket, saveDir, fragSize in zip( ["xchem", "pandda" ],[ "XChem", "PanDDa"] , [1e4, 1e3]) :
#     iterateObjStore( bucket, client, save = True, saveDir = saveDir, fragSize = fragSize, frag = True, function = getAllObjSizes )


# # Turn frag files into file type frag #######################
# from collections import defaultdict
# import time
# from xaidar.filesUtils import loadPickle, savePyObj
# import re

# for bucket in ["pandda", "xchem"]:
#     fileTypeSizes = defaultdict( list )
#     # fileSizes = 
#     sizesDir = Path( f"../../data/s3Sizes/{bucket}" ) # /xchem
#     start = time.time()
#     print( f"Processing file types in {sizesDir}" )
#     for fragPath in sizesDir.iterdir():
#         # if not fragPath.is_file() or not re.search( "_sizes.pkl$", fragPath.name ): 
#         #     print( f"Skipping {fragPath.name}" )
#         #     continue
#         # print( f"Processing {fragPath.name}" )
#         if fragPath.is_file() and re.search( "_sizes.pkl$", fragPath.name ):
#             step = time.time()
#             fragName = fragPath.name
#             frag = loadPickle( fragPath )
#             print( f"    Loaded {fragPath.name} with {len(frag)} entries" )
#             for key, size in frag.items():
#                 if re.search( "\\.\\w*$", key ): 
#                     filetype = re.search( "\\.\\w*$", key.split("/")[-1]).group()
#                     fileTypeSizes[filetype].append( size )
#                 else:
#                     fileTypeSizes[f"dif-{filetype}"].append( size )

                    

#             # break  # Remove this line to process all files

#             newSavePath = sizesDir / "newDir" / f"{fragName[:-10]}_filetype_sizes.pkl"
#             newSavePath.parent.mkdir( parents=True, exist_ok=True )
#             print( f"\tSaving file type sizes to {newSavePath}" )
#             savePyObj( fileTypeSizes, newSavePath )
#             print( f"\tSaved {fragName[:-10]}_filetype_sizes.pkl" )
#             print( f"\tTime: {round(time.time() - step, 0)} seconds" )
#             fileTypeSizes = defaultdict( list )

# # Merge all file type sizes into one file ########################


# from collections import defaultdict
# import re
# from pathlib import Path

# from xaidar.filesUtils import loadPickle, savePyObj
# for bucket in ["pandda", "xchem"]:
#     cacheDir = Path( f"../../data/s3Sizes/{bucket}/newDir")
#     fileNames = sorted( [ file.name for file in cacheDir.iterdir() if file.is_file() ] , key = lambda x: int( re.match( "frag[0-9]+", x).group()[4:] ) )

#     # Save it all into one Dictionary
#     mergedSizes = defaultdict(list)
#     for fileName in fileNames:
#         print(f"Processing {fileName}")
#         fileSizes = loadPickle( cacheDir / fileName )
#         for key, size in fileSizes.items():
#             mergedSizes[key].extend(size)


#     savePath = cacheDir / "merged_filetype_sizes.pkl"
#     print(f"Saving merged sizes to {savePath}")
#     savePyObj( mergedSizes, savePath )
#     print(f"Saved merged sizes to {savePath}")


## Get Statistics of file sizes ########################
import sys
from pathlib import Path
sys.path.insert(0, Path("../..").resolve().absolute().__str__())

import numpy as np

from xaidar.filesUtils import loadPickle

for bucket in [ "xchem"]: # "pandda",
    failedSizes = 0
    cacheDir = Path(f"../../data/s3Sizes/{bucket}/filetypes")

    mergedSizes = loadPickle( cacheDir / "merged_filetype_sizes.pkl" )

    data = { "File Type": [], "Files Count": [], "Median": [], "Mean": [], "Std": [], 
            "1stQrt": [], "3rdQrt": [], "QrtDeviation": [] , "Max": [], "Min": [], "Sum": [] }

    for fileType, sizes in mergedSizes.items():
        # print(f"Processing file type: {fileType} with {len(sizes)} sizes")
        if len(sizes) > 0:
            filteredSizes = [ size for size in sizes if type(size) == int]
            failedSizes  += len( [ size for size in sizes if type(size) != int])

            data["File Type"].append(fileType)
            data["Files Count"].append(len(sizes))

            data["Median"].append(np.median(filteredSizes))
            data["Mean"].append(np.mean(filteredSizes))
            data["Std"].append(np.std(filteredSizes))
            data["1stQrt"].append(np.percentile(filteredSizes, 25))
            data["3rdQrt"].append(np.percentile(filteredSizes, 75))
            data["QrtDeviation"].append((np.percentile(filteredSizes, 75) - np.percentile(filteredSizes, 25)) / 2)
            data["Max"].append(np.max(filteredSizes))
            data["Min"].append(np.min(filteredSizes))
            data["Sum"].append( np.sum(filteredSizes) )



    print("Data collected for file types:")
    print(f"Number of file types: {len(data['File Type'])}")
    from xaidar.filesUtils import savePyObj

    savePath = cacheDir / "stats_filetype_sizes.pkl"
    print(f"Saving statistics to {savePath}")
    savePyObj(data, savePath)
    print(f"Saved statistics to {savePath}")
    print( f"Total files with non-integer sizes: {failedSizes}" ) 