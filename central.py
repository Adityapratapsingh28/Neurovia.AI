import subprocess
import requests
import time
import os
import atexit
from flask import Flask

app = Flask(__name__)

microservices = [
    {"name": "Bone_fracture", "path": r"D:\neurovia-main\backend\Bone_fracture\app.py", "port": 3020},
    {"name": "Brain_Tumor", "path": r"D:\neurovia-main\backend\Brain_Tumor\app.py", "port": 3019},
    {"name": "Tuberclusis", "path": r"D:\neurovia-main\backend\Tuberculosis\app.py", "port": 3021},
    {"name": "Medicine", "path": r"D:\neurovia-main\backend\Medicine_desp\app.py", "port": 5000},
    {"name": "GeniTell", "path": r"D:\neurovia-main\backend\genitell\app.py", "port": 8082},
]

running_processes = []

def launch_microservices():
    for service in microservices:
        print(f"Launching {service['name']} on port {service['port']}...")
        try:
            process = subprocess.Popen(["python", service["path"]],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            running_processes.append({"process": process, "service": service})
        except Exception as e:
            print(f"❌ Failed to launch {service['name']}: {e}")

    print("\nWaiting for services to start...\n")
    time.sleep(5)

    for proc in running_processes:
        port = proc["service"]["port"]
        name = proc["service"]["name"]
        try:
            response = requests.get(f"http://127.0.0.1:{port}", timeout=2)
            if response.status_code == 200:
                print(f"✅ {name} is running at http://127.0.0.1:{port}")
            else:
                print(f"⚠️ {name} is not responding properly at http://127.0.0.1:{port}")
        except requests.exceptions.RequestException:
            print(f"❌ {name} is NOT running at http://127.0.0.1:{port}")

def cleanup():
    print("\nShutting down microservices...")
    for proc in running_processes:
        proc["process"].terminate()
    print("✅ All microservices stopped.")

atexit.register(cleanup)

launch_microservices()

if __name__ == '__main__':
    app.run(debug=True, port=5050)
