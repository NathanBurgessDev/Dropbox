import uvicorn, os, shutil
from fastapi import FastAPI, UploadFile, File, Form, Depends, Query, HTTPException
from pathlib import Path
from dependencies.util import parseArguments

# Globals - don't like this but FastAPI has forced my hand
app: FastAPI = FastAPI()

'''
Function to be overriden for dependency injection
Useful for future testing and preventing global variables
This will be used to provide the `fullDestination` variable to the FastAPI endpoints
'''
def getDestination():
    return

'''
    Saves the uploaded file to the specified subPath within the fullDestination directory.
    Handles directory creation if it does not exist.
    Input:
        uploadFile: The file to be saved.
        subPath: The path of the file or directory to be uploaded to relative to the monitored directory.
        fullDestination: The full server path.

'''
# Potentially rework for async - not particularly familar with FastAPI in this format
def saveFile(uploadFile: UploadFile, subPath: str, fullDestination: str):
    destinationPath = Path(fullDestination) / subPath

    # Check if the parent directory exists - if not then create it
    try:
        destinationPath.parent.mkdir(parents=True, exist_ok=True)

        with destinationPath.open("wb") as buffer:
            shutil.copyfileobj(uploadFile.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    return


'''
    Deletes a file or directory at the specified subPath within the fullDestination directory.
    Handles both file and directory deletion.
    Input:
        subPath: The path of the file or directory to be deleted relative to the monitored directory.
        fullDestination: The full server path.
'''
# Windows Directory Rename API: 
# As Windows does not differentiate between a file and a directory being deleted
# We need to handle file and directory deletion in the same function
def deleteFileOrDirectory(subPath: str, fullDestination: str):
    destinationPath = Path(fullDestination) / subPath

    if not destinationPath.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {subPath}")
    
    try:
        if destinationPath.is_file():
            destinationPath.unlink()
        elif destinationPath.is_dir():
            shutil.rmtree(destinationPath)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type at: {subPath}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete '{subPath}': {e}")
    return



'''
    FastAPI endpoints for file operations.
    These endpoints handle file uploads, deletions, renaming, and directory creation.
    Each endpoint uses the `getDestination` dependency to get the full server path.
    We override the `getDestination` function in the main block to inject the destination path.

    FastAPI creates documentation for these endpoints automatically, which can be accessed at `/docs`.
    To reduce redundancy I will avoid repeating docstrings for each endpoint and instead focus on noting any unique aspects or odd behaviors.
'''
# FastAPI's `UploadFile` is very very useful as shown: https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile
# For our case it uses a "spooled" file - this will store the file in memory up to a size limit, when this limit is passed it will be stored in disk.
# This means we can upload large files without being concerned about running out of memory.
# we can use `shutil.copyfileobj` to write the file - this is better than using the default `.write` as it will copy in chunks, allowing the copying of files larger than available memory.
# It also saves us from needing to do the chunking manually
# https://stackoverflow.com/questions/63580229/how-to-save-uploadfile-in-fastapi
# Further reading on `shutil`: https://stackoverflow.com/questions/67732361/python-read-write-vs-shutil-copy/73365632#73365632
# If `shutil` proves to be difficult to work with I can do manual chunking.
@app.post("/uploadfile")
async def createUploadFileEndpoint(
    file: UploadFile = File(...),
    subPath: str = Form(...),
    fullDestination: str = Depends(getDestination),
):
    try:

        saveFile(file, subPath, fullDestination)

        return {
            "message": f"File '{file.filename}' uploaded successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed : {e}")


@app.delete("/deletefile")
async def deleteFileEndpoint(
    subPath: str = Query(...),
    fullDestination: str = Depends(getDestination),
):
    deleteFileOrDirectory(subPath, fullDestination)
    return {
        "message": f"File or directory deleted at '{subPath}'",
    }


# On a Windows implementation this will never be called due to Windows not differentiating between a deleted directory or a deleted file
@app.delete("/deletedirectory")
async def deleteDirectoryEndpoint(
    subPath: str = Query(...),
    fullDestination: str = Depends(getDestination),
):
    dirPath = Path(fullDestination) / subPath

    if dirPath.exists() and dirPath.is_dir():
        try:
            shutil.rmtree(dirPath)
            return {
                "message": f"Directory deleted at '{subPath}'",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Directory deletion failed: {e}"
            )
    else:
        raise HTTPException(status_code=404, detail=f"Directory not found: {subPath}")


@app.put("/renamefile")
async def renameFileEndpoint(
    oldSubPath: str = Form(...),
    newSubPath: str = Form(...),
    fullDestination: str = Depends(getDestination),
):
    oldPath = Path(fullDestination) / oldSubPath
    newPath = Path(fullDestination) / newSubPath

    # High Level Directory Rename Behavior:
    # Check if the old file exists - As referenced earlier this may raise frequently due to file movements from the client firing file renames 
    # when the file's path is changed. This means when a high level directory is moved / renamed all subdirectories and files will fire but will be unable to be moved
    # as the old path will not exist when we renamed the top level directory.
    # If we were to handle this specifically this is where we would do it
    if not oldPath.exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {oldSubPath}")

    # Create parent directories if needed
    newPath.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.move(str(oldPath), str(newPath))
        return {
            "message": f"File renamed from '{oldSubPath}' to '{newSubPath}'",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rename failed: {e}")

# Windows Directory Rename API: 
# This endpoint will NEVER fire on a Windows implementation
@app.put("/renamedirectory")
async def renameDirectoryEndpoint(
    oldSubPath: str = Form(...),
    newSubPath: str = Form(...),
    fullDestination: str = Depends(getDestination),
):
    oldDirPath = Path(fullDestination) / oldSubPath
    newDirPath = Path(fullDestination) / newSubPath

    if not oldDirPath.exists() or not oldDirPath.is_dir():
        raise HTTPException(
            status_code=404, detail=f"Source directory not found: {oldSubPath}"
        )

    try:
        newDirPath.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(oldDirPath), str(newDirPath))
        return {
            "message": f"Directory renamed from '{oldSubPath}' to '{newSubPath}'",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directory rename failed: {e}")


@app.post("/createdirectory")
async def createDirectoryEndpoint(
    subPath: str = Form(...),
    fullDestination: str = Depends(getDestination),
):
    dirPath = Path(fullDestination) / subPath

    try:
        if dirPath.exists():
            if dirPath.is_dir():
                return {"message": f"Directory already exists: {subPath}"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"A file exists at the directory path: {subPath}",
                )

        dirPath.mkdir(parents=True, exist_ok=False)

        return {
            "message": f"Directory created at '{subPath}'",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directory creation failed: {e}")

if __name__ == "__main__":
    # Parse arguments and perform some permissions / error checks
    destination = parseArguments()
    topLevelDir = Path(destination).name
    print(topLevelDir)

    # Overriding our dummy getDestination function so we can inject the destination
    # To our fastAPI functions
    app.dependency_overrides[getDestination] = lambda: destination

    # Start the application
    uvicorn.run(app)
