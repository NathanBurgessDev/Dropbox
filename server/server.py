import uvicorn, os
from fastapi import FastAPI, UploadFile, File, Form, Depends
from pathlib import Path
from dependencies.util import parseArguments


# Globals - Probably nicer to use some object or singleton in a larger codebase
app: FastAPI = FastAPI()


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
@app.post("/uploadfile")
async def create_upload_file(
    file: UploadFile = File(...), destination: str = Form(...)
):
    print(file)
    print(destination)
    return {"filename": file.filename}


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

    # Start the application
    uvicorn.run(app)
