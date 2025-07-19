from fastapi import FastAPI
import uvicorn,argparse, os 

# Globals - Probably nicer to use some object or singleton in a larger codebase
app: FastAPI = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


# On Event is Deprecated - use Lifespan Event Handlers instead :
# https://fastapi.tiangolo.com/advanced/events/
# @app.on_event("startup")
# async def startup_event():
#     print("App Started")


def parseArguments():
     # Setup Argument Parsing for our destination filepath  
    parser = argparse.ArgumentParser()
    parser.add_argument('-path')
    
    # Input sanitation??????
    args = parser.parse_args()
    directoryPath = args.path
    
    # Error handling for provided directory
    try:
        if os.path.isdir(directoryPath):
            print("Directory at: " + directoryPath + " found")
        else:
            raise FileNotFoundError("Directory at: \"" + directoryPath + "\" cannot be found")
    # Exceptions for os.path.exists() 
    except PermissionError:
        raise PermissionError("os.path.isdir() failed: pleasure ensure permissions to execute os.stat() are granted on the supplied directory.\nPlease see:https://docs.python.org/dev/library/os.path.html#os.path.isdir for help")
        
    # Permissions exceptions - shouldn't need execute permissions? 
    # May require execute in the future for checking destination directory is the same as source
    if not(os.access(directoryPath, os.R_OK)):
        raise PermissionError("No read permissions for directory at: \"" + directoryPath + "\"  ")
        
    if not(os.access(directoryPath, os.W_OK)):
        raise PermissionError("No write permissions for directory at: \"" + directoryPath + "\"  ")
    
    return

if __name__ == "__main__":
    # Parse arguments and perform some permissions / error checks
    parseArguments()
    
    # Start the application
    uvicorn.run(app)
    
