#!/usr/bin/env python3
from flask import Flask, request
from flask import jsonify
import subprocess
import os

app = Flask(__name__)

APP_PATH = "/home/lina/catty-reminders-app"
ENV_CONFIG = "/home/lina/catty-reminders-app/deploy/configs/.env"
APP_SERVICE = "catty-reminders.service"

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
        
        try:
            # 1. Обновляем код
            subprocess.run(["git", "-C", APP_DIR, "pull"], check=True)
            print("Code updated")
            
            # 2. Безопасно обновляем .env (не стирая старые переменные, если они важны)
            lines = []
            if os.path.exists(ENV_FILE):
                with open(ENV_FILE, "r") as f:
                    lines = f.readlines()
            
            # Удаляем старый DEPLOY_REF, если он был
            lines = [line for line in lines if not line.startswith("DEPLOY_REF=")]
            lines.append(f"DEPLOY_REF={commit_sha}\n")
            
            # Записываем всё обратно
            with open(ENV_FILE, "w") as f:
                f.writelines(lines)
            print(f"DEPLOY_REF written: {commit_sha}")
            
            # 3. Перезапускаем сервис
            subprocess.run(["sudo", "systemctl", "restart", APP_SERVICE], check=True)
            print("Service restarted")
            
            return jsonify({"message": "Deployment completed"}), 200
            
        except subprocess.CalledProcessError as e:
            print(f"Subprocess failed with exit code {e.returncode}. Command: {e.cmd}")
            return jsonify({"error": f"Command failed: {e.cmd}"}), 500
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return jsonify({"error": str(e)}), 500
        
    return jsonify({"message": "Not a push event"}), 200
