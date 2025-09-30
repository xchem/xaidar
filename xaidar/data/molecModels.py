from pathlib import Path
from typing import Callable
from copy import deepcopy

import gemmi
import numpy as np


def loadPDB( pdbPath: Path | str ):
    return gemmi.read_pdb( str(pdbPath) )

def createPDB( molecObj: gemmi.Structure | None = None, 
              modelList: list[ gemmi.Model]  | None = None,
              chainList: list[ gemmi.Chain ] | None = None,
              residSpan: gemmi.ResidueSpan | None = None, 
              atomList: list[gemmi.Atom]| None = None   ):
    """
    Only add a list with several items to the last argument of the hierarchy.
    """
    
    if not molecObj: new_molecObj = gemmi.Structure()
    if not modelList: new_model = [ gemmi.Model(1) ]
    if not chainList: new_chain = [ gemmi.Chain( "A") ]
    if not residSpan:
        new_residSpan = []
        resid = gemmi.Residue()
        resid.name = "MOL"
        new_residSpan.append( resid )
    
    if atomList:
        for atom in atomList:
            new_residSpan[0].add_atom( atom )
        residSpan = new_residSpan
    if  residSpan:
        for resid in residSpan: new_chain[0].add_residue( resid )
        chainList = new_chain
    if chainList:
        for chain in chainList: new_model[0].add_chain( chain )
        modelList = new_model
    if modelList:
        for model in modelList: new_molecObj.add_model( model )
        molecObj = new_molecObj
    return molecObj

def savePDB( structure: gemmi.Structure, outPath: Path | str):
    structure.write_pdb( str(outPath) )
    return None

### Format pdbs functions

def clear_empty(pdb):
    """ Remove empty Models, Chains, Residues from a gemmi.Structure object."""
    for model_id, model in enumerate(pdb):
        for chain in model:
            delete_list = [ resi_id for resi_id, residue in enumerate(chain) 
                                                        if len(residue) == 0]
            delete_list = delete_list[::-1]
            for resi_id in delete_list: del pdb[ model_id ][chain.name][resi_id]
    for model_id, model in enumerate(pdb):
        delete_list = [chain.name for chain in model if len(chain) == 0]
        for chain_name in delete_list: del pdb[ model_id ][chain_name]
    for model_idx, model in enumerate(pdb):
        if len(model) == 0: del pdb[model_idx]
    return pdb
### Extract information functions

def get_pdb_stats(structure: gemmi.Structure):
    print( "Number of models: {}".format( len(structure) ) )
    model = structure[0]
    print( "Number of chains in 1st Model: {}".format( len(model) ) )
    print()
    chain_ids = [ chain.name for chain in model ]
    chain_ids.sort()
    for  chain_id in  chain_ids:
        print( "Chain ID: {}".format( chain_id ) )
        print( "\tNumber of Residues: {}".format( len(model[chain_id]) ) )
        print( "\tUnique List of Non-A.A.: {}".format(
            set( [ res.name for res in model[chain_id] if 
                  not gemmi.find_tabulated_residue(res.name).is_amino_acid()] ) )  )
        if any([gemmi.find_tabulated_residue(res.name).is_amino_acid()
                for res in model[chain_id] ]):
            print( "\tContains A.A." )
    return None

def get_res_coords( res):
    array = np.array( [[atom.pos.x, atom.pos.y, atom.pos.z] for atom in res] )
    return array

def get_res_atomMass( res):
    masses = np.array( [ [atom.element.weight] for atom in res] )
    return masses

def get_res_CoM( res):
    coords = get_res_coords( res )
    mass = get_res_atomMass( res )
    cm = np.sum( coords * mass, axis=0) / np.sum(mass)
    return cm

def get_CoM( coords_array: np.ndarray, mass_array: np.ndarray):
    cm = np.sum(  mass_array * coords_array, axis = 0 ) / np.sum(mass_array)
    return cm


### Selection functions

def sele_pdb(pdb: gemmi.Structure, level: str, selection : Callable, *args,
                                                        ) -> gemmi.Structure:
    """
    Perform filtering on a PDB structure based on a specified level and selection.
    Args:
    - pdb (gemmi.Structure): The PDB structure to filter.
    - level (str): The level of filtering ('model', 'chain', 'residue', 'atom').
    - selection (function): A function that takes an element of the specified level
      and additional arguments, returning True if the element should be included.
      - *args: Additional arguments to pass to the selection function.
      Returns:
      - list: A list of elements that meet the filtering selection.
    """
    empty_pdb = deepcopy( pdb ) # Store Object of models
    while len(empty_pdb) > 0: del empty_pdb[0] # Remove everything except Structure level info
    new_pdb = empty_pdb # Create new Structure Object to Store selected elements
  # Looking at models
    if level == 'model': 
        sele_models = selection( pdb, *args) # -> list[ gemmi.Model ]
        for sele_model in sele_models:
            new_pdb.add_model( sele_model ) # Fill Structure with selected Model Objects
    else:
        for model_id, model in enumerate(pdb):
            empty_model = gemmi.Model(model_id + 1 ) # Add Model attribute .num
            new_pdb.add_model( empty_model ) # Create Model Object without chains (empty)
  # Looking a chains
            new_model = new_pdb[-1] # Call Last Empty Model Object to Store chains in
            if level == 'chain': 
                sele_chains = selection( model, *args) # -> list[ gemmi.Chain ]
                for sele_chain in sele_chains:
                    new_model.add_chain( sele_chain )
            else:
                for chain in model:
                    empty_chain = gemmi.Chain(chain.name)
                    new_model.add_chain( empty_chain ) # Create Chain Object without residues
  # Looking at residues 
                    new_chain = new_model[chain.name] # Call Emtpy Chain Object to Store residue Objects in 
                    if level == 'residue':
                        sele_residues = selection( chain, *args) # list[ gemmi.Residue ]
                        for sele_residue in sele_residues: 
                            new_chain.add_residue( sele_residue )
                    else:
                        for residue in chain:
                            empty_resi = deepcopy( residue )
                            while len( empty_resi) > 0 : del empty_resi[0] # Only keep residue level info, delete all atoms
                            new_chain.add_residue( empty_resi ) # Create Residue Object without atoms
  # Looking at atoms                          
                            new_residue = new_chain[-1] # Store Object of atoms
                            if level == 'atom':
                                sele_atoms = selection( residue, *args) # list[ gemmi.Atom ]
                                # if sele_atoms != []:
                                for sele_atom in sele_atoms:
                                    new_residue.add_atom( sele_atom )
                            else:
                                raise ValueError(("Invalid level specified. "
                            "Choose from 'model', 'chain', 'residue', or 'atom'."))
    # Remove empty Models, Chains, Residues from resulting Structure    
    new_pdb = clear_empty(new_pdb)

    return new_pdb

def sele_Lig( chain: gemmi.Chain ):
    return [ res for res in chain if res.name == "LIG" ]

def sele_res( pdb: gemmi.Structure, conditions: dict | None 
                                                    ) ->list[ gemmi.Residue]:
    """ Select residues from a gemmi.Structure based on given conditions.

    Args:
        pdb (gemmi.Structure): Gemmi Structure object containing the model data.
        conditions (dict | None): Dictionary of selection conditions. 
            Supported keys include 'chain', 'resname', 'seqid', 'entity_type', 'entity_id'.
            If None, all residues are selected.
    Returns:
        list[gemmi.Residue]: List of residues that match the selection conditions.
    """
    selected_residues = []
    for model in pdb:
        for chain in model:
            if "chain" in list(conditions.keys()):
                if chain.name != conditions["chain"]:
                    continue
            for residue in chain:
                match = True
                if conditions:
                    for key, value in conditions.items():
                        if key == 'resname' and residue.name not in value:
                            match = False
                            break
                        elif key == 'seqid' and residue.seqid.num != value:
                            match = False
                            break
                        elif key == 'entity_type' and residue.entity_type != value:
                            match = False
                            break
                        elif key == 'entity_id' and residue.entity_id != value:
                            match = False
                            break
                if match:
                    selected_residues.append(residue)
    return selected_residues



def find_inter_aas(prot: gemmi.Structure, lig: gemmi.Structure ):
    """
    Identifies amino acids that are at a distance of 4A from any atom of the ligand.
    Args:
    - prot (gemmi.Structure): 
    - lig (gemmi.Structure):
    Output
    - gemmi.Structure: Object with the identified interacting a.a.
    """

    inter_aas = gemmi.Structure()
    inter_aas.add_model()
    inter_aas[0].add_chain()

    lig_com = get_res_CoM(lig[0][0][0]) 
    lig_com_pos = gemmi.Position( lig_com[0], lig_com[1], lig_com[2])

    for model in prot:
        for chain in model:
            for res in chain:
                dist = res.get_ca().pos.dist(lig_com_pos)
                if dist > 10.0:
                    continue
                for lig_atom in lig[0][0][0]:
                    for atom in res:
                        dist = atom.pos.dist(lig_atom.pos)
                        if dist < 4.0:
                            inter_aas[0][0].add_residue(res)
                            break

    return inter_aas


