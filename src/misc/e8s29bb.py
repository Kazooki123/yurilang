import requests
import threading
import time
import sys

def loading(stop_event):
    width = 10
    pos   = 0
    direction = 1
    
    while not stop_event.is_set():
        bar = ["-"] * width
        for i in range(3):
            if pos + 1 < width:
                bar[pos + i] = "#"
                
        sys.stdout.write("\r[" + "".join(bar) + "] Downloading Keys...")
        sys.stdout.flush()
        
        pos += direction
        
        if pos >= width - 3:
            direction = -1
        elif pos <= 0:
            direction = 1
            
        time.sleep(0.05)
        
    sys.stdout.write("\r[##########] Keys Installed!\n\n")

def keys(file_id, output_name):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    stop_event = threading.Event()
    loader = threading.Thread(
        target=loading,
        args=(stop_event,),
        daemon=True
    )
    loader.start()
    
    try:
        response = requests.get(url, stream=True)
        with open(output_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    finally:
        stop_event.set()
        loader.join()

def jinx():
    files = {
        "prod.zip": "1-nUpcArM2NLxOFdA9B7eGSGI8vOyuRer",
        "title.zip": "1F5Ph6sJnx0ty6CcPWFoI0kn3vArx1cKf"
    }
    
    for filename, file_id in files.items():
        print(f"\nDownloading {filename}...")
        keys(file_id, filename)
    return
