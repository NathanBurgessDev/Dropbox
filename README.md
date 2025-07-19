
## Potential Ideas
- os.lisdir / os.stats for monitoring (slow + expensive call)
- Comparing a hash of all values within the source directory to a cached copy (slow)
- watchdog - provides directory monitoring with eventhandlers for file system events
- Flask / FastAPI
- File / directory events:
    - Added
    - Deleted
    - Updated
    - Moved
- Startup behaviour options:
    1. Do Nothing and wait for a observed change.
    2. Copy source directory to destination.
    3. Sync request to compare source to destination and ammend differences.
    

## How it was built

- FastAPI with Uvicorn - handles async, deployment is easier with the ASGI from uvicorn - should allow for easier scaling as a result.
- https://pypi.org/project/watchdog/ For directory monitoring

## Usage Guide

### Environment

### Server

### Client


## Assumptions and Limitations

- Keep it lean - suggested time is 3-4 hours - no bells and whistles - no formal testing suit - testing performed as the project is built.
- Following the description directly this is a one way sync - we're not concerned about there being "extra" files in the destination directory - if there are we leave them alone or overwrite them in the case of a conflict.
- Under the same logic if I remove something from the destination directory I **do not** expect it to be replaced unless an update or change is triggered in the **source directory**. "Monitor changes in the source directory to syncrhonise changes **to** the destination directory"
    - Could be solved with a "sync" request to the server - Compare os.stats? However Out Of Scope and previously mentioned

## Known Problems

## Notes / Thought Process

- First time using FastAPI - bit of a learning curve.
- Little and often approach
- Keep it lean - stick to the brief - stick to the suggested time 
- Don't re-invent the wheel