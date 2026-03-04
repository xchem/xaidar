from pathlib import Path
from typing import Callable
from copy import deepcopy
from io import StringIO

import gemmi
import parasail

from rdkit import Chem
from rdkit.Chem import rdFMCS, AllChem
import py3Dmol

import Bio
from Bio import PDB
from Bio.PDB import PDBParser, MMCIFParser, PDBIO, MMCIFIO

import MDAnalysis as mda

import numpy as np

####################
# Gemmi Tools
####################

def loadPDB( pdbPath: Path | str ):
    return gemmi.read_pdb( str(pdbPath) )

def createPDB( molecObj: gemmi.Structure | None = None, 
              modelList: list[ gemmi.Model]  | None = None,
              chainList: list[ gemmi.Chain ] | None = None,
              resSpan: gemmi.ResidueSpan | None = None, 
              atomList: list[gemmi.Atom]| None = None   ):
    """
    Only add a list with several items to the last argument of the hierarchy.
    """
    
    if not molecObj: new_molecObj = gemmi.Structure()
    if not modelList: new_model = [ gemmi.Model(1) ]
    if not chainList: new_chain = [ gemmi.Chain( "A") ]
    if not resSpan:
        new_resSpan = []
        res = gemmi.Residue()
        res.name = "MOL"
        new_resSpan.append( res )
    
    if atomList:
        for atom in atomList:
            new_resSpan[0].add_atom( atom )
        resSpan = new_resSpan
    if  resSpan:
        for res in resSpan: new_chain[0].add_residue( res )
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
    return pdb if len(pdb) > 0 else None

def flatten_pdb(pdb: gemmi.Structure, level : str)-> (list[ gemmi.Model]| 
                list[gemmi.Chain] | list[gemmi.Residue] | list[gemmi.Atom]) :
	
    """
	This function outputs a list of certain gemmi objects down the gemmi.Structure
	hierarchy for all the objects of that type that live within the gemmi.Structure.
	Args
	- pdb
	- level (str ): options - [ "model", "chain", "residue", "atom"]
    """
    
    if level == "model":
        return [ model for model in pdb ]

    elif level == "chain":
        return [ chain for model in pdb for chain in model ]

    elif level == "residue":
        lst_resdues = [ residue for model in pdb for chain in model 
                                            for residue in chain ]
        return lst_resdues

    elif level == "atom":
        lst_atoms = [ atom for model in pdb for chain in model 
                            for residue in chain for atom in residue ]
        return lst_atoms

    else:
        raise ValueError(("Invalid level specified. "
            "Choose from 'model', 'chain', 'residue', or 'atom'."))

def resList_to_resSpan( res_lst: list[gemmi.Residue]) -> gemmi.ResidueSpan:
    pdb = createPDB(resSpan = res_lst)
    return flatten_pdb( pdb, "chain")[0].whole()

def append_res_to_chain( new_res_lst, prot_chain_tobealtered: gemmi.Chain) -> None:
    """
    
    """
    prot_chain_tobealtered.append_residues( new_res_lst, min_sep = 1 )
    return None

def add_res_to_chain( new_res_lst, new_res_pos_lst, 
                                prot_chain_tobealtered: gemmi.Chain) -> None:
    """
    Alter state of prot_chain_tobealtered object by adding residues to it.
    Args:
    - new_res_lst: list of residues to be added to protein
    - new_res_pos_lst: final position in chain
    Return:
    - None
    """
    if ( ( not isinstance( new_res_lst, list) ) or 
                                ( not isinstance( new_res_pos_lst, list)) ):
        raise ValueError( " new_res, new_res_pos must be lists even "
                                                    "for one element") 
    elif len( new_res_lst) != len( new_res_pos_lst):
        raise ValueError( " new_res, new_res_pos lists must be of same length")

    lst_for_neg_index = [ (num, res) for num, res in 
                                zip( new_res_pos_lst, new_res_lst) if num < 0 ]
    lst_for_neg_index = sorted( lst_for_neg_index, key= lambda x: abs(x[0]))    # Sort negative indexes to process them in correct order
    
    lst_for_pos_index = [ (num, res) for num, res in 
                                zip( new_res_pos_lst, new_res_lst) if num >= 0]
    lst_for_pos_index = sorted( lst_for_pos_index, key= lambda x: x[0])         # So that residues are added in correct order to the right positions

    sorted_pairs = lst_for_neg_index + lst_for_pos_index
    for new_res_pos, new_res  in sorted_pairs:
        if new_res_pos < 0:
            new_res_pos = new_res_pos % len( prot_chain_tobealtered)            # Allow to account for negative indexing
        res_nums = [ res.seqid.num for res in prot_chain_tobealtered]           # get original indexes of old residues
        new_res.seqid.num = res_nums[new_res_pos]                               # update residue to be added seqid.num before adding it 
        new_res_nums = res_nums[:new_res_pos] + [ num + 1 
                                            for num in res_nums[new_res_pos:]]  # get new indexes for old residues          
        for res, new_num in zip( prot_chain_tobealtered, new_res_nums):         # Update old residues with new indexes
            res.seqid.num = new_num
        prot_chain_tobealtered.add_residue(new_res, new_res_pos)                # Add new residue to chain
    return None


### Extract information functions

def get_pdb_stats(structure: gemmi.Structure):
    print("\n####################")
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

# General level functions

def get_CoM( coords_array: np.ndarray, mass_array: np.ndarray):
    cm = np.sum(  mass_array * coords_array, axis = 0 ) / np.sum(mass_array)
    return cm

def get_pairwise_dist( coords_array1: np.ndarray, coords_array2: np.ndarray):
    """ Compute pairwise distance matrix for a set of coordinates.
    Args:
    - coords_array (np.ndarray): Array of shape (N, 3) containing N 3D coordinates.
    Returns:
    - np.ndarray: Pairwise distance matrix of shape (N, N).
    """
    diff = coords_array1[:, np.newaxis, :] - coords_array2[np.newaxis, :, :]      # Broadcasting to get difference matrix  (N,1,3) - (1,M,3) -> (N,M,3)
    dist_matrix =  np.linalg.norm(diff, axis=2)
    return dist_matrix

# Atom level functions

def get_atom_coord( lst_atoms: list[ gemmi.Atom ] ) -> np.ndarray:
    """
    Extract the coordinates of atoms from a list of gemmi.Atom objects.
    Args:
    - flat_pdb (list of gemmi.Atom): List of gemmi.Atom objects.
    Returns:
    - list of tuples: Each tuple contains the (x, y, z) coordinates of an atom.
    """
    coords = np.array([ [atom.pos.x, atom.pos.y, atom.pos.z] for atom in lst_atoms ])
    return coords

def get_atom_weights( lst_atoms: list[ gemmi.Atom ] )-> np.ndarray:
    """
    Extract the weights of atoms from a list of gemmi.Atom objects.
    Args:
    - flat_pdb (list of gemmi.Atom): List of gemmi.Atom objects.
    Returns:
    - list of floats: Each float represents the weight of an atom.
    """
    weights = np.array([ [atom.element.weight] for atom in lst_atoms ])
    return weights

def get_atom_elements( lst_atoms: list[ gemmi.Atom ] ):
    """
    Extract the elements of atoms from a list of gemmi.Atom objects.
    Args:
    - flat_pdb (list of gemmi.Atom): List of gemmi.Atom objects.
    Returns:
    - list of str: Each string represents the element of an atom.
    """
    elements = [ [atom.element.name] for atom in lst_atoms ]
    return elements

# Residue level functions
def get_res_mw( lst_res: list[gemmi.Residue] ) -> np.ndarray:
    lst_mass = [ sum( get_atom_weights( res ) ) for res in lst_res ]
    return np.array( lst_mass )

def get_res_CoM( lst_res: list[ gemmi.Residue ]) -> np.ndarray:
    lst_cm = [get_CoM( get_atom_coord( res ), get_atom_weights( res ) ) 
                                                    for res in lst_res ]
    return np.array( lst_cm )

def get_res_bfactors( lst_res: list[gemmi.Residue] | gemmi.Structure,
                     sign_fig = 3, numpy_Array = False) -> list[float]:
    """ Get the b-factors for a list of residues """
    if isinstance( lst_res, gemmi.Structure):
        lst_res = flatten_pdb(lst_res, "residue")

    bfactors = [ round( float( np.mean( [atom.b_iso for atom in res]) ), sign_fig)
                if  isinstance(res, gemmi.Residue) and len(res) > 0 else None
                                             for res in lst_res ]
    if numpy_Array:
        bfactors = np.array( bfactors )
    return bfactors

# Chain Level Function

def get_chain_seq(lst_chain: list[gemmi.Chain]) -> list[str]:
    """
    Get the amino acid sequence for each chain in a list of gemmi.Chain objects.
    """
    if isinstance( lst_chain, gemmi.Structure):
        lst_chain = flatten_pdb(lst_chain, "chain")
    lst_seqs = []
    for chain in lst_chain:
        if isinstance( chain, gemmi.Chain):lst_res = chain.whole()
        elif isinstance( chain, list) and isinstance( chain[0], gemmi.Residue):
            lst_res = chain
        else: raise ValueError("Input must be a gemmi.Chain or list of " \
        "                                                   gemmi.Residue")
        lst_aa = [gemmi.find_tabulated_residue(res.name).one_letter_code 
                                                    for res in lst_res]
        seq_aa = "".join(lst_aa)
        lst_seqs.append(seq_aa )
    return lst_seqs


### Selection / Filtering / Extraction functions 
# These functions do not alter or process the information in the pdbs 
# into new one

# Return a pdb

def sele_pdb(pdb: gemmi.Structure, selection : Callable, 
                        *args, level: str = None, **kwargs) -> gemmi.Structure:
    """
    Perform filtering on a PDB structure based on a specified level and selection.
    Used to access a specific level of the gemmi.Structure hierarchy and filter
    elements at that level using a provided selection function.
    Args:
    - pdb (gemmi.Structure): The PDB structure to filter.
    - level (str): The level of filtering ('model', 'chain', 'residue', 'atom').
    - selection (function): A function that takes an element of the specified level
      and additional arguments, returning True if the element should be included.
      - *args: Additional arguments to pass to the selection function.
      Returns:
      - list: A list of elements that meet the filtering selection.
    """
    level = selection( pdb, *args, level = True, **kwargs) if level is None else level
    empty_pdb = deepcopy( pdb )                                                     # Store Object of models
    while len(empty_pdb) > 0: del empty_pdb[0]                                      # Remove everything except Structure level info
    new_pdb = empty_pdb                                                             # Create new Structure Object to Store selected elements
                                                                                    # Looking at models
    if level == 'model': 
        sele_models = selection( pdb, *args, **kwargs)                              # -> list[ gemmi.Model ]
        for sele_model in sele_models:
            new_pdb.add_model( sele_model )                                         # Fill Structure with selected Model Objects
    else:
        for model_id, model in enumerate(pdb):
            empty_model = gemmi.Model(model_id + 1 )                                # Add Model attribute .num
            new_pdb.add_model( empty_model )                                        # Create Model Object without chains (empty)
                                                                                    # Looking a chains
            new_model = new_pdb[-1]                                                 # Call Last Empty Model Object to Store chains in
            if level == 'chain': 
                sele_chains = selection( model, *args, **kwargs)                    # -> list[ gemmi.Chain ]
                for sele_chain in sele_chains:
                    new_model.add_chain( sele_chain )
            else:
                for chain in model:
                    empty_chain = gemmi.Chain(chain.name)
                    new_model.add_chain( empty_chain )                              # Create Chain Object without residues
                                                                                    # Looking at residues 
                    new_chain = new_model[chain.name]                               # Call Emtpy Chain Object to Store residue Objects in 
                    if level == 'residue':
                        sele_residues = selection( chain, *args, **kwargs)          # list[ gemmi.Residue ]
                        for sele_residue in sele_residues: 
                            new_chain.add_residue( sele_residue )
                    else:
                        for residue in chain:
                            empty_res = deepcopy( residue )
                            while len( empty_res) > 0 : del empty_res[0]            # Only keep residue level info, delete all atoms
                            new_chain.add_residue( empty_res )                      # Create Residue Object without atoms
                                                                                    # Looking at atoms                          
                            new_residue = new_chain[-1]                             # Store Object of atoms
                            if level == 'atom':
                                sele_atoms = selection( residue, *args, **kwargs)   # list[ gemmi.Atom ]
                                for sele_atom in sele_atoms:
                                    new_residue.add_atom( sele_atom )
                            else:
                                raise ValueError(("Invalid level specified. "
                            "Choose from 'model', 'chain', 'residue', or 'atom'."))
                                                                                    # Remove empty Models, Chains, Residues from resulting Structure    
    new_pdb = clear_empty(new_pdb)

    return new_pdb

    # sele_pdb helper functions ####################

def sele_Lig( lst_res: list[gemmi.Residue], level = False) -> list[gemmi.Residue]:
    if level: return "residue"
    return [ res for res in lst_res if res.name == "LIG" ]

def sele_AA( lst_res: list[gemmi.Residue] , level = False):
    if level: return "residue"
    return [ res for res in lst_res if gemmi.find_tabulated_residue(res.name).is_amino_acid() ]

def sele_HOH( lst_res: list[gemmi.Residue], level = False  ):
    if level: return "residue"
    return [ res for res in lst_res if res.name == "HOH" ]

def sele_metal( lst_atom: list[gemmi.Atom], level = False ):
    if level: return "atom"
    return [ atom for atom in lst_atom if atom.element.is_metal ]

def id_org_res( lst_atom: list[gemmi.Atom], level = False):
    if level: return "atom"
    if any( [ atom.element.name == "C" for atom in lst_atom ]): return True
    else: return False
    
def sele_org( lst_res: list[gemmi.Residue], level = False  ):
    if level: return "residue"
    return [ res for res in lst_res if id_org_res(res) ]

def sele_others( pdb: gemmi.Structure ):
    """Ensure that select from highest to lowest level of hierarchy, for 
    optimal results. I.e. first residues, then atoms."""
    def sele_others_pt1( lst_res: list[gemmi.Residue], level = False  ):
        if level: return "residue"
        return [ res for res in lst_res if 
                not gemmi.find_tabulated_residue(res.name).is_amino_acid() 
                and res.name not in ["HOH", "LIG" ] 
                and not id_org_res(res) ]

    def sele_others_pt2( lst_atom: list[gemmi.Atom], level = False ):
        if level: return "atom"
        return [ atom for atom in lst_atom if 
                not atom.element.is_metal  ]

    others_res = sele_pdb( pdb,  sele_others_pt1, level= "residue") 
    others = sele_pdb( others_res, sele_others_pt2, level= "atom")
    return others

        # Atom Level Function

def sele_C_alpha( lst_atoms: list[gemmi.Atom], level = False) -> list[gemmi.Atom]:
    """
    Extract only the alpha carbon atom in each residue.
    If there is an alpha carbon with alternative locations, a weighted average
    is taken based off of the occupancies.
    """
    if level: return "atom"

    lst_ca = [atom  for atom in lst_atoms  if atom.name == "CA"  ]
    if len( lst_ca) == 1: return lst_ca
    elif len( lst_ca) > 1: 
        new_atom = deepcopy( lst_ca[0])
        occ, pos =  list( zip( *[ ( [atom.occ], atom.pos.tolist() )for atom in lst_ca] ) )
        occ, pos = np.array(occ), np.array( pos)
        new_pos =  np.sum( pos*occ, axis = 0)
        new_atom.pos, new_atom.occ = gemmi.Position( *new_pos), 1.0
        return [new_atom]
    else: raise Exception( "No alpha C found")



        # Residue Level Function

def sele_dist_AA( lst_res: list[gemmi.Residue], coord: gemmi.Position, 
                                        dist: float = 10, level = False ):
    
    """
    Select residues within a specified distance from a given coordinate.
    Args:
    - lst_res (list of gemmi.Residue): List of amino acid gemmi.Residue objects.
    - coord (gemmi.Position): The reference coordinate.
    - dist (float): The distance threshold.
    Returns:
    - list of gemmi.Residue: Residues within the specified distance from the coordinate.
    """
    if level: return "residue"
    return [ res for res in lst_res if 
                res.get_ca().pos.dist( coord ) < dist  ]

def sele_res_idx( lst_res: list[gemmi.Residue], lst_slices: list[ tuple ],
                slice_within = True, level = False  ):
    """
    Select residues from a list based on specified slices.
    Args:
    - lst_res (list[gemmi.Residue]): List of residue objects.
    - lst_slices (list[tuple]): List of tuples specifying slices to remove.
        Must be in (start, end) format, where 'start' is inclusive and 'end' is exclusive.
        The slices should not overlap. The integers must be positive and within the range of lst_res.
    - slice_within (bool, optional): If True, remove residues within the slices.
        If False, remove residues outside the slices. Defaults to True.
    - level (bool, optional): If True, operate at residue level. Defaults to False.
    Returns:
    - list[gemmi.Residue]: Updated list of residue objects after removal.
    """
    if level: return "residue"
    lst_slices = sorted( lst_slices, reverse=True )
    new_lst_res = lst_res if slice_within else []
    for slice_idx in lst_slices:
        start, end = slice_idx
        if slice_within:
            del new_lst_res[start:end]
        else:
            new_lst_res = new_lst_res + lst_res[start:end]
    return new_lst_res


def sele_closest_res( lst_res: list[gemmi.Residue], 
                       CoM: gemmi.Position , verbose = False, 
                       level = False) -> list[gemmi.Chain]:
    
    """
    Select the chain that contains the ligand and is closest to the CoM
    of the protein.
    Args:
    - lst_chains (list[gemmi.Chain]): List of chains in the PDB.
    - CoM (gemmi.Position): Center of Mass of the protein.
    - ligLabel (str, optional): Ligand residue name. Defaults to "LIG".
    Returns:
    - list[gemmi.Chain]: List containing the selected chain.
    """
    if level: return "residue"
    if len(lst_res) == 1:
        if verbose: print("Only one chain in the PDB, returning it")
        return lst_res
    else:
        # Select the chain closest to the CoM
        min_dist = float('inf')
        selected_res = None
        for res in lst_res:
            dist = np.linalg.norm( [get_res_CoM([res])[0], CoM] )
            if dist < min_dist:
                min_dist = dist
                selected_res = res
        return [selected_res]
    

    # Chains level functions

def sele_chain_idx( model: list[gemmi.Chain], lst_idx = [0],level = False, sort = True ):
    if level: return "chain"
    chain_names = [ chain.name for chain in model ]  
    if sort:  chain_names.sort()                  # Ensure alphabetical order
    lst_chains = [ model[chain_name] for chain_name in chain_names ]
    return [ lst_chains[idx] for idx in lst_idx ]

def sele_chain_name( lst_chain: list[gemmi.Chain], level = False, chain_name: 
                                str | list[str]  = None) -> list[gemmi.Chain]:
    """Helper function of sele_pdb, used to extract one or several
    chains into a pdb object based off of their
    """
    if level: return "chain"
    if isinstance( chain_name, str): chain_name = list(chain_name )
    return [ chain for chain in lst_chain if chain.name in chain_name]


def sele_closest_Chain( lst_chains: list[gemmi.Chain], 
                       CoM: gemmi.Position | np.ndarray, verbose = False, 
                       level = False) -> list[gemmi.Chain]:
    
    """
    Select the chain that contains the ligand and is closest to the CoM
    of the protein.
    Args:
    - lst_chains (list[gemmi.Chain]): List of chains in the PDB.
    - CoM (gemmi.Position): Center of Mass of the protein.
    - ligLabel (str, optional): Ligand residue name. Defaults to "LIG".
    Returns:
    - list[gemmi.Chain]: List containing the selected chain.
    """
    if isinstance( CoM, np.ndarray): 
        CoM = gemmi.Position( *CoM.flatten())
    if level: return "chain"
    if len(lst_chains) == 1:
        if verbose: print("Only one chain in the PDB, returning it")
        return lst_chains
    else:
        # Select the chain closest to the CoM
        min_dist = float('inf')
        selected_chain = None
        for chain in lst_chains:
            dist = chain.calculate_center_of_mass().dist(CoM)
            if dist < min_dist:
                min_dist = dist
                selected_chain = chain
        return [selected_chain]

    # Model level functions

def sele_model( lst_model: list[gemmi.Model], lst_idx = [0],level = False ):
    if level: return "model"
    return [ lst_model[idx] for idx in lst_idx ]


    ### END sele_pdb helper functions ###################

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



def find_inter_aas(prot: gemmi.Structure, lig: gemmi.Structure)-> gemmi.Structure:
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


# Functions to transfer data between different python packages (e.g. RDKit, Gemmi, PyMOL)

def rdkit_to_gemmi( mol:Chem.Mol  ):
    """ Convert an RDKit Mol object to a Gemmi Structure object.
    Args:
    - mol (rdkit.Chem.Mol): The RDKit Mol object to convert.
    Returns:
    - gemmi.Structure: The converted Gemmi Structure object.
    """
    pdb_block = Chem.MolToPDBBlock(mol)
    gemmi_structure = gemmi.read_pdb_string(pdb_block)
    return gemmi_structure

# Sequence Alignment functions


class seqAlign():
    def __init__( self, refseq: str, queryseq: str, sanityCheck: bool = True): 
        self.refseq = refseq
        self.queryseq = queryseq
        self.result = None                                                       # parasail alignment result object
        self.reverseQuery = False
        self.sanityCheck = sanityCheck
        self.matched_indices = None                                              # Dictionary of matched indices and AAs {"Ref":{"Seq_Idx":None, "Seq_AA":None }, "Query":{"Seq_Idx":None, "Seq_AA":None }}
        self.matched_indices_map = None                                          # Dictionary mapping matched indices between ref and query sequences {"Ref_to_Query":{ref_idx:query_idx}, "Query_to_Ref":{query_idx:ref_idx}}
        if sanityCheck:                                                                                                 
            self.find_orientation()
            if self.reverseQuery: 
                print("Warning: Query sequence reversed for better alignment")

    def align( self, mode: str = "global", gap_open: int = 10, gap_extend: int = 1,
              matrix: str = "blosum62"):
        if mode == "global":
            self.result = parasail.nw_trace_striped_32( self.queryseq,
                self.refseq, gap_open, gap_extend, getattr( parasail, matrix) )
        elif mode == "local":
            self.result = parasail.sw_trace_striped_32( self.queryseq, 
                self.refseq, gap_open, gap_extend, getattr( parasail, matrix))
        else:
            raise ValueError("Invalid mode. Choose 'global' or 'local'.")
        
        return self
    
    def find_orientation( self, mode: str = "global", gap_open: int = 10, 
                                gap_extend: int = 1, matrix: str = "blosum62"):
        """
        Find if the best alignment is obtained by reversing the query sequence.
        """
        normalScore = self.align(mode = mode, gap_open = gap_open, 
                    gap_extend = gap_extend,matrix = matrix).result.score
        self.queryseq = self.queryseq[::-1]
        reverseScore = self.align(mode = mode, gap_open = gap_open, 
                    gap_extend = gap_extend,matrix = matrix).result.score
        if reverseScore > normalScore:
            self.reverseQuery = True
        else:
            self.queryseq = self.queryseq[::-1]                                 # Restore original query sequence
            self.align(mode = mode, gap_open = gap_open, 
                    gap_extend = gap_extend,matrix = matrix)
            self.reverseQuery = False                                   
        return self
    
    def map_matching_res( self, match_type = "exact"):
        
        """ 
        Map the matched residues between reference and query sequences based
        on alignment result.
        Args:
        - match_type (str ("exact","all") ): Type of match to consider. 
            Options:
            - "exact":  for exact matches only, or 
            - "all" for matched including conservative and semi-conservative matches.
        Returns:
            self: Updated seqAlign object with matched indices.
        """

        if self.result is None: self.align()                                    # Perform alignment if not done already to obtain traceback / self.result 
        matches = {"Ref":{"Seq_Idx":None, "Seq_AA":None },
                   "Query":{"Seq_Idx":None, "Seq_AA":None }}

        if match_type == "exact":matchpattern = ["|"]                           # Exact matches only
        elif match_type == "all": matchpattern = ["|", ":", "."]                # Include conservative and semi-conservative matches
        else:
            raise ValueError("Invalid match_type. Choose 'exact' or 'all'.")                  

        comp_matchIndex=[idx for idx, char in enumerate(self.result.traceback.comp) # Get indices of matches in comparison string 
                           if char in matchpattern ]
   
        def seq_match_idx( seq: str, matchIdx: list[int]) -> list[int]:         # Helper function to get indices
            gapCount = 0
            seq_indices = []
            for seq_idx, char in enumerate(seq):                                # seq = self.result.traceback.ref or .query
                if char == '-':
                    gapCount += 1
                if seq_idx in matchIdx:
                    seq_indices.append(seq_idx - gapCount)
            return seq_indices
        
        refSeq_matchIdx = seq_match_idx( self.result.traceback.ref,comp_matchIndex)
        matches["Ref"]["Seq_Idx"] = refSeq_matchIdx 

        queryseq_matchIdx = seq_match_idx( self.result.traceback.query,comp_matchIndex)
        matches["Query"]["Seq_Idx"] = queryseq_matchIdx

        refSeq_matchAA = [ self.refseq[idx] for idx in refSeq_matchIdx ]
        matches["Ref"]["Seq_AA"] = refSeq_matchAA 

        queryseq_matchAA = [ self.queryseq[idx] for idx in queryseq_matchIdx ]
        matches["Query"]["Seq_AA"] = queryseq_matchAA 
        
        self.matched_indices = matches
        self.matched_indices_map = dict(                                        # Map ref seq idx to query seq idx based on alignment
                                zip( self.matched_indices["Ref"]["Seq_Idx"],
                                    self.matched_indices["Query"]["Seq_Idx"]) )                   
        return self
    
    def visualize( self):
        if self.result is None: self.align()                                    # Perform alignment if not done already to obtain traceback / self.result
        comp_size = len(self.result.traceback.comp)
        count = list( " "*comp_size )
        for idx in range(comp_size):
            if idx % 100 - 99 == 0 and idx != 0: count[idx] = "+"
            elif idx % 50 - 49 == 0 and idx != 0: count[idx] = "*"
            elif idx % 10 - 9 == 0 and idx != 0: count[idx] = "|"
        count = "".join(count)
        
        print("      ", count)
        print("Ref:  ", self.result.traceback.ref)
        print("      ", self.result.traceback.comp)
        print("Query:", self.result.traceback.query)
        return self

class model_seqAlign( seqAlign):
    def __init__( self, refmodel: gemmi.Structure, querymodel: gemmi.Structure, sanityCheck: bool = True): 
        self.refmodel = refmodel
        self.querymodel = querymodel
        self.refseq = get_chain_seq( refmodel )[0]                              # Get sequence of first chain in REFERENCE model
        self.queryseq = get_chain_seq( querymodel )[0]                          # Get sequence of first chain in QUERY model            
        super().__init__( refseq = self.refseq, queryseq = self.queryseq, 
                                                    sanityCheck = sanityCheck)
        self.ref_res_lst = flatten_pdb( refmodel, "chain")[0].whole()           # List of all residue objects in REFERENCE model
        self.query_res_lst = flatten_pdb( querymodel, "chain")[0].whole()      # List of all residue objects in QUERY model       
        self.matched_indices = None                                             # Dictionary of matched indices and AAs {"Ref":{"Seq_Idx":None, "Seq_AA":None }, "Query":{"Seq_Idx":None, "Seq_AA":None }}
        self.matched_res = { "Ref": None, "Query": None }                       # Dictionary of matched residues {"Ref": [residue objects], "Query": [residue objects]    }
        self.match_status = None                                                # Status of match check (None if not checked, True if all matched, False if mismatch)          

    def map_matching_res(self, match_type = "exact", gaps = False):
        """
        Map matched residues between reference and query models based on sequence alignment.
        Args:
        - match_type (str, optional): Type of match to consider. Defaults to "exact". Options: "all", "exact".
            Options:
            - "exact": Only exact matches of amino acids.
            - "all": Includes partial matches and conserved substitutions.
        - gaps (bool, optional): Whether to include gaps in the mapping. Defaults to False.
        This does not mean add gaps found in the reference but only on the query in
        relation to the reference.
        Returns:
        - self: Updated object with matched residues.
        """
        super().map_matching_res( match_type = match_type)                      # Call parent method to get matched indices (self.matched_indices)
        self.ref_res_lst  = flatten_pdb(self.refmodel, level = "residue")                 # List of all residue objects in REFERENCE model
        self.query_res_lst = flatten_pdb(self.querymodel, level = "residue")             # List of all residue objects in QUERY model


        if gaps:                                               # Some positions in ref seq may not have a matching position in query seq due to gaps in alignment             
            self.matched_res["Ref"] = self.ref_res_lst
            self.matched_res["Query"] = []                                                            
            for ref_aa_pos in range( len(self.refseq)  ):                            # Loop over all positions in ref seq
                if ref_aa_pos in list( self.matched_indices_map.keys() ):               # If ref position has a matching position in current query seq
                    matching_query_aa_id = self.matched_indices_map[ref_aa_pos]                   # Get matching query seq idx
                    res = self.query_res_lst[ matching_query_aa_id ]                    # Get matching residue object in QUERY model
                    self.matched_res["Query"].append(res)                               # Append matched residue object to list
                else: self.matched_res["Query"].append( None )                      # If ref position has NO matching position in current query seq add None to list
                    
        else:
            self.matched_res["Ref"] = [ self.ref_res_lst[idx] for idx in           # List of matched residue objects in REFERENCE model
                                self.matched_indices["Ref"]["Seq_Idx"]]
            self.matched_res["Query"] = [ self.query_res_lst[idx] for idx in       # List of matched residue objects in QUERY model
                                    self.matched_indices["Query"]["Seq_Idx"] ]
        
        return self


    def check_match(self, verbose = True, match_type = "exact", gaps = False):
        """
        Check if the matched residues between reference and query models have 
        the same residue serial numbers.
        Args:
        - verbose (bool, optional): Whether to print mismatch information. 
            Defaults to True.
        - match_type (str, optional): Type of match to consider. Defaults to "exact". Options: "all", "exact".
        - gaps (bool, optional): Whether to include gaps in the mapping. Defaults to False
        Returns:
        - self: Updated object with .match_status.
        """
        if self.matched_indices is None:
            self.map_matching_res(match_type = match_type, gaps = gaps)
        if len( self.matched_indices["Ref"]["Seq_Idx"]) != len(
                                     self.matched_indices["Query"]["Seq_Idx"]):
            raise ValueError("Mismatch in number of matched amino acids " \
                                                "between reference and query.")
        ref_match_res_ids = [ res.seqid.num for res in 
                                                    self.matched_res["Ref"] ]   # List of matched residue serial numbers in REFERENCE model    
        query_match_res_ids = [ res.seqid.num for res in 
                                                    self.matched_res["Query"]]  # List of matched residue serial numbers in QUERY model
        
        if ref_match_res_ids != query_match_res_ids:
            if verbose:
                print( "Mismatch in residue serial numbers between " \
                                                        "reference and query.")
            self.match_status = False
        else:
            if verbose:
                print("Match of all residue serial numbers between " \
                                                       "reference and query.")
            self.match_status = True
        return self
        
def get_aa_distribution( ref_model: gemmi.Structure, 
                         query_models_lst: list[gemmi.Structure],
                         ref_aa_positions: None | list[int] = None,
                         ) -> dict:
    """
    Get the amino acid distribution at each position in the reference sequence
    across a list of query models.
    Args:
    - ref_model (gemmi.Structure): Reference protein structure.
    - query_models_lst (list[gemmi.Structure]): List of query protein structures.
    - ref_aa_positions: choose which amino acids of the ref protein to look at.
    Lowest position = 0, highest postion = len(ref_model) - 1
    Returns:
    - dict: Dictionary with positions as keys and lists of amino acids as values.
    """
    ref_seq = get_chain_seq( ref_model )[0]
    if not ref_aa_positions: ref_aa_positions = list( range(len(ref_seq)))
    aa_distrib_dict = {ref_aa_pos : [] for ref_aa_pos in ref_aa_positions}   # Dictionary to store AA distribution at each position in ref seq       
    for query_model in query_models_lst[:]:
        alignment  = model_seqAlign( ref_model, query_model)
        alignment.map_matching_res(match_type = "exact", gaps = True)
        for ref_idx in aa_distrib_dict.keys():                                       # Loop over each position in ref seq
            aa_distrib_dict[ref_idx].append( alignment.matched_res["Query"][ref_idx])
    return aa_distrib_dict

class structAlign():
    def __init__( self, ref_prot:gemmi.Structure, mobile_prot:gemmi.Structure):
        self.ref_prot : gemmi.Structure = ref_prot
        self.mobile_prot: gemmi.Structure  = mobile_prot
        self.aligned_prot: gemmi.Structure | None  = None
        self.aligned_status: bool = False
        self.transform = None
        self.rmsd = None
        self.rot_matrix = None
        self.trans_vect = None

    def calc_transform(self, ref_atoms: str = "All") :
        if ref_atoms not in ["All", "MainChain", "CaP"]:
            raise ValueError("ref_atoms must be one of 'All', 'MainChain', or 'CaP'.")

        supresult = gemmi.calculate_superposition( 
        flatten_pdb(self.ref_prot, "chain")[0].whole(),
        flatten_pdb(self.mobile_prot, "chain" )[0].whole(),
        flatten_pdb(self.mobile_prot, "chain")[0].whole().check_polymer_type(),
        getattr((gemmi.SupSelect),ref_atoms ), )
        
        self.transform = supresult.transform
        self.rmsd = supresult.rmsd
        self.rot_matrix = supresult.transform.mat # Rotation Matrix
        self.trans_vect = supresult.transform.vec # Translation Vector

        return self

    def apply_transform(self, transform = None):
        self.aligned_prot = self.mobile_prot.clone()
        if transform is not None:
            self.transform = transform
        (flatten_pdb(self.aligned_prot, "chain" )[0].whole()
                                .transform_pos_and_adp(self.transform))
        self.aligned = True
        return self
    
    def calc_rmsd( self, ref_atoms: str = "All") -> float:
        """ 
        Calculate RMSD between ref_prot and mobile_prot without alignment.
        ref_atoms: str
            Atom selection for reference structure alignment. 
            Options: "All", "MainChain", "CaP"
        Returns:
        rmsd: float
            The calculated RMSD value.
        """
        if ref_atoms not in ["All", "MainChain", "CaP"]:
            raise ValueError("ref_atoms must be one of 'All', 'MainChain', or 'CaP'.")

        supresult = gemmi.calculate_current_rmsd( 
        flatten_pdb(self.ref_prot, "chain")[0].whole(),
        flatten_pdb(self.mobile_prot, "chain" )[0].whole(),
        flatten_pdb(self.ref_prot, "chain")[0].whole().check_polymer_type(),
        getattr((gemmi.SupSelect),ref_atoms ), )
        self.rmsd = supresult.rmsd
        return self

    def align( self, ref_atoms: str = "All") :
        """ 
        Align mobile_prot to ref_prot using gemmi superposition calculation 
        Currently, only takes one chain from each structure for alignment.
        Also, aligns all atoms in the chain (can be modified to select specific atoms).
        ref_atoms: str
            Atom selection for reference structure alignment. 
            Options: "All", "MainChain", "CaP" (C alpha)
        Returns:
        self: model_structAlign
            The instance with updated aligned_prot, transform, rmsd, rot_matrix, 
            trans_vect attributes.
        """
        self.calc_transform( ref_atoms = ref_atoms )
        self.apply_transform()
        return self
    
####################
# RDKit Tools
####################
def rdkit_to_gemmi( rdkit_mol_lst: list[Chem.Mol] ):
    """
    Convert RDKit molecule to Gemmi structure.
    Args:
    - rdkit_mol: RDKit molecule object
    return:
    - gemmi_struct: Gemmi structure object
    """
    if ( not isinstance( rdkit_mol_lst, list) and 
         not isinstance( rdkit_mol_lst, Chem.SDMolSupplier) ):
        rdkit_mol_lst = [ rdkit_mol_lst ]
    lst_gemmi_struct = []
    for rdkit_mol in rdkit_mol_lst:
        if rdkit_mol is None:
            continue
        pdb_block = Chem.MolToPDBBlock( rdkit_mol )
        gemmi_struct = gemmi.read_pdb_string( pdb_block )
        lst_gemmi_struct.append( gemmi_struct )
    return lst_gemmi_struct

def view_3d(mol_lst: list[ Chem.Mol ], file_type: str = 'sdf', 
                                        highlight = None) -> None:
    # Create a py3Dmol view object
    view = py3Dmol.view(width=250, height=250)
    for idx, mol in enumerate(mol_lst):
        # Add the molecule data from the file content
        # The second argument specifies the format
        view.addModel(Chem.MolToMolBlock(mol), file_type)
        if highlight:
            view.setStyle({'serial': highlight[idx]}, 
                          {'sphere': {'color': 'blue', 'radius': 1.0}})
    # Set the visualization style
    view.setStyle({'stick': {}})

    view.setStyle({'serial': highlight[0]}, 
                  {'sphere': {'color': 'red', 'radius': 1.0}})
    # Center and zoom the view
    view.zoomTo()
    # Show the interactive viewer
    view.show()

def create_newOrder( ref_at_idx:list, trgt_at_idx: list, 
                    ref_mol:Chem.Mol= None, target_mol: Chem.Mol= None):
    """
    Outputs a list of new indexes for a target molecule so that its atoms
    are ordered in the same way as a reference molecule based on a common
    substructure match.
    Args:
    - ref_at_idx: list of atom indexes in the reference molecule
    - trgt_at_idx: list of matching atom indexes in the target molecule
    return: 
    - list of new atom indexes for the target molecule
    """
    if ref_mol.GetNumAtoms() > target_mol.GetNumAtoms():
        raise ValueError("Reference atom index list is longer " \
        "than target atom index list.\nIt must be smaller or equal." \
        "This ensures that reindexing does not create gaps.") 
    map_dict = dict( zip(ref_at_idx, trgt_at_idx))
    new_order = [ map_dict[i] for i in sorted(list(ref_at_idx)) ]
    missing_idx = [ i for i in list( range(target_mol.GetNumAtoms()))           # Get missing indices in of the target molecule (bc it is larger)
                                            if i not in trgt_at_idx ]
    new_order.extend( missing_idx )                                             # Add missing indices at the end of the new order
    return new_order

def reindex_mol_fromCMS( ref_mol: Chem.Mol, trgt_mol: Chem.Mol):
    """
    Reindex atoms in the target molecule based on the common substructure
    match with the reference molecule.
    Args:
    - ref_mol: reference RDKit molecule
    - trgt_mol: target RDKit molecule to be reindexed
    return:
    - new_trgt_mol: reindexed target RDKit molecule
    """
    mcs_result = rdFMCS.FindMCS( [ref_mol, trgt_mol])
    mcs_mol = Chem.MolFromSmarts(mcs_result.smartsString)                       # Create mol object of matching atoms only from SMARTS string
    ref_match = ref_mol.GetSubstructMatch(mcs_mol)                              # Get indices of matching atoms in reference and target molecules    
    trgt_match = trgt_mol.GetSubstructMatch(mcs_mol)
    new_order = create_newOrder( ref_match, trgt_match,                         # Get new order of target molecule atoms to match related refence molecule atoms
                                ref_mol= ref_mol, target_mol = trgt_mol)
    new_trgt_mol = Chem.RenumberAtoms( trgt_mol,  new_order )
    return new_trgt_mol

def align_mols( ref_mol, trgt_mol):
    """
    Align target molecule coordinates to reference molecule in 3D space based
    on common substructure match.
    Args:
    - ref_mol: reference RDKit molecule
    - trgt_mol: target RDKit molecule to be aligned
    return:
    - aligned_trgt_mol: aligned target RDKit molecule
    """
    mcs_result = rdFMCS.FindMCS( [ref_mol, trgt_mol])
    mcs_mol = Chem.MolFromSmarts(mcs_result.smartsString)
    ref_match = ref_mol.GetSubstructMatch(mcs_mol)
    trgt_match = trgt_mol.GetSubstructMatch(mcs_mol)
    AllChem.AlignMol(trgt_mol,ref_mol,atomMap=list(zip(trgt_match, ref_match)))
    return trgt_mol

####################
# Biopython Tools
####################

def gemmi_to_biopy( gemmi_struct: gemmi.Structure, file_type: str = "mmcif"):
    """
    Convert a Gemmi Structure object to a Biopython Structure object.
    Args:
    - gemmi_struct (gemmi.Structure): The Gemmi Structure object to convert.
    - file_type (str): The file format to use for conversion ("pdb" or "mmcif").
    Returns:
    - Bio.PDB.Structure.Structure: The converted Biopython Structure object.
    """
    if file_type == "pdb":
        prot_block = gemmi_struct.make_pdb_string()
        parser = PDBParser(QUIET=True)                                          # Create a PDBParser    
    elif file_type == "mmcif" :
        prot_block =  gemmi_struct.make_mmcif_block().as_string()
        parser = MMCIFParser(QUIET=True)                                        # Create an MMCIFParser
    
    biopython_struct = parser.get_structure(gemmi_struct.name,                  # gemmi_struct.name = ID you assign to the Biopython structure
                                            StringIO(prot_block))               # Use StringIO to treat the string as a file
    return biopython_struct

def biopy_to_gemmi( biopython_struct: 'Bio.PDB.Structure.Structure', 
                       file_type : str = "mmcif" ) -> gemmi.Structure:
    """
    Convert a Biopython Structure object to a Gemmi Structure object.
    Args:
    - biopython_struct (Bio.PDB.Structure.Structure): The Biopython Structure object to convert.
    - file_type (str): The file format to use for conversion ("pdb" or "mmcif").
    Returns:
    - gemmi.Structure: The converted Gemmi Structure object.
    """
                                                                                # Write Biopython structure to a PDB string
    if file_type == "pdb":
        file_io = PDBIO()
    elif file_type == "mmcif":
        file_io = MMCIFIO()
    else:
        raise ValueError("Unsupported file type. Use 'pdb' or 'mmcif'.")
    string_io = StringIO()
    file_io.set_structure(biopython_struct)
    file_io.save(string_io)
    file_string = string_io.getvalue()                                              # Get the string value from the buffer
                                                                                # Read the PDB/MMCIF string into a Gemmi Structure
    if file_type == "pdb": gemmi_struct = gemmi.read_pdb_string(file_string)
    elif file_type == "mmcif": 
        gemmi_doc = gemmi.cif.read_string(file_string)                           # First, parse the string into a gemmi.cif.Document
        gemmi_struct = gemmi.make_structure_from_block(gemmi_doc.sole_block())   # Then, create a Gemmi Structure from the sole block
    return gemmi_struct

####################
# MDAnalysis Tools
####################

def gemmi_to_mda( gemmi_struct: gemmi.Structure, file_type: str = "mmcif"):
    """
    Convert a Gemmi Structure object to an MDAnalysis Universe object.
    Args:
    - gemmi_struct (gemmi.Structure): The Gemmi Structure object to convert.
    - file_type (str): The file format to use for conversion ("pdb" or "mmcif").
    Returns:
    - MDAnalysis.Universe: The converted MDAnalysis Universe object.
    """
    if file_type == "pdb":
        prot_block = gemmi_struct.make_pdb_string()
    elif file_type == "mmcif" :
        prot_block =  gemmi_struct.make_mmcif_block().as_string()
    else:
        raise ValueError("Unsupported file type. Use 'pdb' or 'mmcif'.")
    
    universe = mda.Universe(StringIO(prot_block), format=file_type)              # Create an MDAnalysis Universe from the string using StringIO
    return universe 