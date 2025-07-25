import argparse, os
from pathlib import Path

"""
    Checks the arguments passed and performs error checking:
        Correct arguments passed (an argument was parsed and the correct flag(s) were used)
        Checks the provided directory is valid and reachable
        Checks the provided directy has read and write permissions for the user running the program
    
    Behaviour on failed check:
        Program will error out with an appropriate exception and description - without a valid directory or permissions we cannot recover
        
    Returns:
        A valid directory provided in args
    
    If we were being pedantic we may move the error checking to a separate "checkDirectory" function.
"""


def parseArguments():

    # Setup Argument Parsing for our destination filepath
    parser = argparse.ArgumentParser()
    parser.add_argument("-path")

    # Input sanitation??????
    args = parser.parse_args()

    directoryPath = args.path

    # Check that Arguments were actually passed
    if directoryPath is None:
        raise ValueError("Bad Arguments passed please use: -path pathName")

    # Error handling for provided directory
    try:
        if os.path.isdir(directoryPath):
            print("Directory at: " + directoryPath + " found")
        else:
            raise FileNotFoundError(
                'Directory at: "' + directoryPath + '" cannot be found'
            )
    # Exceptions for os.path.isdir()
    except PermissionError:
        raise PermissionError(
            "os.path.isdir() failed: pleasure ensure permissions to execute os.stat() are granted on the supplied directory.\nPlease see:https://docs.python.org/dev/library/os.path.html#os.path.isdir for help"
        )

    # Permissions exceptions - shouldn't need execute permissions?
    # May require execute in the future for checking destination directory is the same as source
    if not (os.access(directoryPath, os.R_OK)):
        raise PermissionError(
            'No read permissions for directory at: "' + directoryPath + '"  '
        )

    if not (os.access(directoryPath, os.W_OK)):
        raise PermissionError(
            'No write permissions for directory at: "' + directoryPath + '"  '
        )

    return directoryPath


"""
   Input: a Path in string format
   
   Returns: Path Object
   
   Returns the Path from target onwards - not including
   
   Example: 
   
   C:\\Users\\Username\\Documents\\Projects\\DropBox\\source_test\\yerty\\New Text Document.txt
   -->
   yerty\\New Text Document.txt
"""


def stripPath(pathStr, target):
    path = Path(pathStr)
    parts = path.parts

    index = parts.index(target)

    return Path(*parts[index + 1 :])
