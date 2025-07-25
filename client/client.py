import httpx, time, tempfile, shutil
from pathlib import Path
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler, FileMovedEvent
from watchdog.observers import Observer
from dependencies.util import parseArguments, stripPath


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

    # https://github.com/syncthing/syncthing - A similar Open Source Project - creates a copy of the file and then uploads that
    def sendFile(self, dataPath, srcPath):
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
                print(r.status_code, r.text)

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
                print(r.status_code, r.text)

                tempCopyPath.unlink(missing_ok=True)

        except Exception as e:
            print(f"Error sending file: {e}")
        return

    # def on_any_event(self, event: FileSystemEvent) -> None:
    #     print(event)

    # Despite being called "on_moved" this refers to when a file is *renamed*
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
                r = self.client.put("http://localhost:8000/renamefile", data=data)
                print(r.status_code, r.text)
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
                response = self.client.put(
                    "http://localhost:8000/renamedirectory", data=data
                )
                print(response.status_code, response.text)
            except Exception as e:
                print(f"Error sending directory rename request: {e}")

        return super().on_moved(event)

    def on_created(self, event):
        if not (event.is_directory):
            print("FILE CREATED ")
            print(event)
            destinationPath = stripPath(event.src_path, topLevelDir)
            dataPath = {"subPath": str(destinationPath)}
            self.sendFile(dataPath=dataPath, srcPath=event.src_path)
        else:
            print("DIRECTORY CREATED")
            print(event)
            subPath = stripPath(event.src_path, self.topLevelDir)
            data = {"subPath": str(subPath)}
            try:
                r = self.client.post("http://localhost:8000/createdirectory", data=data)
                print(r.status_code, r.text)
            except Exception as e:
                print(f"Error sending directory creation request: {e}")
        return super().on_created(event)

    def on_deleted(self, event):
        if not (event.is_directory):
            print("FILE DELETED ")
            print(event)

            destinationPath = stripPath(event.src_path, topLevelDir)
            dataPath = {"subPath": str(destinationPath)}
            r = self.client.delete("http://localhost:8000/deletefile", params=dataPath)
            print(r.text)
        return super().on_deleted(event)

    # ignore DirModifiedEvent - can be fired with non changes
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
            destinationPath = stripPath(event.src_path, topLevelDir)
            dataPath = {"subPath": str(destinationPath)}
            self.sendFile(dataPath=dataPath, srcPath=event.src_path)
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
