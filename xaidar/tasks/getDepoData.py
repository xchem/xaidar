import sys
from pathlib import Path

from xaidar.filesUtils import loadPickle
from xaidar.sqliteUtils import loadDatabase

# Get 2017 soakDB data
DBdir = Path("./data/soakDB/xchem/data").resolve().absolute()
sessions = [item for item in DBdir.iterdir() if item.is_dir()]

idx = 0

# Identify Sessions with Deposited Structures
refinedPathCif = []
refinedCrystal = []
sessionsCount= 0

refinedLog = {}
for session in sessions:
    sessionName = session.name
    DBfile = session / "database" / "soakDBDataFile.sqlite"
    db = loadDatabase( DBfile )
    mainDB = db["mainTable"]

    if "RefinementOutcome" in mainDB.columns.values:
        refined = mainDB[ (mainDB[ "RefinementOutcome" ] == "6 - Deposited") &
                        (mainDB[ "RefinementStatus" ] == "finished")
                        ]
        
        if len(refined) > 0:
            refinedLog[sessionName] = {"CifPath": list( refined["RefinementCIF"].values) ,
                                       "PDBPath": list( refined["RefinementPDB_latest"].values) ,
                                       "CrystalName":list( refined["CrystalName"].values) 
                                       }
            sessionsCount += 1
            refinedPathCif.extend( list( refined["RefinementCIF"].values) )
            refinedCrystal.extend( list( refined["CrystalName"].values) )

print(f"Found {sessionsCount} sessions with deposited structures")
print(f"Found {len(refinedPathCif)} deposited structures in total")


import re
from collections import defaultdict

# Get Folders of Interst:
    # Re-structure path to deposited pdb structure, to get parent dataset directory 
    # (i.e. /data/2017/lb18145-3/processing/analysis/initial_model/NUDT7A-x0140)
filesofInt = defaultdict( list )
for session in refinedLog:
    print(f"--------{session}----------------")
    for pdbPath, cryst in zip( refinedLog[session]["PDBPath"],  refinedLog[session]["CrystalName"]):
        print(cryst, ": ",re.search(f"/data.*{cryst}", pdbPath).group() )
        filesofInt[session].append( re.search(f"/data.*{cryst}", pdbPath).group()[1:] ) # In current objects, the path starts without a "/"



from xaidar.treeObj import openFolderwPath
from xaidar.s3Utils import decryptCredentials, initialize

credKey = "v6Q2ZQB7FlFgpI_-8OpC-4g7LZA34JKWesfZsYng7Wg="
# credKey = "" #### !!! Must fill this for code to work !!! ####
# credKey = os.getenv( "CRED_KEY" )
credPath =  Path( "./credentials.enc").resolve()
credDict = decryptCredentials( credKey, credPath )
client = initialize( "XChem", cred_dict=credDict)
bucket = "xchem"



# Get corresponding files of interest for each dataset parent folder

keysDir = Path("./data/treeObjs/xchem/data").resolve().absolute()

for session, lst_datasets in filesofInt.items():

    treePath = keysDir / f"tree_{session}.pkl"      # i.e. session = "2017_lb18145-3" 
    tree = loadPickle( treePath )


    for dataset in lst_datasets:
        datasetFilePaths = { "compound.pdb": [], "compound.cif": [], "compound.smiles": [], "dimple.mtz": [], "dimple.pdb": [],
        "mean-map":[], "z_map" : [], "events": [] ,"pandda-model": [], "refined-ground-model":[], "refined-bound-model":[], 
        "refined-mtz" : []}
            
        datasetPath = dataset # i.e. "data/2017/lb18145-3/processing/analysis/initial_model/NUDT7A-x0140"
        datasetName = datasetPath.split("/")[-1] # I.e. "NUDT7A-x0140"
        datasetContent = openFolderwPath( tree["fileTree"], tree["foldersCount"],  datasetPath )

        for item in datasetContent:
            if item == "dimple.mtz": datasetFilePaths["dimple.mtz"].append(datasetPath +"/dimple.mtz" )
            if re.search( "-pandda-input.mtz$", item): datasetFilePaths["dimple.mtz"].append(datasetPath + f"/{item}" )
            if item == "dimple.pdb": datasetFilePaths["dimple.pdb"].append(datasetPath +"/dimple.pdb" )
            if re.search( "-pandda-input.pdb$", item): datasetFilePaths["dimple.pdb"].append( datasetPath + f"/{item}" )
            if re.search( "pandda-model.pdb$", item ): datasetFilePaths["pandda-model"].append(  datasetPath + f"/{item}" )
            if re.search( "ground-state-average-map.native.ccp4$", item ): datasetFilePaths["mean-map"].append( datasetPath + f"/{item}" )
            if re.search( "-ground-state-mean-map.native.ccp4$", item ): datasetFilePaths["mean-map"].append( datasetPath + f"/{item}" )
            if re.search( "z_map.native.ccp4$", item ): datasetFilePaths["z_map"].append( datasetPath +  f"/{item}")
            if re.search( ".+-event_.+-BDC_.+_map.native.ccp4$", item ): datasetFilePaths["events"].append( datasetPath + f"/{item}" )
            
            if re.search( "refine.split.ground-state.pdb$", item): datasetFilePaths["refined-ground-model"].append(datasetPath + f"/{item}" )
            if re.search( "refine.split.bound-state.pdb$", item): datasetFilePaths["refined-bound-model"].append(datasetPath + f"/{item}" )
            if re.search( "refine.mtz$", item): datasetFilePaths["refined-mtz"].append(datasetPath + f"/{item}" )
            
            if item == "compound":
                compoundPath = datasetPath + "/compound"
                compoundContent = openFolderwPath( tree["fileTree"], tree["foldersCount"], compoundPath )
                for compoundItem in compoundContent:
                    if re.search( ".+pdb$", compoundItem): datasetFilePaths["compound.pdb"].append( compoundPath + f"/{compoundItem}" )
                    if re.search( ".+cif$", compoundItem): datasetFilePaths["compound.cif"].append( compoundPath + f"/{compoundItem}" )
                    if re.search( ".+smiles$", compoundItem): datasetFilePaths["compound.smiles"].append( compoundPath + f"/{compoundItem}" )

        # Download files from S3 bucket
        DirName = session # i.e."2017_lb18145-3"
        for filetype, lst_objKey in datasetFilePaths.items():
            if len(lst_objKey) == 0:
                print(f"Warning: No files found for {filetype} in dataset {datasetName} in session {session}.")
                continue
            else:
                for objKey in lst_objKey:
                    dataFileName = objKey.split("/")[-1]
                    # key = treePickle[0] # "data/2019/lb18145-122"
                    storeDir = Path(  "./data/s3Data/Deposited" , DirName )
                    storeDir.mkdir( parents=True, exist_ok=True )

                    storePath = storeDir / f"{datasetName}_{dataFileName}" 
                    try:
                        client.download_file( bucket, objKey, storePath.as_posix() ) 
                    except Exception as e:
                        raise Exception(f"Error downloading {dataFileName} from {objKey} in session {session}:\n\t{e}")
        print(f"Downloaded files for dataset {datasetName} in session {session}")
    print(f"Completed processing session {session}. Total datasets processed: {len(filesofInt[session])}")
print("All sessions processed successfully.")