import os
import pytest
import paramiko
import requests
import datetime
import logging


logger = logging.getLogger("test_index")
logger.setLevel(logging.INFO)


TARGET_HOST = os.getenv("TARGET_HOST")
TARGET_PORT = os.getenv("TARGET_PORT")
TARGET_USER = os.getenv("TARGET_USER")
TARGET_PASSWORD_FILE = os.getenv("TARGET_PASSWORD_FILE")
CHECK_MINUTES = int(os.getenv("CHECK_MINUTES"))

# Читаем пароль из секрета
with open(TARGET_PASSWORD_FILE, "r") as f:
    TARGET_PASSWORD = f.read().strip()


@pytest.fixture(scope="module")
def ssh_client():
    """
    Создаём SSH-соединение один раз на модуль тестов.
    После всех тестов соединение закрывается.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=TARGET_HOST,
        port=22,
        username=TARGET_USER,
        password=TARGET_PASSWORD
    )
    yield client
    client.close()


def test_apache_running(ssh_client):
    """Проверяем, что Apache запущен"""
    stdin, stdout, stderr = ssh_client.exec_command("ps aux | grep httpd | grep -v grep")
    output = stdout.read().decode().strip()
    assert output != "", "Apache2 не запущен"


def test_apache_logs(ssh_client):
    """
    Проверяем логи Apache за последние N минут на наличие ошибок.
    """
    
    cmd = "tail -n 200 /usr/local/apache2/logs/error_log"
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    logs = stdout.read().decode().splitlines()

    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(minutes=CHECK_MINUTES)

    recent_errors = []
    for line in logs:
        if line.startswith("["):
            try:
                ts = line.split("]")[0].lstrip("[")
                dt = datetime.datetime.strptime(ts.split()[0:4] + [ts.split()[-1]], "%a %b %d %H:%M:%S %Y")
                if dt >= cutoff:
                    recent_errors.append(line)
            except Exception:
                continue

    assert not recent_errors, f"В логах Apache есть ошибки за последние {CHECK_MINUTES} минут:\n" + "\n".join(recent_errors)


def test_index_page():
    """Проверяем, что /index возвращает 200 и содержит HTML"""
    url = f"http://{TARGET_HOST}:{TARGET_PORT}/index.html"
    r = requests.get(url)
    assert r.status_code == 200, "/index.html недоступен"
    assert "<html" in r.text.lower(), "Содержимое /index.html некорректное"
    
    msg = f"Index доступен по http://localhost:8080/index.html"

    # Логирование для pytest-html
    logger.info(msg)


def test_404_page():
    """Проверяем, что несуществующая страница возвращает 404"""
    url = f"http://{TARGET_HOST}:{TARGET_PORT}/nonexistent_page"
    r = requests.get(url)
    assert r.status_code == 404, "Несуществующая страница не возвращает 404"


def test_tar_works(ssh_client):
    cmd = "mkdir /tmp/test && echo 'hello' > /tmp/test/test.txt && tar -cf /tmp/test/test.tar /tmp/test/test.txt && tar -xf /tmp/test/test.tar -C /tmp/test && cat /tmp/test/test.txt && rm -rf /tmp/test"
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    output = stdout.read().decode().strip()
    ssh_client.exec_command(f"rm -rf /tmp/test")
    assert output == "hello", f"tar failed, got: {output}"


def test_ln_works(ssh_client):
    cmd = "mkdir /tmp/test && echo 'world' > /tmp/test/original.txt && ln -s //tmp/test/original.txt /tmp/test/symlink.txt && cat /tmp/test/symlink.txt && rm -rf /tmp/test"
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    output = stdout.read().decode().strip()
    assert output == "world", f"ln failed, got: {output}"
