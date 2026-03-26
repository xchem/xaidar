from pathlib import Path, WindowsPath
from time import time

def calc_order_parameter(start_time):
    from pathlib import Path
    root_dir = WindowsPath(".")          # !!!!! Make sure this is correctly set to the root directory of the project !!!!!!
    import re
    import numpy as np
    import sys
    import subprocess
    import re
    sys.path.insert(0, root_dir.__str__())

    qfit_dir = root_dir.joinpath("qfit-3.0")
    data_dir = root_dir.joinpath("data/entropy/wankowicz")
    orderParam_dir = data_dir.joinpath("orderParam_analysis")
    log_file_path = WindowsPath(r"D:\powershellScripts\log.txt")

    def extract_resolution(pdb_file, verbose=False):
        with open( pdb_file, "r") as file:
            lines = file.readlines()
            resolution = [ line for line in lines if "RESOLUTION RANGE HIGH (ANGSTROMS) :" in line ][0]
            resolution = re.findall(r"[-+]?\d*\.\d*", resolution)[0]
            if verbose: print(resolution)
            return resolution


    # Calculate per residue B-factor from PDB file
    from shutil import move
    for pdb_dir in list( orderParam_dir.iterdir() )[:]:
        pdb_name = pdb_dir.name
        pdb_file = pdb_dir.joinpath( f"{pdb_name}_final_qFit.pdb")
        calc_bfactor = fr"python {qfit_dir.joinpath(r"scripts\post\b_factor.py").__str__()} {pdb_file} --pdb {pdb_name} --ca"
        try: subprocess.run(f"{calc_bfactor}", shell=True)
        except Exception as e:
            with open(log_file_path, "a") as file:
                file.write("\nError Addressing Order Parameter Calculation: " + str(e))

        move( f"{pdb_name}_B_factors.csv", pdb_dir.joinpath(f"{pdb_name}_B_factors.csv") )


    # Calculate intermediate .dat file for order parameter calculation
        get_dat_file = fr"python {qfit_dir.joinpath(r"scripts\post\make_methyl_df.py")} {pdb_file} --pdb {pdb_name} " 
        try: subprocess.run(f"{get_dat_file}", shell=True)
        except Exception as e:
            with open(log_file_path, "a") as file:
                file.write("\nError Addressing Order Parameter Calculation: " + str(e))

        move( f"{pdb_name}.dat", pdb_dir.joinpath(f"{pdb_name}.dat") )


    # Calculate order parameters
        pdb_dat = pdb_dir.joinpath(fr"{pdb_name + ".dat"}") 
        output_file = pdb_dir.joinpath(fr"{pdb_name}_qfit_order_par.out")
        resolution = extract_resolution(pdb_file)
        avg_bfactor = np.loadtxt(pdb_dir.joinpath(fr"{pdb_name}_B_factors.csv"), 
                                delimiter=",", skiprows=1 , dtype=float, 
                                usecols=-2).mean().round(2)
        calc_op = f"python {qfit_dir.joinpath(r"scripts\post\calc_OP.py")} "\
                    f"{pdb_dat} {pdb_file} {output_file} "\
                    f"-r {resolution} -b {avg_bfactor}"
        try: subprocess.run(f"{calc_op}", shell=True)
        except Exception as e:
            with open(log_file_path, "a") as file:
                file.write("\nError Addressing Order Parameter Calculation: " + str(e))


    # Log time taken for order parameter calculation
        current_time = time() - start_time
        with open(log_file_path, "a") as file:
            file.write(f"\nFinished running {pdb_name} in {(current_time/60):.4f} minutes")

        pass

def main():
    start_time = time()
    log_file_path = WindowsPath(r"D:\powershellScripts\log.txt")
    print("Hello from xaida!")
    with open(log_file_path, "w") as file:
        file.write("Still running")
    try:
        calc_order_parameter(start_time)
    except Exception as e:
        with open(log_file_path, "a") as file:
            file.write("\nError Addressing Order Parameter Calculation: " + str(e))

    with open(log_file_path, "a") as file:
        file.write("\nFinished running")


if __name__ == "__main__":
    main()
