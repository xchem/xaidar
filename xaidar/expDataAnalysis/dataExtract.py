from pathlib import Path
import shutil
import pandas as pd

from xaidar.filesUtils import savePyObj


def get_refine_bound_pdbs():
    boundPdbDir = Path("./data/s3Data/01-refinedBoundPDBs")
    boundPdbDir.mkdir(parents = True, exist_ok = True)

    depoTo01Map = pd.DataFrame(columns=["Depo-dir",  "Depo-file", "01-file"])

    depositedDir = Path("./data/s3Data/Deposited")
    for sessionDir in depositedDir.iterdir():
        if sessionDir.is_dir():
            for boundPdbFile in sessionDir.glob("*refine.split.bound-state.pdb"):
                datasetName = boundPdbFile.name.split("_")[0]
                newFileName = f"{datasetName}.pdb"
                newFilePath = boundPdbDir / newFileName
                shutil.copy(boundPdbFile, newFilePath)
                depoTo01Map.loc[ int(len(depoTo01Map)+1) ] = [ sessionDir.name, boundPdbFile.name, newFileName ]

    MapPath = Path("./data/s3Data/00-fileMaps/depoTo01Map.pkl")
    savePyObj( depoTo01Map, MapPath)
    print( "Finished Moving all the Bound State Refined PDBs")



if __name__ == "__main__":
    # get_refine_bound_pdbs()
    print("Hi")
