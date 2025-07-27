
# Dropbox
A client server file mirroring system.

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
  - Care taken to not leak information about server paths
- A quick unit test to demonstrate how a more comprehensive test suite would be built.

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

- Designed to be Linux + Windows + MacOS compatible  
  - However this was built and tested on Windows 10 and as such I suggest using it on Windows 10.
- Built on version 1.13.5 of Python
- `Cd` into the top level directory
  - i.e. ...\DropBox

## Pre-requisites
- Python 3.13.5
- `pip` - Python package manager
- `venv` - Python virtual environment
- Empty source and destination directories

### Environment

Please ensure you have [venv](https://docs.python.org/3/library/venv.html) installed and follow the instructions to create and activate your environment depending on your OS and terminal of choice.

When the environment has been activated download the requirements from the provided `requirements.txt`

```
 pip install -r requirements.txt
```

### Server

The server will accept a directory path supplied after the `-path` flag where the files + directories will be uploaded to.

The file is located at `server/server.py`.

```
python -m server.server -path "destinationPath" 
```

### Client

The client will accept a directory path supplied after the `-path` flag which will be monitored for file system events.

The file is located at `client/client.py`.

```
python -m client.client -path "sourcePath"
```

### Tests
The tests are located in the `tests` directory.

```
python -m pytest
```

### Documenation

Documentation is available within the code with docstrings and comments.

FastAPI also provides an interactive API documentation by default at `http://localhost:8000/docs` when the server is running.

## Known Problems

All known problems have had fixes applied where applicable - but describe odd / non-intuitive behaviour and are logged here for maintainability.
Where applicable parts of the code relevent to the problem have been labelled with the problem for ease of maintainability.

- **Windows Directory Rename API: - Fix Applied** `"Since the Windows API does not provide information about whether an object is a file or a directory, delete events for directories may be reported as a file deleted event."` [Watchdog docs](https://python-watchdog.readthedocs.io/en/stable/installation.html#supported-platforms-and-caveats)
    - On a windows implementation the `deleteFileEndpoint` is called for both file and directory deletion
    - File and directory deletion is still functional and a description of the fix applied is available in the code.
- Fix Applied - Large files create a temp version to be streamed to prevent a time of check to time of use race condition.
- **High Level Directory Rename Behavior: - Fix Applied** When renaming a directory this also renames all sub-directories and files
    - This will fire an `on_moved` event for **all** sub-directories / files
    - As the parent directory is renamed on the server first - all sub-directories / files will also be renamed (as it updates their full path)
    - However the `on_moved` events will still make a server request
    - As the sub-directores / files will have already been renamed on the server when the parent directory was renamed.
    - The requests to re-name the server side sub-directories / files will return 404.
- Sometimes copying a file to the `source` directory will encounter a `[WinError 32] The process cannot access the file because it is being used by another process` error or `[Errno 13] Permission denied: "FILEPATH"` on a **Windows 11** implementation.
  - So far through testing this will resolve itself on both Windows 10 and MacOS as the final `file modified` event will successfully access the file after the file is unlocked.
  - However - on a Windows 11 implementation this final `file modified` event will *still* have the file locked and will return either a `[WinError 32] The process cannot access the file because it is being used by another process` or a `[Errno 13] Permission denied: "FILEPATH"`
  - I suspect this is due to Windows creating the file handle - firing the `file created` event - and then writing to the file - firing the `file modified` event.
  - Through testing on both a Windows 10 Laptop and Desktop machine, the final `file modified` event is fired *after* the file is unlocked and the file can be accessed and the problem does not occur.
  - However on Windows 11 the final `file modified` event is fired *before* the file is unlocked and the file cannot be accessed.
  - While a current fix for this has *not* been implemented - a proposed solution would be to add a retry mechanism on a permission denied error that will timeout after a certain number of attempts to prevent an infinite loop if a file is truly locked or permission denied.
  - This retry mechanism could be futher improved by allocating the retry attempts to a separate thread or providing async functionality to file upload. However this would require significant changes to the current implementation and is not within the scope of this project.
  - It is also worth noting that the Windows 11 implementation this was tested on *did* have OneDrive enabled - it is possible that this is resulting in the file being locked for an extended period of time.

## Testing

- Built primarily on Windows 10 and tested as produced.
- Tested:
  - Copying files
  - Copying directories
  - Renaming files
  - Renaming directories
  - Deleting files
  - Deleting directories
  - Moving files externally and internally
  - Moving directories externally and internally
  - Large files (> 1GB) and small files (< 1MB)
  - Several file types including:
    - `.txt`
    - `.jpg`
    - `.png`
    - `.mp4`
    - `.zip`
    - `.pdf`
  - Large directories (creates a large number of log messages)
- Less robust testing done on MacOS and Windows 11 to check basic functionality.
- Two user tests to confirm usage guide is explanatory
- An example of a basic unit test is provided in [tests](https://github.com/NathanBurgessDev/Dropbox/tree/fb0ddc60913490dbaa593daf4940cb7b435dccc1/tests) to provide an example of how a more comprehensive test suite could be built.

## Notes / Thought Process

Some notes I made during the development process - I have elected to keep them here to provide insight into my thought process and to guide future development.

- First time using FastAPI - bit of a learning curve.
- Little and often approach
- Keep it lean - stick to the brief - stick to the suggested time 
- Don't re-invent the wheel

## Assumptions and potential ideas

- Keep it lean - suggested time is 3-4 hours - no bells and whistles - no formal testing suite - testing performed as the project is built.
- Following the description directly this is a one way sync - we're not concerned about there being "extra" files in the destination directory - if there are we leave them alone or overwrite them in the case of a conflict.
- Under the same logic if I remove something from the destination directory I **do not** expect it to be replaced unless an update or change is triggered in the **source directory**. "Monitor changes in the source directory to syncrhonise changes **to** the destination directory"
    - Could be solved with a "sync" request to the server - Compare os.stats? However Out Of Scope and previously mentioned
- Client and server are on the same localhost - CORS could be a problem if they are not?
- Some file editors will create temporary files in a directory when they are edited.

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

Time Taken: 7-10 hours - Worked on this *very* intermittently for a week or so doing 20 minutes here and there hence the "little and often" approach.
