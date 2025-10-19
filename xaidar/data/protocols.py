# Integrating Existing functions into Protocols
from pathlib import Path

import gemmi

from xaidar.data.molecModels import sele_pdb, sele_model, sele_Lig, sele_AA, sele_closest_Chain 
from xaidar.data.molecModels import flatten_pdb
from xaidar.data.molecModels import get_res_CoM

def protein_processing(pdb: gemmi.Structure) -> gemmi.Structure:
    """
    Get single model, single amino acid chain, closest to the ligand
    """
    pdb = sele_pdb( pdb, sele_model)
    lig_pdb = sele_pdb( pdb, sele_Lig)
    lig = flatten_pdb( lig_pdb, level = "residue")
    lig_CoM = get_res_CoM( lig)[0]
    lig_CoM = gemmi.Position( *lig_CoM)
    pdb = sele_pdb( pdb, sele_AA)
    pdb = sele_pdb( pdb, sele_closest_Chain, lig_CoM)
    return pdb


def load_and_filter_Proteins( datasets_dir: Path,
                             mean_CoM: gemmi.Position ,
                             ) -> tuple[list[gemmi.Structure], dict]:
    """
    Load and filter protein structures based on proximity to a given center of mass (CoM).
    Args:
    - datasets (list[str]): List of dataset names.
    - fileTypes (list[str]): List of file types corresponding to each dataset.
    - mean_CoM (gemmi.Position): Center of Mass coordinates. 
            Defaults to mean_CoM.

    Returns:
    - tuple[list[gemmi.Structure], dict]: Tuple containing the list of filtered 
    protein structures and a log dictionary with stats.     
    """
    lst_prots = []                                                                # List to Save filtered proteins
    prot_logs = {"sequence": [], "chainSize":[], "NumChains":[], "NumModels":[]}  # Log dictionary with stats for filtered proteins
    
    datasets = [ dataset.name for dataset in datasets_dir.iterdir()            
            if dataset.is_dir() ]
    for dataset in datasets:                                                    # Loop over datasets
        # print( "\n########################")
        # print("Processing dataset: ", dataset, "\n")
        pdb = gemmi.read_pdb( str(datasets_dir /                                # Load PDB
                                    "{}/{}.pdb".format(dataset, dataset) ))

                                                                                # Filtering
        allProts = sele_pdb( pdb, sele_AA)                                          # Get a.a.s (all models and chains and residues that are a.a.s)

        coord = gemmi.Position( *mean_CoM )                                         # Get chains closest to mean CoM
        prot_chainList=sele_closest_Chain(flatten_pdb(allProts,"chain"), coord) 
                                                                                # Save selected chains in new structure
        prot = allProts.clone()
        chain_names = [ chain.name for chain in prot[0]]
        for chain_name in chain_names: del  prot[0][chain_name[0]]                  # Create empty structure, delete all chains 
        for chain in prot_chainList: prot[0].add_chain( chain)                      # Add selected chains to new structure
                                                                                # Log stats for filtered proteins                 
        startChain = [ chain.name for chain in prot[0]][0]
        prot_logs["sequence"].append( "".join([ res.name for res                    # Get sequence of first chain
                                            in prot[0][startChain].whole()]) )
        prot_logs["chainSize"].append( len(prot[0][startChain]) )                   # Get size of first chain            
        prot_logs["NumChains"].append( len(prot[0]) )                               # Get number of chains                      
        prot_logs["NumModels"].append( len(prot) )                                  # Get number of models 
        lst_prots.append( prot)

    return lst_prots, prot_logs

def extract_lig_from_prot( datasets_dir: Path):
    lst_ligs = []                                                                # List to Save filtered proteins
    prot_logs = {"sequence": [], "chainSize":[], "NumChains":[], "NumModels":[]}  # Log dictionary with stats for filtered proteins
    
    datasets = [ dataset.name for dataset in datasets_dir.iterdir()            
            if dataset.is_dir() ]
    for dataset in datasets:
        pdb = gemmi.read_pdb( str(datasets_dir /                                # Load PDB
                            "{}/{}.pdb".format(dataset, dataset) ))  
        lig =  sele_pdb( pdb, sele_Lig)                                         # Extract LIG   
        num_res = len( flatten_pdb( lig, "residue") )
        if num_res == 0: lst_ligs.append( None )                            
        elif num_res > 0: lst_ligs.append( lig )                                                   # Append to list
        else: raise ValueError("Error in extracting LIG from PDB: {}".format(dataset))
    return lst_ligs 
