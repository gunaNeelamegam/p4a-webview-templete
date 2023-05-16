import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set the source directory (Flask templates or static files directory)
SOURCE_DIR = f"{os.path.join(os.path.abspath('.'))}/test_app/templates"

# Set the package name of your Android app
PACKAGE_NAME = "org.kivy.sample"

# Define the event ha]ndler for file changes
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Only handle changes in the source directory
        if event.src_path.endswith(SOURCE_DIR):
            print("Change detected:", event.src_path)
            # Get the relative path of the modified file
            # relative_path = os.path.relpath(event.src_path, start=SOURCE_DIR)
            # Construct the destination path on the Android device
            relative_path = event.src_path.split("/")[-1]
            if relative_path in ("templates"):            
                dest_path = f"/data/data/{PACKAGE_NAME}/files/app/{relative_path}"
            # Trigger adb push to synchronize the file to the Android device
                os.system(f"adb push  {event.src_path} {dest_path}")

# Create the event handler and observer
event_handler = FileChangeHandler()
observer = Observer()
observer.schedule(event_handler, path=SOURCE_DIR, recursive=True)
observer.start()

print("Watching for changes...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()