
import sys
from pathlib import Path
sys.path.insert(0, Path("../..").resolve().absolute().__str__())

# # Add max min and sum of file sizes for each file type
# import numpy as np

# from xaidar.filesUtils import loadPickle

# cacheDir = Path("../../data/s3Sizes/xchem/filetypes")
# mergedSizes = loadPickle( cacheDir / "merged_filetype_sizes.pkl" )


# data = { "Max": [], "Min": [], "Sum": [] }

# for fileType, sizes in mergedSizes.items():
#     # print(f"Processing file type: {fileType} with {len(sizes)} sizes")
#     if len(sizes) > 0:
#         data["Max"].append(np.max(sizes))
#         data["Min"].append(np.min(sizes))
#         data["Sum"].append(np.sum(sizes))


# from xaidar.filesUtils import savePyObj
# savePath = cacheDir / "stats_filetype_sizes_pt2.pkl"
# print(f"Saving statistics to {savePath}")
# savePyObj(data, savePath)
# print(f"Saved statistics to {savePath}")

# # Trim the large file into smaller ordered chunks

from time import time

from xaidar.filesUtils import loadPickle
start = time()
dataPath = Path( "../../data/s3Sizes/xchem/filetypes/merged_filetype_sizes.pkl" ) 
data = loadPickle( dataPath )
print(f"Loaded data from {dataPath}, number of file types: {len(data)}")#
print(f"Time taken to load data: {time() - start:.2f} seconds")