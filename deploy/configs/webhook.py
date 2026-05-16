import os
import subprocess
import threading
import logging
from flask import Flask, request, jsonify

# Конфигурация путей
APP_PATH = "/home/lina/catty-reminders-app"
ENV_CONFIG = "/home/lina/deployref"
APP_SERVICE = "catty-reminders.service"

# Инициализация Flask приложения
webhook_app = Flask(__name__)
log_file = "/home/lina/deploy.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def execute_deployment(commit_hash):
    """Выполняет развертывание приложения"""
    try:
        # Шаг 1: Синхронизация с репозиторием
        subprocess.run(
            ["git", "-C", APP_PATH, "fetch", "--all"],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "-C", APP_PATH, "reset", "--hard", commit_hash],
            check=True,
            capture_output=True
        )
        
        # Шаг 2: Сохраняем ссылку на коммит для CI/CD
        with open(ENV_CONFIG, "w") as config_file:
            config_file.write(f"DEPLOY_REF={commit_hash}\n")
        
        # Шаг 3: Перезапуск сервиса приложения
        subprocess.run(
            ["sudo", "systemctl", "restart", APP_SERVICE],
            check=True
        )
        
        logging.info(f"Deployment successful: {commit_hash[:8]}")
        
    except subprocess.CalledProcessError as proc_err:
        logging.error(f"Command failed: {proc_err}")
    except Exception as deploy_error:
        logging.error(f"Deployment error: {str(deploy_error)}")

@webhook_app.route('/', methods=['POST'])
def webhook_listener():
    """Обработчик входящих webhook запросов"""
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type == 'push':
        payload = request.get_json()
        new_commit = payload.get('after') if payload else None
        
        # Проверяем, что это не удаление ветки
        if new_commit and new_commit != "0" * 40:
            deploy_thread = threading.Thread(
                target=execute_deployment,
                args=(new_commit,)
            )
            deploy_thread.daemon = True
            deploy_thread.start()
            
            return jsonify({"message": "accepted"}), 202
    
    return jsonify({"message": "no action"}), 200

if __name__ == '__main__':
    webhook_app.run(
        host='0.0.0.0',
        port=8080,
        threaded=True
    )
