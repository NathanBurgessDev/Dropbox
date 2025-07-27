import httpx, time, tempfile, shutil
from pathlib import Path
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler, FileMovedEvent
from watchdog.observers import Observer
from dependencies.util import parseArguments, stripPath



'''
Event handler for file system events using watchdog
Handles file and directory events such as creation, modification, deletion, and renaming.
Uses a pattern matching event handler to ignore certain file types and directories.

Watchdog grabs file system events and calls the appropriate methods on the event handler.
This should work for both Windows and Linux systems. However this was built and tested on Windows and as such I suggest using it on Windows.
However there are limitations and caveats to be aware of which are documented in the README.md file as well as the watchdog documentation: https://python-watchdog.readthedocs.io/en/stable/installation.html#supported-platforms-and-caveats

Uses httpx for making HTTP requests to a fastAPI server running at "http://localhost:8000". The code for the server is located as `server/server.py` file.

Documentation for Watchdog: https://python-watchdog.readthedocs.io/en/stable/
Documentation for httpx: https://www.python-httpx.org/
'''
class MyEventHandler(PatternMatchingEventHandler):
    def __init__(self, topLevelDirectory: str, client: httpx.Client):
        super().__init__(
            ignore_patterns=[
                "*.tmp",  # Common Windows temp file pattern
                "~*",  # Backup temp files
                "*.swp",  # Vim swap files
                "*.temp",  # General temp file extension
                "*/temp/*",  # Any temp folder in path
                "*/tmp/*",  # Any tmp folder in path
            ],
            ignore_directories=False,
            case_sensitive=False,
        )
        self.topLevelDir = topLevelDirectory
        self.client = client

    def logResponse(self, response: httpx.Response, action: str):
        if response.status_code != 200:
            print(f"[{action}] Error:  {response.status_code}, {response.text}")
        else:
            print(f"[{action}] Success: {response.status_code}, {response.text}")

    '''
        Send file helper function
        Handles both small and large files

        Small files are read into memory and sent in one go
        Large files are copied and streamed in chunks to avoid race conditions + memory issues. Streaming is done using httpx's default streaming capabilities.

        Input:
        - dataPath: Dictionary containing the subPath for the file
            - example: {"subPath": "foo/New Text Document.txt"}
        - srcPath: String The full path to the source file to be sent 
            - example: "C:\\Users\\Username\\Documents\\Projects\\DropBox\\source_test\\foo\\New Text Document.txt"#

        Returns:
        - HTTP response from the server
        - None if an error occurs during the file sending process
    '''

    # https://github.com/syncthing/syncthing - A similar Open Source Project - creates a copy of the file and then uploads that
    def sendFile(self, dataPath: dict, srcPath: str):
        try:
            fileSize = Path(srcPath).stat().st_size
            filename = Path(srcPath).name

            # Small file < 10_000 bytes —> read into memory
            if fileSize < 10_000:
                with open(srcPath, "rb") as f:
                    fileBytes = f.read()
                files = {"file": (filename, fileBytes)}
                print(f"Sending Small file: {filename} ({fileSize} bytes)")
                r = self.client.post(
                    "http://localhost:8000/uploadfile", files=files, data=dataPath
                )
                self.logResponse(r, "File Upload Small")

            # Large file >= 10_000 bytes —> stream it
            # To solve a race condition with streamed files where the file grows or shrinks during sending
            # resulting in a "h11._util.LocalProtcolError: Too much / Too Little data for declared Content-Length"
            # We create a temp copy of the large file, upload the copy, and then delete the temp file
            else:
                # delete=False here is needed as default behaviour has the tempfile delete when close() is called
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tempCopyPath = Path(tmp.name)
                # .copy2 will attempt to preserve file metadata where possible
                shutil.copy2(srcPath, tempCopyPath)
                with open(tempCopyPath, "rb") as f:
                    files = {"file": (filename, f)}
                    print(f"Sending Large file: {filename} ({fileSize} bytes)")
                    r = self.client.post(
                        "http://localhost:8000/uploadfile", files=files, data=dataPath
                    )
                self.logResponse(r, "File Upload Large")

                tempCopyPath.unlink(missing_ok=True)

        except Exception as e:
            print(f"Error sending file: {e}")
            return None
        #  Return the HTTP response for further processing if needed
        return r


    '''
        Watchdog event handler method
        Specific documenation for this method is available in the official watchdog documentation

        Triggers when a file or directory is moved or renamed
        Moved refers to when a file full handle is changed
        for example:
        From
        - C:\\Users\\Username\\Documents\\Projects\\DropBox\\source_test\\*foo*\\New Text Document.txt
        to
        - C:\\Users\\Username\\Documents\\Projects\\DropBox\\source_test\\*bar*\\New Text Document.txt

        Makes a PUT request to the server to rename the file or directory

        Behaviour of note:
        - When renaming a directory this also renames all sub-directories and files
            - This will fire an `on_moved` event for **all** sub-directories / files
            - As the parent directory is renamed on the server first - all sub-directories / files will also be renamed (as it updates their full path)
            - However the `on_moved` events will still make a server request
            - As the sub-directores / files will have already been renamed on the server when the parent directory was renamed.
            - The requests to re-name the server side sub-directories / files will return 404.
    '''
    # Despite being called "on_moved" this refers to when a file is *renamed* or its directory changes
    def on_moved(self, event):
        if not (event.is_directory):
            print("FILE MOVED")
            print(event)
            oldPath = stripPath(event.src_path, self.topLevelDir)
            newPath = stripPath(event.dest_path, self.topLevelDir)

            data = {
                "oldSubPath": str(oldPath),
                "newSubPath": str(newPath),
            }

            try:
                r = self.client.put(
                    "http://localhost:8000/renamefile", data=data
                    )
                self.logResponse(r, "File Rename / Move")
            except Exception as e:
                print(f"Error sending rename request: {e}")
        else:
            print("DIRECTORY MOVED")
            print(event)

            oldPath = stripPath(event.src_path, self.topLevelDir)
            newPath = stripPath(event.dest_path, self.topLevelDir)

            data = {
                "oldSubPath": str(oldPath),
                "newSubPath": str(newPath),
            }

            try:
                r = self.client.put(
                    "http://localhost:8000/renamedirectory", data=data
                )
                self.logResponse(r, "Directory Rename / Move")
            except Exception as e:
                print(f"Error sending directory rename request: {e}")

        return super().on_moved(event)


    '''
        Watchdog event handler method
        Specific documenation for this method is available in the official watchdog documentation

        Triggers when a file or directory is created
        Makes a POST request to the server to create the file or directory
    '''
    def on_created(self, event):
        if not (event.is_directory):
            print("FILE CREATED ")
            print(event)
            destinationPath = stripPath(event.src_path,self.topLevelDir)
            dataPath = {"subPath": str(destinationPath)}
             # Send the file to the server - logging handled in `sendFile`
            success = self.sendFile(dataPath=dataPath, srcPath=event.src_path)
            if success is None:
                print(f"Error uploading file: exception occurred or no response")
        else:
            print("DIRECTORY CREATED")
            print(event)
            subPath = stripPath(event.src_path, self.topLevelDir)
            data = {"subPath": str(subPath)}
            try:
                r = self.client.post("http://localhost:8000/createdirectory", data=data)
                self.logResponse(r, "Directory Creation")
            except Exception as e:
                print(f"Error sending directory creation request: {e}")
        return super().on_created(event)


    '''
    Watchdog event handler method
    Specific documenation for this method is available in the official watchdog documentation

    Triggers when a file or directory is deleted
    Makes a DELETE request to the server to delete the file or directory
    '''
    # Another interesting bug - this time windows related
    # Windows does not differenciate between a file deletion and a directory deletion
    # It only uses FileDeletedEvent for both
    # https://python-watchdog.readthedocs.io/en/stable/installation.html#supported-platforms-and-caveats
    # from the watchdog documentation : Since the Windows API does not provide information about whether an object is a file or a directory, delete events for directories may be reported as a file deleted event.
    # Naturally this isnt included in the documentation of `on_deleted`
    def on_deleted(self, event):
        destinationPath = stripPath(event.src_path, self.topLevelDir)
        dataPath = {"subPath": str(destinationPath)}
        if not (event.is_directory):
            print("FILE DELETED ")
            print(event)
            try:
                r = self.client.delete("http://localhost:8000/deletefile", params=dataPath)
                self.logResponse(r, "File Deletion")
            except Exception as e:
                print(f"Error sending file deletion request: {e}")
        else:
            print("DIRECTORY DELETED")
            print(event)
            try:
                r = self.client.delete(
                    "http://localhost:8000/deletedirectory", params=dataPath
                )
                self.logResponse(r, "Directory Deletion")
            except Exception as e:
                print(f"Error sending directory deletion request: {e}")
        return super().on_deleted(event)



    '''
    Watchdog event handler method
    Specific documenation for this method is available in the official watchdog documentation

    Triggers when a file or directory is modified
    Makes a POST request to the server to update the file or directory
    
    Note: We ignore directory modification events as they can fire spontaneously without any changes to be uploaded
    It is possible this is due to metadata changes but as this is not documented in the watchdog documentation I am unsure

    '''
    # Fun little race condition here:
    # As we are uploading the file in a chunked format we do a few things
    # 1. The file is opened *but not read into memory* this allows us to upload larger files
    # 2. When making our post request the file size is calculated and the expected size is set
    # 3. As the file is streamed - If the file is edited and saved again between the file size calculated and when the file is streamed - the size of the file has changed
    # we will get an "h11._util.LocalProtcolError: Too much / Too Little data for declared Content-Length"
    # Our http request expects a smaller file than has been provided by the stream
    # How do we solve this???
    # 1. Ignore support for larger files and load the file into memory
    # 2. Catch the error and keep trying until it works - a bit of a jank solution tbh
    # 3. Create a copy of the file elsewhere and upload that - time + storage intensive
    # 4. Lock the file - reaaaaaly janky and likely to be very very very painful
    # https://github.com/syncthing/syncthing - A similar Open Source Project - creates a copy of the file and then uploads that
    def on_modified(self, event):
        if not (event.is_directory):
            print("FILE MODIFIED ")
            print(event)
            destinationPath = stripPath(event.src_path, self.topLevelDir)
            dataPath = {"subPath": str(destinationPath)}
            # Send the file to the server - logging handled in `sendFile`
            success = self.sendFile(dataPath=dataPath, srcPath=event.src_path)
            if success is None:
                print(f"Error uploading file: exception occurred or no response")

        return super().on_modified(event)


if __name__ == "__main__":

    source = parseArguments()
    topLevelDir = Path(source).name
    print(topLevelDir)

    with httpx.Client() as client:
        event_handler = MyEventHandler(topLevelDirectory=topLevelDir, client=client)
        observer = Observer()
        observer.schedule(event_handler=event_handler, path=source, recursive=True)
        observer.start()

        try:
            while observer.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt received.")
            observer.stop()
        observer.join()

        exit(0)
