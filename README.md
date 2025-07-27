
# Dropbox

## Functionality

- Update destination folder in real time for directory and file events:
    - Added
    - Deleted
    - Updated
    - Renamed / moved
- Startup Behaviour
    - Assumes empty source and destination directory
- Supports empty directories
- Pattern matching for file types not wanted to be tracked.
- Error handling for serverside requests
  - Security in mind to not leak full server paths

## Future Functionality to consider

- Logging
- API key validation
- Async for HTTP requests


## How it was built

- `FastAPI` with `Uvicorn` - handles async, deployment is easier with the ASGI from uvicorn.
- `Watchdog` https://pypi.org/project/watchdog/ for directory monitoring.
    - Creates an observer thread that fires when various directory changes occur
- `httpx` 
    - Shared `httpx` client to prevent creation of new connections

## Usage Guide

- Designed to be Linux + Windows compatible  
  - However this was built and tested on Windows 10 and as such I suggest using it on Windows.
- Built on version 1.13.5 of Python
- `Cd` into the top level directory
  - i.e. ...\DropBox

## Pre-requisites
- Python 3.13.5
- `pip` - Python package manager
- `venv` - Python virtual environment

### Environment

Please ensure you have `(venv)[https://docs.python.org/3/library/venv.html]` installed and follow the instructions to create and activate your environment depending on your OS and terminal of choice.

When the environment has been activated download the requirements from the provided `requirements.txt`

```
 pip install -r requirements.txt
```

### Server

The server will accept a directory path supplied after the `-path` flag.

The file is located at `server/server.py`.

```
python -m server.server -path "destinationPath" 
```

### Client

The client will accept a directory path supplied after the `-path` flag.

The file is located at `client/client.py`.

```
python -m client.client -path "sourcePath"
```

### Documenation

Documentation is available within the code with docstrings and comments.

FastAPI also provides an interactive API documentation by default at `http://localhost:8000/docs` when the server is running.

## Assumptions and Limitations

- Keep it lean - suggested time is 3-4 hours - no bells and whistles - no formal testing suite - testing performed as the project is built.
- Following the description directly this is a one way sync - we're not concerned about there being "extra" files in the destination directory - if there are we leave them alone or overwrite them in the case of a conflict.
- Under the same logic if I remove something from the destination directory I **do not** expect it to be replaced unless an update or change is triggered in the **source directory**. "Monitor changes in the source directory to syncrhonise changes **to** the destination directory"
    - Could be solved with a "sync" request to the server - Compare os.stats? However Out Of Scope and previously mentioned
- Client and server are on the same localhost - CORS could be a problem if they are not?
- Some file editors will create temporary files in a directory when they are edited.

## Known Problems

All known problems have had fixes applied where applicable - but describe odd / non-intuitive behaviour and are logged here for maintainability.
Where applicable parts of the code relevent to the problem have been labelled with the problem for ease of finding.

- **Windows Directory Rename API:** `"Since the Windows API does not provide information about whether an object is a file or a directory, delete events for directories may be reported as a file deleted event."` [Watchdog docs](https://python-watchdog.readthedocs.io/en/stable/installation.html#supported-platforms-and-caveats)
    - On a windows implementation the `deleteFileEndpoint` is called for both file and directory deletion
    - File and directory deletion is still functional and a description of the fix applied is available in the code.
- Large files create a temp version to be streamed to prevent a time of check to time of use race condition.
- **High Level Directory Rename Behavior:** When renaming a directory this also renames all sub-directories and files
    - This will fire an `on_moved` event for **all** sub-directories / files
    - As the parent directory is renamed on the server first - all sub-directories / files will also be renamed (as it updates their full path)
    - However the `on_moved` events will still make a server request
    - As the sub-directores / files will have already been renamed on the server when the parent directory was renamed.
    - The requests to re-name the server side sub-directories / files will return 404.

## Notes / Thought Process

- First time using FastAPI - bit of a learning curve.
- Little and often approach
- Keep it lean - stick to the brief - stick to the suggested time 
- Don't re-invent the wheel


### Potential Ideas

Some notes I made during the development process

- os.lisdir / os.stats for monitoring (slow + expensive call)
- Comparing a hash of all values within the source directory to a cached copy (slow)
- watchdog - provides directory monitoring with eventhandlers for file system events
- Flask / FastAPI
- File / directory events:
    - Added
    - Deleted
    - Updated
    - Renamed
    - Moved
- Startup behaviour options:
    1. Do Nothing and wait for a observed change.
    2. Copy source directory to destination.
    3. Sync request to compare source to destination and ammend differences.
- Large files (> available memory) may be problematic - research