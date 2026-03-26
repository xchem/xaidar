# This aims at extracting all the keys from object storage and save them to specific file directories
# This can be used in the future to update object storage statistics

from pathlib import Path
import sys
sys.path.insert(0, str(Path("../../").resolve().absolute().__str__()))
from time import time

from xaidar.filesUtils import loadPickle, savePyObj
from xaidar.s3Utils import decryptCredentials, initialize, iterateObjStore, lstAllKeys

startTime = time()

# Initialize S3 client
import os
credKey = os.getenv( "CRED_KEY" ) 
credPath =  Path( "../../credentials.enc").resolve()
credDict = decryptCredentials( credKey, credPath )
client = initialize( "XChem", cred_dict=credDict)

# First Check Bucket Names

response = client.list_buckets()
bucketsList = [ bucket["Name"] for bucket in response['Buckets'] ]
print( "Available Buckets:", bucketsList )

if set( ['xchem', 'pandda']) <= set(bucketsList):
    print("xchem and pandda are found in the object store")
else:
    raise Exception("Expected buckets not found in the object store (xchem and pandda).")

from xaidar.s3Utils import getBucketSize

# Define the cache directory

cacheDir = Path("../../data/s3ObjKeys")

for bucket, fragsize in zip( ['xchem' ], [1e4] ):# 'pandda', 1e2, 
    # Get all keys from the bucket
    print(f"Processing bucket: {bucket} with fragment size: {fragsize*1000}")
    # Iterate over the object store and get all object sizes
    iterateObjStore( bucket, client, function = lstAllKeys, 
                    save = True, savePath = cacheDir / bucket / "raw", 
                    frag = True, fragSize = fragsize  )

print(f"Finished processing in {time() - startTime:.2f} seconds")