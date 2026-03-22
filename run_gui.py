import os
import socket
import subprocess
import sys

def pick_free_port(default=8787):
    # Try default, otherwise pick a free port
    def free(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) != 0
    if free(default):
        return default
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    # Ensure src is visible
    env = os.environ.copy()
    src = os.path.join(root, "src")
    env["PYTHONPATH"] = src + (os.pathsep + env.get("PYTHONPATH", ""))

    port = pick_free_port(8787)
    env["CP_PORT"] = str(port)

    # Run web_gui.py with the same interpreter
    subprocess.check_call([sys.executable, "web_gui.py"], env=env)

if __name__ == "__main__":
    main()
