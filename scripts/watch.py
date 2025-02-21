import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_app()

    def restart_app(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        self.process = subprocess.Popen(['python', '-m', 'reup.dev'])

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"Change detected in {event.src_path}, restarting...")
            self.restart_app()

if __name__ == "__main__":
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, 'reup', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if handler.process:
            handler.process.terminate()
    observer.join() 