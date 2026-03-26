from pathlib import Path
import shutil
import pandas as pd
import gemmi
import pathlib

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

def create_ligand_file( residueSpan, pdb_name = None, save_path = None):

    st = gemmi.Structure()
    
    if pdb_name: st.name = pdb_name
    else: st.name = "ligand"

    model = gemmi.Model(1)
    chain = gemmi.Chain( "A")

    for residue in residueSpan:
        chain.add_residue( residue)

    model.add_chain( chain )
    st.add_model( model )

    if save_path:
        st.write_pdb(save_path, gemmi.PdbWriteOptions() )
    pass


def extractLigands( pdb_st: gemmi.Structure, saveDirPath: pathlib.Path, protName: str ):
    """
    Extracts ligands from a PDB structure and saves them as individual PDB files.
    Args:
    - pdb_st (gemmi.Structure): The PDB structure object containing the ligands.
    - saveDirPath (pathlib.Path): The directory path where the ligand PDB files
    - protName (str): The name of the protein, used to name the ligand PDB files.
    Returns:
    - None: The function saves the ligand PDB files to the specified directory.
    """

    saveDirPath.mkdir( parents=True, exist_ok=True)
    if len(pdb_st) == 1:
        model = pdb_st[0]
        for chain in model:
            if chain.get_ligands():
                print( f"Processing Chain: {chain.name }")
                resSpan =  chain.whole() 
                ligName = list( set( resSpan.extract_sequence() ) )
                if len(ligName) > 1:
                    print( f"Bad arrangement of ligands with more than one in a chain: {ligName}" )
                    for lig in ligName:
                        ligPDBName = f"{protName}_{lig}.pdb"

                        for residue in chain.whole():
                            print(residue.name)
                            # Continue code

                else:
                    print( f"Processing Ligand: {ligName[0]}")
                    ligPDBName = f"{protName}_{ligName[0]}.pdb"
                    saveFilePath = saveDirPath / ligPDBName
                    saveFilePath = saveFilePath.resolve().as_posix().__str__()
                    create_ligand_file( resSpan, ligPDBName, saveFilePath)


    elif len(pdb_st) == 0:
        print( "Error with Model")
    else:
        print("More than one model")

def extractAllLigands(lst_pdbPaths, saveDirPath=None):
    """
    Extracts ligands from a list of PDB file paths and saves them to a specified directory.
    Args:
    - lst_pdbPaths (list): A list of paths to PDB files.
    - saveDirPath (pathlib.Path, optional): The directory path where the ligands will be saved.
        - If None, a default path is used.
    
    Returns:
    - None: The function saves the ligand PDB files to the specified directory.
    """
    # saveDirPath = Path( "../../../data/s3Data/02-ligandPDBs")
    for path in lst_pdbPaths: # glob.glob("../../../data/s3Data/01-refinedBoundPDBs/*.pdb"):
        boundProtPath = Path(path)
        print(boundProtPath.resolve())
        protName = boundProtPath.name[:-4] # remove .pdb extension
        print(f"Protein Name: {protName}")
        pdb = gemmi.read_pdb(boundProtPath.resolve().as_posix() )
        pdb.setup_entities()
        pdb.assign_label_seq_id()
        extractLigands( pdb, saveDirPath, protName )

def prepPyMOLVisualization(filePath, lst_paths, lst_names = None ):
    """
    Prepares a text file for PyMOL visualization of ligands.
    Args:
    - filePath (str): The path to the output text file.
    - lst_paths (list): A list of paths to the ligand PDB files.
    - lst_names (list, optional): A list of names corresponding to the ligand PDB files.
    
    Returns:
    - None: The function writes the ligand paths and names to the specified text file.
    """
    # lst_paths = glob.glob("../../../data/s3Data/02-ligandPDBs/NUDT7A*LIG.pdb")
    # filePath = Path("../../../../PyMOL/load_NUDT7A_LIG.txt").resolve()
    with open( filePath , 'w') as file:
        if lst_names:
            for path, name in zip(lst_paths, lst_names):
                pathStr = Path(path).resolve().as_posix() 
                file.write(f"{pathStr}   {name}\n")
        else:
            for path in lst_paths:
                pathStr = Path(path).resolve().as_posix() 
                ligNumb = Path(path).name[8:-4] 
                file.write(f"{pathStr}   {ligNumb}\n")


if __name__ == "__main__":
    # get_refine_bound_pdbs()
    print("Hi")
