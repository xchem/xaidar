# from pathlib import Path
# import sys
# sys.path.append( Path( "." ).resolve().__str__() )

# import os
# import pickle
# import time

# from xaidar.filesUtils import loadPickle, savePyObj
# from xaidar.s3Utils import decryptCredentials, initialize

# credKey = os.getenv( "CRED_KEY" ) 
# credDic = decryptCredentials( credKey, Path( "credentials.enc") )
# client = initialize( "XChem", credDic )

# start = time.time()
# print("Started")

# objKeysDir = Path( "data/s3ObjKeys" ) 
# xchemDir = objKeysDir / "xchem" 
# panddaDir = objKeysDir / "pandda" 

# for bucketDir in [ panddaDir, xchemDir  ]:
#     bucket = bucketDir.name
#     for pickleLst in bucketDir.iterdir():
#         if  pickleLst.is_file():
#             fileCountLabel = pickleLst.name[:-4] + "_sizes.pkl"
#             print(fileCountLabel)
#             fileSizesCount = {}

#             pathsLst = loadPickle( pickleLst)[1:]
#             # print(pathsLst)
#             for objKey in pathsLst:
#                 fileSizesCount[ objKey ] = int( client.head_object(  Bucket = bucket, Key = objKey)["ContentLength"] )

#             print( "Count Done")
#             # print( fileSizesCount)
#             savePath = Path("data/s3Sizes").joinpath( bucket, fileCountLabel ).resolve()
#             print( savePath )
#             savePath.parent.mkdir( parents=True, exist_ok=True )
#             savePyObj( fileSizesCount, savePath ) 
#             print( f"Saved {bucket}-{fileCountLabel}: { time.time() - start }" )
       


from pathlib import Path
import sys
sys.path.append( Path( "." ).resolve().__str__() )

import os
import pickle
import time

from xaidar.filesUtils import loadPickle, savePyObj
from xaidar.s3Utils import decryptCredentials, initialize

import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
credKey = os.getenv( "CRED_KEY" )
credDic = decryptCredentials( credKey, Path( "./credentials.enc") )
# Initialize boto3 client
s3 = initialize("XChem", credDic)

def get_object_size(bucket_name, key):
    try:
        response = s3.head_object(Bucket=bucket_name, Key=key)
        return key, response['ContentLength']  # Size in bytes
    except Exception as e:
        return key, f"Error: {e}"

def fetch_sizes_parallel(bucket_name, keys, max_workers=20):
    sizes = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {executor.submit(get_object_size, bucket_name, key): key for key in keys}
        for future in as_completed(future_to_key):
            key, size = future.result()
            sizes[key] = size
    return sizes

for bucket_name in [ "xchem", ]:# "pandda",
    # bucket_name = "xchem"
    for frag in Path( f"./data/s3ObjKeys/{bucket_name}" ).iterdir():
        if frag.is_file():
            if frag.name == "frag4.pkl":
                pass
            else:
                keys = loadPickle( frag )[1:]
                start = time.time()
                print(f"Started with {frag.name[:-4]} for {bucket_name}")
                sizes = fetch_sizes_parallel( bucket_name, keys, max_workers=40 )
                print( f"Fetched sizes in {time.time() - start} seconds")

                savePath = Path("./data/s3Sizes").joinpath( bucket_name, f"{frag.name[:-4]}_sizes.pkl" ).resolve()
                print( "Saved Path: {}".format( savePath ) )    
                savePath.parent.mkdir( parents=True, exist_ok=True )
                savePyObj( sizes, savePath ) 
                print( f"Saved {bucket_name}-{frag.name[:-4]}_sizes.pkl: { time.time() - start }" )
    #         break
    #     break
    # break
