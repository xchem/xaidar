from pathlib import Path
from typing import Callable
from copy import deepcopy

import gemmi
import parasail

from rdkit import Chem
from rdkit.Chem import rdFMCS, AllChem
import py3Dmol

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




### Selection functions

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

    # sele_pdb helper functions

def sele_Lig( lst_res: list[gemmi.Residue], level = False):
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
        
        # Chains level functions
def sele_closest_Chain( lst_chains: list[gemmi.Chain], 
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


    ### END sele_pdb helper functions

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
        self.result = None
        self.reverseQuery = False
        self.sanityCheck = sanityCheck
        self.matched_indices = None
        if sanityCheck:
            self.find_orientation()
            if self.reverseQuery: print("Warning: Query sequence reversed for better alignment")

    def align( self, mode: str = "global", gap_open: int = 10, gap_extend: int = 1,
              matrix: str = "blosum62"):
        if mode == "global":
            self.result = parasail.nw_trace_striped_32( self.queryseq, self.refseq, gap_open, gap_extend,
                                      getattr( parasail, matrix) )
        elif mode == "local":
            self.result = parasail.sw_trace_striped_32( self.queryseq, self.refseq, gap_open, gap_extend,
                                      getattr( parasail, matrix))
        else:
            raise ValueError("Invalid mode. Choose 'global' or 'local'.")
        
        return self
    
    def find_orientation( self, mode: str = "global", gap_open: int = 10, gap_extend: int = 1,
              matrix: str = "blosum62"):
        """
        Find if the best score is obtained with the query sequence reversed
        """
        normalScore = self.align(mode = mode, gap_open = gap_open, 
                    gap_extend = gap_extend,matrix = matrix).result.score
        self.queryseq = self.queryseq[::-1]
        reverseScore = self.align(mode = mode, gap_open = gap_open, 
                    gap_extend = gap_extend,matrix = matrix).result.score
        if reverseScore > normalScore:
            self.reverseQuery = True
        else:
            self.queryseq = self.queryseq[::-1]
            self.align(mode = mode, gap_open = gap_open, 
                    gap_extend = gap_extend,matrix = matrix)
            self.reverseQuery = False
            # self.queryseq = self.queryseq[::-1]                                       # Restore original query

    def match_indices( self):
        if self.result is None:
            raise ValueError("Alignment not performed yet. Call align() first.")
        matches = {"Ref":{"Seq_Idx":None, "Seq_AA":None },
                   "Query":{"Seq_Idx":None, "Seq_AA":None }}
        comp_matchIndex = [ idx for idx, char in                                # Get indices of matches in comparison string
                           enumerate(self.result.traceback.comp) if char == '|']
        
        def seq_match_idx( seq: str, matchIdx: list[int]) -> list[int]:         # Helper function to get indices
            gapCount = 0
            seq_indices = []
            for seq_idx, char in enumerate(seq):
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

        return self

    def visualize( self):
        if self.result is None:
            raise ValueError("Alignment not performed yet. Call align() first.")
        print("Ref:  ", self.result.traceback.ref)
        print("      ", self.result.traceback.comp)
        print("Query:", self.result.traceback.query)
        

####################
# RDKit Tools
##################

def view_3d(mol_lst: list[ Chem.Mol ], file_type: str = 'sdf', highlight = None) -> None:
    # Create a py3Dmol view object
    view = py3Dmol.view(width=250, height=250)
    for idx, mol in enumerate(mol_lst):
        # Add the molecule data from the file content
        # The second argument specifies the format
        view.addModel(Chem.MolToMolBlock(mol), file_type)
        if highlight:
            view.setStyle({'serial': highlight[idx]}, {'sphere': {'color': 'blue', 'radius': 1.0}})
    # Set the visualization style
    view.setStyle({'stick': {}})

    view.setStyle({'serial': highlight[0]}, {'sphere': {'color': 'red', 'radius': 1.0}})
    # Center and zoom the view
    view.zoomTo()
    # Show the interactive viewer
    view.show()

def create_newOrder( ref_at_idx:list, trgt_at_idx: list):
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
    map_dict = dict( zip(ref_at_idx, trgt_at_idx))
    new_order = [ map_dict[i] for i in sorted(list(ref_at_idx)) ]
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
    mcs_mol = Chem.MolFromSmarts(mcs_result.smartsString)
    ref_match = ref_mol.GetSubstructMatch(mcs_mol)
    trgt_match = trgt_mol.GetSubstructMatch(mcs_mol)
    new_order = create_newOrder( ref_match, trgt_match)
    new_trgt_mol = Chem.RenumberAtoms( trgt_mol,  new_order )
    return new_trgt_mol

def align_mols( ref_mol, trgt_mol):
    mcs_result = rdFMCS.FindMCS( [ref_mol, trgt_mol])
    mcs_mol = Chem.MolFromSmarts(mcs_result.smartsString)
    ref_match = ref_mol.GetSubstructMatch(mcs_mol)
    trgt_match = trgt_mol.GetSubstructMatch(mcs_mol)
    AllChem.AlignMol(trgt_mol, ref_mol, atomMap= list(zip(trgt_match, ref_match)) )
    return trgt_mol