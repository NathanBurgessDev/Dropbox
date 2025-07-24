
## Functionality

- Update destination folder in real time for directory and file events:
    - Added
    - Deleted
    - Updated
    - Moved
- Startup Behaviour
    - Copy source directory to destination.

## Future Functionality to consider

- Logging
- API key validation


## How it was built

- `FastAPI` with `Uvicorn` - handles async, deployment is easier with the ASGI from uvicorn - should allow for easier scaling as a result.
- `Watchdog` https://pypi.org/project/watchdog/ for directory monitoring.
    - Creates an observer thread that fires when various directory changes occur
- `httpx` - as `requests` is a synchronous library.
    - If we were to add API calls to `server.py`, `httpx` would need to be used - it would be sensible to use the same tooling for both client and server where possible.
    - This is subject to httpx being a pain to use or not
    - Shared `httpx` client to prevent creation of new connections

## Usage Guide

### Environment

### Server

The server will accept a directory path supplied after the `-path` flag.

The file is located at `server/server.py`.

```
python -m server.server -path "destinationPath" 
```

### Client

```
python -m client.client -path "sourcePath"
```

## Assumptions and Limitations

- Keep it lean - suggested time is 3-4 hours - no bells and whistles - no formal testing suit - testing performed as the project is built.
- Following the description directly this is a one way sync - we're not concerned about there being "extra" files in the destination directory - if there are we leave them alone or overwrite them in the case of a conflict.
- Under the same logic if I remove something from the destination directory I **do not** expect it to be replaced unless an update or change is triggered in the **source directory**. "Monitor changes in the source directory to syncrhonise changes **to** the destination directory"
    - Could be solved with a "sync" request to the server - Compare os.stats? However Out Of Scope and previously mentioned
- Client and server are on the same localhost - CORS could be a problem.
- Some file editors will create temporary files in a directory when they are edited - will ignore files starting with `.` for example `.word`.

## Known Problems

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
    
- Empty directories???????????????????