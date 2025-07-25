import uvicorn, os, shutil
from fastapi import FastAPI, UploadFile, File, Form, Depends, Query, HTTPException
from pathlib import Path
from dependencies.util import parseArguments

# Globals - don't like this but FastAPI has forced my hand
app: FastAPI = FastAPI()


# Function to be overriden for dependency injection
# Useful for testing
def getDestination():
    return


# Potentially rework for async - not particularly familar with FastAPI in this format
# Works for now
def saveFile(uploadFile: UploadFile, subPath: str, fullDestination: str):
    destinationPath = Path(fullDestination) / subPath

    # Check if the parent directory exists - if not then create it
    destinationPath.parent.mkdir(parents=True, exist_ok=True)

    with destinationPath.open("wb") as buffer:
        shutil.copyfileobj(uploadFile.file, buffer)

    return


def deleteFileOrDirectory(subPath: str, fullDestination: str):
    destinationPath = Path(fullDestination) / subPath

    if os.path.exists(destinationPath):
        if destinationPath.is_file():
            os.remove(destinationPath)
        elif destinationPath.is_dir():
            shutil.rmtree(destinationPath)
        else:
            print("Unsupported file type for deletion:", destinationPath)
    else:
        print("File does not exist: ", destinationPath)

    return


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
# If `shutil` proves to be difficult to work with I can do manual chunking.
@app.post("/uploadfile")
async def createUploadFileEndpoint(
    file: UploadFile = File(...),
    subPath: str = Form(...),
    fullDestination: str = Depends(getDestination),
):
    print(file)
    print(subPath)
    print(fullDestination)

    saveFile(file, subPath, fullDestination)

    return {
        "filename": file.filename,
        "subPath": subPath,
        "fullDestination": fullDestination,
    }


@app.delete("/deletefile")
async def deleteFileEndpoint(
    subPath: str = Query(...),
    fullDestination: str = Depends(getDestination),
):
    deleteFileOrDirectory(subPath, fullDestination)
    return {
        "subPath": subPath,
        "fullDestination": fullDestination,
    }


# On a windows implementation this will never be called due to Windows not differenciating between a deleted directory or a deleted file
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
                "fullDestination": fullDestination,
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Directory deletion failed: {e}"
            )
    else:
        raise HTTPException(status_code=404, detail=f"Directory not found: {dirPath}")


@app.put("/renamefile")
async def renameFileEndpoint(
    oldSubPath: str = Form(...),
    newSubPath: str = Form(...),
    fullDestination: str = Depends(getDestination),
):
    oldPath = Path(fullDestination) / oldSubPath
    newPath = Path(fullDestination) / newSubPath

    if not oldPath.exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {oldPath}")

    # Create parent directories if needed
    newPath.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.move(str(oldPath), str(newPath))
        return {
            "oldPath": oldPath,
            "newPath": newPath,
            "fullDestination": fullDestination,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rename failed: {e}")


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
            status_code=404, detail=f"Source directory not found: {oldDirPath}"
        )

    try:
        newDirPath.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(oldDirPath), str(newDirPath))
        return {
            "oldDirPath": oldDirPath,
            "newDirPath": newDirPath,
            "fullDestination": fullDestination,
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
                return {"message": f"Directory already exists: {dirPath}"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"A file exists at the directory path: {dirPath}",
                )

        dirPath.mkdir(parents=True, exist_ok=False)

        return {
            "message": f"Directory created at '{subPath}'",
            "fullDestination": fullDestination,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directory creation failed: {e}")


# On Event is Deprecated - use Lifespan Event Handlers instead :
# https://fastapi.tiangolo.com/advanced/events/
# @app.on_event("startup")
# async def startup_event():
#     print("App Started")

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
