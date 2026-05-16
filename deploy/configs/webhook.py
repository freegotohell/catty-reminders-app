#!/usr/bin/env python3
from flask import Flask, request
from flask import jsonify
import subprocess
import os

app = Flask(__name__)

APP_DIR = "/home/lina/catty-reminders-app"
ENV_FILE = "/home/lina/catty-reminders-app/deploy/configs/.env"
APP_SERVICE = "catty-reminders.service"
PORT = 8080

@app.route('/', methods=['GET', 'POST'])
def handle():
    if request.method == 'GET':
        return jsonify({"message": "webhook handler running"}), 200
    
    if request.headers.get('X-GitHub-Event') == 'push':
        data = request.json
        commit_sha = data.get('after') if data else None
        
        if not commit_sha or commit_sha == '0000000000000000000000000000000000000000':
            return jsonify({"message": "No valid SHA"}), 200
            
        print("Starting deployment...")
        
        subprocess.run(["git", "-C", APP_DIR, "pull"], check=True)
        print("Code updated")
        
        with open(ENV_FILE, "w") as f:
            f.write(f"DEPLOY_REF={commit_sha}")
        print(f"DEPLOY_REF written: {commit_sha}")
        
        subprocess.run(["sudo", "systemctl", "restart", APP_SERVICE], check=True)
        print("Service restarted")
        
        return jsonify({"message": "Deployment completed"}), 200
        
    return jsonify({"message": "Not a push event"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
