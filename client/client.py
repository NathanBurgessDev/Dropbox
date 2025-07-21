import httpx, time
from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileMovedEvent
from watchdog.observers import Observer

class MyEventHandler(FileSystemEventHandler):
    # def on_any_event(self, event: FileSystemEvent) -> None:
    #     print(event)
        
    # Despite being called "on_moved" this refers to when a file is *renamed*
    def on_moved(self, event):
        print("FILE MOVED")
        print(event)
        return super().on_moved(event)
    
    def on_created(self, event):
        print("FILE CREATED ")
        print(event)
        files = {'file': open(event.src_path,"rb")}
       
        return super().on_created(event)
    
    def on_deleted(self, event):
        print("FILE DELETED ")
        print(event)
        return super().on_deleted(event)
    
    # ignore DirModifiedEvent - can be fired with non changes
    def on_modified(self, event):
        print("FILE MODIFIED ")
        print(event)
        return super().on_modified(event)

if __name__ == "__main__":
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler = event_handler, path = r"C:\Users\Marbo\Documents\Projects\DropBox\destination_test", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()