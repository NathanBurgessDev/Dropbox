import httpx, time
from pathlib import Path
from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileMovedEvent
from watchdog.observers import Observer
from dependencies.util import parseArguments, stripPath


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, topLevelDirectory: str):
        super().__init__()
        self.topLevelDir = topLevelDirectory

    # def on_any_event(self, event: FileSystemEvent) -> None:
    #     print(event)

    # Despite being called "on_moved" this refers to when a file is *renamed*
    def on_moved(self, event):
        print("FILE MOVED")
        print(event)
        return super().on_moved(event)

    def on_created(self, event):
        if not (event.is_directory):
            print("FILE CREATED ")
            print(event)
            destinationPath = stripPath(event.src_path, topLevelDir)
            print(destinationPath)
            dataPath = {"subPath": str(destinationPath)}
            try:
                files = {"file": open(event.src_path, "rb")}
            except:
                print("File failed to open")
            print(files)
            r = httpx.post(
                "http://localhost:8000/uploadfile", files=files, data=dataPath
            )
            print(r.text)
            files["file"].close()
        return super().on_created(event)

    def on_deleted(self, event):
        print("FILE DELETED ")
        print(event)
        return super().on_deleted(event)

    # ignore DirModifiedEvent - can be fired with non changes
    #
    def on_modified(self, event):
        print("FILE MODIFIED ")
        print(event)
        return super().on_modified(event)


if __name__ == "__main__":

    source = parseArguments()
    topLevelDir = Path(source).name
    print(topLevelDir)

    event_handler = MyEventHandler(topLevelDir)
    observer = Observer()
    observer.schedule(event_handler=event_handler, path=source, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
