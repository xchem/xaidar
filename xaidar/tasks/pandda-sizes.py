from pathlib import Path
import sys
sys.path.insert(0, str( Path( "../../" ).resolve().absolute().__str__() ) )

from collections import defaultdict
import re
import time
import numpy as np

from xaidar.filesUtils import loadPickle, savePyObj

# # Step 1: Process file types and their sizes from the S3 data

# fileTypeSizes = defaultdict( list )
# # fileSizes = 
# sizesDir = Path( "../../data/s3Sizes/pandda" ) # /xchem
# start = time.time()
# print( f"Processing file types in {sizesDir}" )
# for fragPath in sizesDir.iterdir():
#     step = time.time()
#     fragName = fragPath.name
#     frag = loadPickle( fragPath )
#     print( f"    Loaded {fragPath.name} with {len(frag)} entries" )
#     for key, size in frag.items():
#         if re.search( "\\.\\w*$", key ): 
#             filetype = re.search( "\\.\\w*$", key.split("/")[-1]).group()
#             fileTypeSizes[filetype].append( size )

#         # break  # Remove this line to process all files
#     savePath = sizesDir / "filetypes" / f"{fragName[:-10]}_filetype_sizes.pkl" 
#     savePath.parent.mkdir( parents=True, exist_ok=True )
#     print( f"\tSaving file type sizes to {savePath}" )
#     savePyObj( fileTypeSizes, savePath )
#     print( f"\tSaved {fragName[:-10]}_filetype_sizes.pkl" )
#     print( f"\tTime: {round(time.time() - step, 0)} seconds" )
#     # break  # Remove this line to process all fragments
# print( f"Done processing file types in {round( time.time() - start, 0)} seconds " )

# # Step 2: Merge all file type sizes into one dictionary

# cacheDir = Path( "../../data/s3Sizes/pandda/filetypes" )  # Adjust path as needed
# fileNames = [ file.name for file in cacheDir.iterdir() if file.suffix == ".pkl" ]

# print(f"Found {len(fileNames)} files to merge.")

# from collections import defaultdict

# # Save it all into one Dictionary
# mergedSizes = defaultdict(list)
# for fileName in fileNames:
#     print(f"Processing {fileName}")
#     fileSizes = loadPickle( cacheDir / fileName )
#     for key, size in fileSizes.items():
#         mergedSizes[key].extend(size)

# # Save the merged sizes to a file

# savePath = cacheDir / "merged_filetype_sizes.pkl"
# print(f"Saving merged sizes to {savePath}")
# savePyObj( mergedSizes, savePath )
# print(f"Saved merged sizes to {savePath}")

# Step 3: Get statistics of the merged file type sizes

# Load Data

cacheDir = Path("../../data/s3Sizes/pandda/filetypes")
mergedSizes = loadPickle( cacheDir / "merged_filetype_sizes.pkl" )


data = { "File Type": [], "Files Count": [], "Median": [], "Mean": [], "Std": [], 
        "1stQrt": [], "3rdQrt": [], "QrtDeviation": [] , "Max": [], "Min": [], "Sum": [] }

for fileType, sizes in mergedSizes.items():
    # print(f"Processing file type: {fileType} with {len(sizes)} sizes")
    if len(sizes) > 0:
        data["File Type"].append(fileType)
        data["Files Count"].append(len(sizes))
        data["Median"].append(np.median(sizes))
        data["Mean"].append(np.mean(sizes))
        data["Std"].append(np.std(sizes))
        data["1stQrt"].append(np.percentile(sizes, 25))
        data["3rdQrt"].append(np.percentile(sizes, 75))
        data["QrtDeviation"].append((np.percentile(sizes, 75) - np.percentile(sizes, 25)) / 2)
        data["Max"].append(np.max(sizes))
        data["Min"].append(np.min(sizes))
        data["Sum"].append(np.sum(sizes))

print("Data collected for file types:")
print(f"Number of file types: {len(data['File Type'])}")


# Save the data to a pickle file

from xaidar.filesUtils import savePyObj
savePath = cacheDir / "stats_filetype_sizes.pkl"
print(f"Saving statistics to {savePath}")
savePyObj(data, savePath)
print(f"Saved statistics to {savePath}")