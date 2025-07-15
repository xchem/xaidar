# xaidar associated with S3 operations

import os
from pathlib import Path
import sys
import boto3
import pickle
import numpy as np
from datetime import datetime
import re
import concurrent
import json
from cryptography.fernet import Fernet

from xaidar.filesUtils import savePyObj, saveList, roundBytes, loadPickle

# Current Accessible S3 Storage Systems
cred = {"XChem":                            # For xchem, the credentials can be found in credentials.enc or dls_keys.zip
                {"endpoint_url": None ,
                    "access_key": None ,
                    "secret_key": None,
             },
        "MinIO":
                {"endpoint_url": "https://play.min.io" ,
                    "access_key": "Q3AM3UQ867SPQQA43P2F" ,
                    "secret_key": "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
             },
        }

def encryptCredentials( key, credentials_dict, storePath, ):
    """
    Task: Encrypt a python object with credentials information to access XChem
    data storage, and save it into a encryption file.
    Args:
    - key: encryption key used. This should be saved by the user in a safe key storage system.
    - credentials_dict: this is a python dictionary object with the credentials information.
    - storePath: this is a pathlib.Path object with the path and name of the file to store encrypted info.
    """
    # Step 1: Turn key into cipher
    cipher = Fernet(key)
    
    # Step 2: Convert to serialized object (i.e. json) with bytes and encrypt
    plaintext = json.dumps(credentials_dict).encode( 'utf-8' )
    encrypted = cipher.encrypt(plaintext)

    # Step 3: Save encrypted 
    with open( storePath, "wb") as f:
        f.write(encrypted)

    print( f"Saved { storePath.name} in { storePath.parents[0] }")
    pass

def decryptCredentials(key, credentialPath):
    """
    Task: Decrypt credentials data and return it as 
    Args:
    - key: encryption key
    - credentialPath: Path to file with encrypted credentials
    Output:
    - Decrypted credentials dictionary
    """
    # Step 1: Loading Encrypted file
    with open( credentialPath , "rb") as f:
        encrypted = f.read()

    # Step 2: Use the same key used for encryption
    cipher = Fernet(key)  # key must be in bytes

    # Step 3: Decrypt
    decrypted_bytes = cipher.decrypt(encrypted)

    # Step 4: Convert back from json to dictionary
    credentials_dict = json.loads(decrypted_bytes.decode('utf-8'))


    print(f"Object Store Names:{ list( credentials_dict.keys()) }" )
    credNames = list( credentials_dict[ "MinIO" ].keys() )
    print( f"Credentials Associated with each Object Store: { credNames }" )
    
    return credentials_dict

def initialize( store, cred_dict = cred ):
    """
    Args:
    - store: Key from cred Dictionary related to the specific storage being used
    - cred_dict: A dictionary of the form similar to the above with the keys. MinIO is a public available, but for XChem this
                    information should only be loaded in-time when running a programm and stay encrypted otherwise.
    Return
    - boto3.client() object
    """
    storage = store # e.g. "XChem" 
    # sesh = boto3.Session()
    client = boto3.client(
        's3' , # AWS service API being used (it could be sqs, )                 
        aws_access_key_id= cred_dict[storage]["access_key"],  # user ID for a user account  
        aws_secret_access_key= cred_dict[storage]["secret_key"], # password for the user account  
        endpoint_url = cred_dict[storage]["endpoint_url"] ,  # endpoit: hostname / URL of the target service. e.g. 's3' 
        region_name = 'us-east-1'  # specify the region
        # aws_session_token=SESSION_TOKEN,
    )
    return client

#### Get Metadata For All Objects in Data Store ########################################################################################################

def lstAllKeys( response, lstOfKeys):

    if lstOfKeys["Content"] == None: lstOfKeys["Content"] =  [] 

    contToken = response["NextContinuationToken"] if "NextContinuationToken" in response else None
    lstOfKeys[0] = f"NxTkn-{ contToken  }"
    if "Contents" in response:
        lstOfKeys.extend( [ obj["Key"] for obj in response["Contents"] if "Contents" in response ] )

    output = {"size": None, "Content": None}
    output["size"] = len( lstOfKeys )
    output["Content"] = lstOfKeys
    
    return output

def getAllObjSizes( response, objSizes):
    
    if objSizes["Content"] == None: objSizes["Content"] = { "Keys": [], "Sizes": [], "NxToken": None} 

    # print( type(response) )
    contToken = response["NextContinuationToken"] if "NextContinuationToken" in response else None
    objSizes["NxToken"] = f"NxTkn-{ contToken  }"
    if "Contents" in response:
        objSizes["Content"]["Keys"].extend( [ obj["Key"] for obj in response["Contents"] if "Contents" in response ] )
        objSizes["Content"]["Sizes"].extend( [ obj["Size"] for obj in response["Contents"] if "Contents" in response ] )

    objSizes["Size"] = len( objSizes["Content"]["Keys"] )
    
    return objSizes


def iterateObjStore(bucket_name, client, save = True, function = None, saveDir = "ObjStoreContent", fragSize = 1, maxLen = None, frag = True, saveObjContent = None):
    

    """
    This function has many options:
    - Object selection:
        - browse through all objects -> (maxLen = None)
        - browse through the first n objects -> (maxLen = n )
    
    - Output forms:
        - return a list of objects -> (save = False, frag = False)
        - - NOTE: Only use this option for a small size of object keys
        - save a list of objects  -> (save = True)
        - - Save in one pickle file -> (frag = False)
        - - Save in many pickle files -> ( Frag = True )
    
    Args:
    - bucketKey
    - client -> boto3.client object
    - Function: function must output a dictionary with: "size" key = int of number of elements | "content" key = python object that contains information wanted. Args: response & saveObj
    - save (bool) -> if True, it will output pickle files with lists of object keys. If False, will output a list object.
    - saveDir (str) -> Name of directory created to save files
    - fragSize (float) -> Units of  1000
    - maxLen (float)-> Max Number of Objects being iterated. Must be higher than the fragSize to have an effect. That is the minimum size. Same units as fragSize
    - Frag (bool) -> Tells whether to save the resul in small fragment files (True) or in one big file (False)
    Note: For linux users, must alter the f".\\{saveDir}" to /{saveDir}
    
    Return:
    - Save one or more lists (lstKeys), where the 1st element is the nextToken and the rest are the object keys



    """
    
    saveObj = { "Size": 0, "Content" : saveObjContent }
    kwargs = { "Bucket" : bucket_name }
    if fragSize < 1: kwargs["MaxKeys"] = int( 1e3*fragSize )
    fragmentSize = int( 1e3*fragSize )
    fragCount = 1

    response = client.list_objects_v2( **kwargs )
    kwargs["ContinuationToken"]  = response["NextContinuationToken"] if "NextContinuationToken" in response else None
    saveObj = function( response, saveObj )

    # Save first list
    if save:
        Path(f"./{saveDir}").mkdir(exist_ok=True)
        path = Path( f"./{saveDir}", f"frag{fragCount}.pkl" )
        if frag: 
            savePyObj( saveObj, path )
            saveObj = { "Size": 0, "Content" : None }

    while kwargs["ContinuationToken"] != None:
        if  maxLen:
            if fragCount*fragmentSize >= maxLen*1000 and frag:
                break
            elif saveObj["Size"] >= maxLen*1000:
                break
        
        response = client.list_objects_v2( **kwargs )   
        kwargs["ContinuationToken"] = response["NextContinuationToken"] if "NextContinuationToken" in response else None

        saveObj = function(  response, saveObj )

        # Save the current list and reset it for the next fragment of objects 
        if saveObj["Size"] >= fragmentSize and frag and save:
            fragCount += 1
            Path(f"./{saveDir}").mkdir(exist_ok=True)
            path = Path( f"./{saveDir}", f"frag{fragCount}.pkl" )
            savePyObj( saveObj, path )

            saveObj = { "Size": 0, "Content" : None }


    if saveObj != None and save: savePyObj( saveObj, Path( f"./{saveDir}", f"frag{fragCount+1}.pkl" ) )

    if save and frag: print(f"Finished saving around { fragCount*fragmentSize } keys.")
    elif save and not frag: print( "Finished saving around {} keys.".format( saveObj["Size"] ))
    else: return saveObj


#### Get Metadata For The Overall Bucket ################################################

# Get number of files a bucket or several buckets
def getBucketSize(client, bucket_list:list, page_size = 100, maxitems = 1000):
    size = {}
    for bucket_key in bucket_list:
        paginator = client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_key, PaginationConfig = {"PageSize": page_size, "MaxItems":maxitems })
        size[bucket_key] = page_size * ( len( [ None for _ in pages ] ) - 1 )
        # for page in pages:
        #     for obj in page['Contents']:
        #         print(obj['Key'], obj['Size'], obj['LastModified'])
    return size

def getBucketSize_v2(bucket, client, keysDirPath, max_workers = 30):
    """
    Task: Load several lists of pickle files with object keys, obtains the size
    of each object, and sums together the total bucket size. It does so in parallel.

    Args:
    - bucket (str): Name ID of bucket in object store
    - client: AWS client used to access the object store
    - keysDirPath: Path to a directory of pickle files, where each file corresponds to 
                a list object of object keys for the corresponding bucket.
    - max_workers: The number of threads to run simultaneously in parallel.
    """
    lstLstObjectKeys = [ loadPickle( os.path.join( keysDirPath,
                        file)  )[1:] for file in os.listdir( keysDirPath ) ] 
    # [1:] bc the first element represents a continuation token instead of a key
    print(f"Loaded {bucket} List of List of Object Keys")
    BucketSize = sum( [parallelObjectSize( bucket, client, lstObjectKeys ,
                         max_workers = max_workers) for lstObjectKeys in lstLstObjectKeys])
    print(f"""--------------------------\n
          Finished Measuring {bucket}\n
          --------------------------\n
          """)
    print( f"""There are {roundBytes(BucketSize)} in {bucket} Bucket""")
    return BucketSize




# Outputs a dictionary with the number of objects found in each bucket
def getObjCount(client, bucket_list:list, page_size = 1000 , maxitems = 10000 ):
    size = {}
    for bucket_key in bucket_list:
        paginator = client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_key, PaginationConfig = {"PageSize": page_size, "MaxItems":maxitems } )
        size[bucket_key] = sum( [ len( page[ "Contents"] ) for page in pages if "Contents" in page ] )
    return size



########## Get Metadata for specific Object lists ########################################################################################

def getObjectSize( bucket, client, objectList : list ):
    """
    Get the size of one object, several objects, or a whole bucket.
    Note that if using listKeys, you get a list of objects with content. Other
    """
    bucketByteSize = 0
    bucketSize = ""
    for key in objectList:
        # print( client.head_object( Bucket = bucket, Key = key)["ContentLength"]  )
        bucketByteSize += int( client.head_object(  Bucket = bucket, Key = key)["ContentLength"] )

    units = ['Byte', 'KB', 'MB', 'GB', 'TB']
    for n, unit in  zip( range( 0, 13, 3), units) :
        if bucketByteSize >= 1*10**n: bucketSize = f"{ bucketByteSize // (1*10**n) }{unit}"
        else: break

    print( bucketSize )    
    return bucketByteSize

# ### GPT Vibe Code 
# def getObjSizes(bucket_name, client):
#     """
#     Efficiently lists the size of each object in an S3 bucket.

#     Args:
#         bucket_name (str): The name of the S3 bucket.
#     """

#     paginator = client.get_paginator('list_objects_v2')

#     try:
#         # Create a PageIterator from the Paginator
#         page_iterator = paginator.paginate(Bucket=bucket_name)

#         print(f"Object sizes in bucket: {bucket_name}\n")

#         for page in page_iterator:
#             if "Contents" in page:
#                 for obj in page['Contents']:
#                     # obj is a dictionary containing metadata
#                     key = obj['Key']
#                     size = obj['Size'] # Size in bytes
#                     print(f"Key: {key}, Size: {size} bytes")
#             break

#     except Exception as e:
#         print(f"An error occurred: {e}")

def parallelObjectSize(bucket, client, lstObjectKeys, max_workers = 10):
    
    """
    Get the size of one object, several objects, or a whole bucket with multithreading.
    """
    size = 0
    
    def measureObject( bucket, client, objectKey ):
        return int( client.head_object(  Bucket = bucket, Key = objectKey)["ContentLength"] )
    
    with concurrent.futures.ThreadPoolExecutor( max_workers = max_workers ) as executor:
        futuresLst = [ executor.submit( measureObject, bucket, client, objectKey) for 
                    objectKey in  lstObjectKeys ]
        for future in  concurrent.futures.as_completed( futuresLst):
            size += future.result()
    
    units = ['Byte', 'KB', 'MB', 'GB', 'TB']
    for n, unit in  zip( range( 0, 13, 3), units) :
        if size >= 1*10**n: bucketSize = f"{ size // (1*10**n) }{unit}"
        else: break
    
    print(bucketSize)
    return size 



def uploadManyFiles( bucket, client, objectNames:list, filesPaths: list, ):

    def uploadFile( bucket, client, objectName, filePath, ):
        with open( filePath, "rb") as file:
            file_data = file.read()
            # file_size = len(file_data)
            # print(file.readlines() )
            # bytes_encode = file.enco("utf-8")
            response = client.put_object(
                Body = file_data ,
                # ContentLength = file_size, 
                Bucket = bucket,
                Key = objectName,
                Metadata = {
                    "Message": "This object contains a test file without any value."
                },
            )

    runCode = [ uploadFile( bucket, client, name, path, ) for name, path in zip(objectNames, filesPaths )]
    print("Finished upload")


########### Obsolete Code ###################################

#####  New Version is iterateObjStore( function = lstKeys )
# def listKeys(bucketKey: str, client, save = True,  saveDir = "SavedLsts", fragSize = 1, maxLen = None, frag = True):
#     """
#     This function has many options:
#     - Object selection:
#         - browse through all objects -> (maxLen = None)
#         - browse through the first n objects -> (maxLen = n )
    
#     - Output forms:
#         - return a list of objects -> (save = False, frag = False)
#         - - NOTE: Only use this option for a small size of object keys
#         - save a list of objects  -> (save = True)
#         - - Save in one pickle file -> (frag = False)
#         - - Save in many pickle files -> ( Frag = True )
    

#     Args:
#     - bucketKey
#     - client -> boto3.client object
#     - save (bool) -> if True, it will output pickle files with lists of object keys. If False, will output a list object.
#     - saveDir -> Name of directory created to save files
#     - fragSize -> Units of  1000
#     - maxLen -> Max Number of Objects being iterated. Must be higher than the fragSize to have an effect. That is the minimum size. Same units as fragSize
#     - Frag (bool) -> Tells whether to save the resul in small fragment files (True) or in one big file (False)
#     Note: For linux users, must alter the f".\\{saveDir}" to /{saveDir}
    
#     Return:
#     - Save one or more lists (lstKeys), where the 1st element is the nextToken and the rest are the object keys 
#     """
#     kwargs = { "Bucket" : bucketKey }
#     if fragSize < 1: kwargs["MaxKeys"] = int( 1e3*fragSize )
#     fragmentSize = int( 1e3*fragSize )
#     fragCount = 1
#     if os.path.exists( f".\\{saveDir}"):
#         dirIdx = len( [ dir for dir in os.listdir(".") if re.search(f"^{saveDir}", dir) ] ) + 1  
#         saveDir = f"{saveDir}_{dirIdx}"


#     response = client.list_objects_v2( **kwargs )
#     kwargs["ContinuationToken"]  = response["NextContinuationToken"] if "NextContinuationToken" in response else None
#     contToken = kwargs["ContinuationToken"] 
#     lstKeys = [ f"NxTkn-{  contToken }" ]
#     lstKeys.extend( [ obj["Key"] for obj in response["Contents"] if "Contents" in response ] )

#     # Save first list
#     if save:
#         if not os.path.exists( f".\\{saveDir}"): os.mkdir(saveDir )
#         path = os.path.join( f".\\{saveDir}", f"frag{fragCount}.pkl" )
#         if frag: 
#             saveList( lstKeys, path )
#             contToken = kwargs["ContinuationToken"]
#             lstKeys = [ f"NxTkn-{ contToken  }" ]

#     while kwargs["ContinuationToken"] != None:
#         if  maxLen:
#             if fragCount*fragmentSize >= maxLen*1000:
#                 break
        
#         response = client.list_objects_v2( **kwargs )   
#         kwargs["ContinuationToken"] = response["NextContinuationToken"] if "NextContinuationToken" in response else None
#         contToken =  kwargs["ContinuationToken"]
#         lstKeys[0] = f"NxTkn-{ contToken  }"
#         if "Contents" in response:
#             lstKeys.extend( [ obj["Key"] for obj in response["Contents"] if "Contents" in response ] )

#         # Save the current list and reset it for the next fragment of objects 
#         if len( lstKeys) >= fragmentSize and frag and save:
#             fragCount += 1
#             if not os.path.exists( f".\\{saveDir}"): os.mkdir(saveDir )
#             path = os.path.join( f".\\{saveDir}", f"frag{fragCount}.pkl" )
#             saveList( lstKeys, path )
#             contToken =  kwargs["ContinuationToken"]
#             lstKeys = [ f"NxTkn-{ contToken }" ]


#     if len( lstKeys ) > 0 and save: saveList( lstKeys, os.path.join( f".\\{saveDir}", f"frag{fragCount+1}.pkl" ) )

#     if save and frag: print(f"Finished saving around { fragCount*fragmentSize } keys.")
#     elif save and not frag: print(f"Finished saving around { len( lstKeys ) } keys.")
#     else: return lstKeys



# # Used before fragLstObjectKeys() created
# # Outputs a dictionary with a list of object keys for each bucket
# def objectKeys(client, bucket_list:list, page_size = 1000 , maxitems = 10000 , save = False, save_path = None, fragment = False ):
#     """
#     Obsolete -> use 
#     fragment: None or int -> tells 

#     """
#     lst_keys = {}
#     nextToken = None
#     count = 0
#     if fragment: os.mkdir( "ObjectKeys" )
#     for bucket_key in bucket_list:
#         paginator = client.get_paginator('list_objects_v2')
#         pages = paginator.paginate( Bucket=bucket_key, PaginationConfig = {"PageSize": page_size, 
#                                                                           "MaxItems":maxitems, 
#                                                                           "StartingToken" : nextToken } )
#         for page in pages:
#             if "Contents" in page:
#                 lst_keys[bucket_key] =  [  obj["Key"] for obj in page[ "Contents" ] ]
#         if fragment and len( lst_keys[bucket_key] ) >= fragment:
#             count+=1
#             nextToken = next( iter( pages ) )["NextContinuationToken"] 
#             lst_keys["NextContinuationToken"] = nextToken
#             saveList( lst_keys,  os.path.join(f".\\ObjectKeys\\Bucket_{bucket_key}_pt{count}.pkl"), readMe = f"This contains a fragment of the whole list of object keys present in the bucket {bucket_key}" )
#             lst_keys = {}

                
            
#         # lst_keys[bucket_key] =  [  obj["Key"] for page in pages for obj in page[ "Contents"] if "Contents" in page ] 
#     if save:
#         lst_keys["ReadMe"] = "This dictionary contains bucket keys as keys and a list of all object keys present in such bucket as values"
#         if save_path != None:
#             with open(save_path, "wb") as file:
#                 pickle.dump( lst_keys, file)
#         elif save_path == None:
#             save_path = os.path.join( os.getcwd(),  f"{ datetime.today().strftime("%Y%m%d-%H%M") }_objectKeysDict.pkl" )
#             with open(save_path, "wb") as file:
#                 pickle.dump( lst_keys, file)
#         else: raise Exception( "There is an error with the save_path argument" ) 

#     return lst_keys



