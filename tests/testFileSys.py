# This contains a series of file paths that describe a known file system with known metrics such as gamma and folderIDs for each file.
# This can be used to test the manipulation of a file system based off of a list of paths.

# testDir1, testTree, testFileTree, testFolderTree, testLabels, testLabelsDic
# Includes paths of directories as well 
testDir1 = ["root/file11.txt", "root/subDir11/file21.txt","root/subDir11/subDir21",
            "root/subDir11/subDir22", "root/subDir11/subDir23",
            "root/subDir11/subDir21/file31.txt", "root/subDir11/subDir21/file32.txt",
            "root/subDir11/subDir21/file33.txt","root/subDir11/subDir22/file34.txt",
            "root/subDir11/subDir22/subDir31", "root/subDir11/subDir22/subDir31/file41.txt",
            "root/subDir11/subDir22/subDir31/file42.txt", "root/subDir11/subDir22/subDir31/file43.txt",
            "root/subDir11/subDir23/file35.txt","root/subDir11/subDir23/subDir32",
            "root/subDir11/subDir23/subDir32/file44.txt", "root/subDir11/subDir23/subDir32/file45.txt",
            "root/subDir11/subDir23/subDir32/subDir41", "root/subDir11/subDir23/subDir32/subDir41/file51.txt",
            "root/subDir12", "root/subDir12/file22.txt", "root/subDir12/subDir24",
            "root/subDir12/subDir24/file36.txt", "root/subDir12/subDir24/file37.txt",
            "root/subDir12/subDir25", "root/subDir12/subDir25/file38.txt",
            "root/subDir12/subDir25/subDir33", "root/subDir12/subDir25/subDir33/file46.txt",
            "root/subDir12/subDir25/subDir33/file47.txt",
            ]

# Order: first files then folders
testTree = ["root/file11.txt", 
            "root/subDir11/file21.txt",
            "root/subDir11/subDir21/file31.txt", "root/subDir11/subDir21/file32.txt","root/subDir11/subDir21/file33.txt",
            
            "root/subDir11/subDir22/file34.txt",
            "root/subDir11/subDir22/subDir31/file41.txt", "root/subDir11/subDir22/subDir31/file42.txt", "root/subDir11/subDir22/subDir31/file43.txt",
            
            "root/subDir11/subDir23/file35.txt",
            "root/subDir11/subDir23/subDir32/file44.txt", "root/subDir11/subDir23/subDir32/file45.txt",
            "root/subDir11/subDir23/subDir32/subDir41/file51.txt",
            
            "root/subDir12/file22.txt",
            "root/subDir12/subDir24/file36.txt", "root/subDir12/subDir24/file37.txt",
            
            "root/subDir12/subDir25/file38.txt",
            "root/subDir12/subDir25/subDir33/file46.txt",
            "root/subDir12/subDir25/subDir33/file47.txt",
            ]



# Order: First folders then files
testFileTree = [           
            "root/subDir11/subDir21/file31.txt", "root/subDir11/subDir21/file32.txt","root/subDir11/subDir21/file33.txt",    

            "root/subDir11/subDir22/subDir31/file41.txt", "root/subDir11/subDir22/subDir31/file42.txt", "root/subDir11/subDir22/subDir31/file43.txt",
            "root/subDir11/subDir22/file34.txt",

            "root/subDir11/subDir23/subDir32/subDir41/file51.txt",
            "root/subDir11/subDir23/subDir32/file44.txt", "root/subDir11/subDir23/subDir32/file45.txt",
            "root/subDir11/subDir23/file35.txt",

            "root/subDir11/file21.txt",


            "root/subDir12/subDir24/file36.txt", "root/subDir12/subDir24/file37.txt",
            

            "root/subDir12/subDir25/subDir33/file46.txt",
            "root/subDir12/subDir25/subDir33/file47.txt",
            "root/subDir12/subDir25/file38.txt",

            "root/subDir12/file22.txt",

            "root/file11.txt", 
            ]

# Only Contains directories
testFolderTree = ["root", 
            "root/subDir11",
            "root/subDir11/subDir21",
            
            "root/subDir11/subDir22",
            "root/subDir11/subDir22/subDir31",
            
            "root/subDir11/subDir23",
            "root/subDir11/subDir23/subDir32",
            "root/subDir11/subDir23/subDir32/subDir41",
            
            "root/subDir12",
            "root/subDir12/subDir24",
            
            "root/subDir12/subDir25",
            "root/subDir12/subDir25/subDir33",
            ]



testLabels = [ ["fileID", "Gamma"], # Gamma is only based on folders
            # Subdir11
                # Subdir21 
                [ [0, 0, 0], [ 0 ] ], [ [ 0, 0, 1 ], [0] ],  [ [0, 0, 2], [0] ], 
                # subDir22 
                [ [0, 1, 0, 0], [0] ], [ [0, 1, 0, 1], [0] ], [ [0, 1, 0, 2], [0] ],
                [ [0, 1, 1], [1]], 
                # subDir23
                [ [0, 2, 0, 0, 0], [0] ],
                [ [0, 2, 0, 1], [1] ], [ [0, 2, 0, 2], [1] ],  
                [ [0, 2, 1], [2] ],
            [ [0, 3], [0] ],

            #subDir12
                #subDir24
                [ [1,0,0], [3]], [ [1,0,1], [3]],
                #subDir25
                [ [1,1,0,0], [2] ], [ [ 1, 1, 0, 1], [2] ],                 
                [ [1,1,1], [4] ],
            [ [1, 2], [1]],

            [ [2], [] ],              

               ]

testLabelsDic = { key: value for key, value in zip( ["path"]+ testFileTree, testLabels )}

# List that represents an unordered list of file paths, to be ordered alphabetically
test_sortLst = ["A/A/A/A/.file", "A/A/A/B/.file", "A/A/A/C/.file", "A/A/A/D/.file",
                 "A/A/B/.file",
                 "A/A/C/A/.file", "A/A/C/B/.file", "A/A/C/C/.file",
                 
                 "A/B/A/A/.file","A/B/A/B/.file","A/B/A/C/.file",
                 "A/B/B/A/.file", "A/B/B/B/.file",
                  "A/B/C/.file", 
                  
                  "A/C/.file",
                  
                  "B/C/D/.file", "B/C/C/.file", "B/C/B/.file", "B/C/A/.file",
                  "B/A/A/A/.file", "B/A/A/C/.file", "B/A/B/.file", "B/A/A/B/.file",
                   "B/B B/.file", ]