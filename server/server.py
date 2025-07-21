from fastapi import FastAPI, UploadFile, File
import uvicorn,argparse, os 
from pydantic import BaseModel



# Globals - Probably nicer to use some object or singleton in a larger codebase
app: FastAPI = FastAPI()
destination: str

@app.get("/")
async def root():
    return {"message": "Hello World"}


# FastAPI's `UploadFile` is very very useful as shown: https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile
# For our case it uses a "spooled" file - this will store the file in memory up to a size limit, when this limit is passed it will be stored in disk.
# This means we can upload large files without being concered about running out of memory.
# we can use `shutil.copyfileobj` to write the file - this is better than using the default `.write` as it will copy in chunks, allowing the copying of files larger than available memory.
# It also saves us from needing to do the chunking manually
# https://stackoverflow.com/questions/63580229/how-to-save-uploadfile-in-fastapi
# Further reading on `shutil`: https://stackoverflow.com/questions/67732361/python-read-write-vs-shutil-copy/73365632#73365632
# If `shutil` proves to be difficult to work with I can do manual chunking as shown here:
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile, destination: str):
    return {"filename": file.filename}


# On Event is Deprecated - use Lifespan Event Handlers instead :
# https://fastapi.tiangolo.com/advanced/events/
# @app.on_event("startup")
# async def startup_event():
#     print("App Started")

"""
    Checks the arguments passed and performs error checking:
        Correct arguments passed (an argument was parsed and the correct flag(s) were used)
        Checks the provided directory is valid and reachable
        Checks the provided directy has read and write permissions for the user running the program
    
    Behaviour on failed check:
        Program will error out with an appropriate exception and description - without a valid directory or permissions we cannot recover
    
    If we were being pedantic we may move the error checking to a separate "checkDirectory" function.
"""
def parseArguments():

    # Setup Argument Parsing for our destination filepath  
    parser = argparse.ArgumentParser()
    parser.add_argument('-path')
    
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
            raise FileNotFoundError("Directory at: \"" + directoryPath + "\" cannot be found")
    # Exceptions for os.path.isdir() 
    except PermissionError:
        raise PermissionError("os.path.isdir() failed: pleasure ensure permissions to execute os.stat() are granted on the supplied directory.\nPlease see:https://docs.python.org/dev/library/os.path.html#os.path.isdir for help")
        
    # Permissions exceptions - shouldn't need execute permissions? 
    # May require execute in the future for checking destination directory is the same as source
    if not(os.access(directoryPath, os.R_OK)):
        raise PermissionError("No read permissions for directory at: \"" + directoryPath + "\"  ")
        
    if not(os.access(directoryPath, os.W_OK)):
        raise PermissionError("No write permissions for directory at: \"" + directoryPath + "\"  ")
    
    # Kinda jank to do this here but idk man
    destination = directoryPath
    
    return

if __name__ == "__main__":
    # Parse arguments and perform some permissions / error checks
    parseArguments()
    
    # Start the application
    uvicorn.run(app)
    
