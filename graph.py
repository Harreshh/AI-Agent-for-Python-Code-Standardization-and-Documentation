import ast
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from graphviz import Digraph

PROJECT_DIR = "/Users/valentingempp/Documents/ai-code-agent"
OUTPUT_NAME = "dependency_graph"
IGNORE_DIRS = {"__pycache__", ".venv", "venv", "venv_tk", "build"}

def should_ignore(path):
    return any(part in IGNORE_DIRS for part in path.split(os.sep))

def parse_imports(file_path):
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except Exception:
        pass
    return imports

def build_graph():
    print(f"\nRendering Graph: {time.strftime('%H:%M:%S')}")

    graph = Digraph(format="png")
    graph.attr(
        rankdir="TB", 
        bgcolor="#0a0a0a",   
        fontcolor="white",
        nodesep="0.6",       
        ranksep="1.0",       
        splines="polyline"   
    )

    file_nodes = {}
    graph.attr('node', fontname="Helvetica", fontsize="10", fontcolor="black")

    for root, dirs, files in os.walk(PROJECT_DIR):
        if should_ignore(root):
            continue

        parent = os.path.relpath(root, PROJECT_DIR)
        parent = parent if parent != "." else "PROJECT_ROOT"

        graph.node(
            parent,
            label=os.path.basename(parent) if parent != "PROJECT_ROOT" else "ROOT",
            shape="box",
            style="filled,rounded",
            fillcolor="#FFD966" if parent != "PROJECT_ROOT" else "#F08080" 
        )

        for d in dirs:
            full_dir = os.path.join(root, d)
            if should_ignore(full_dir):
                continue
            child = os.path.relpath(full_dir, PROJECT_DIR)
            graph.edge(parent, child, color="#444444")

        for f in files:
            file_path = os.path.join(root, f)
            node_id = os.path.relpath(file_path, PROJECT_DIR)
            is_py = f.endswith(".py")
            color = "#98FB98" if is_py else "#D9D9D9" 

            graph.node(node_id, f, shape="capsule" if is_py else "box", style="filled", fillcolor=color)
            graph.edge(parent, node_id, color="#444444")

            if is_py:
                file_nodes[node_id] = file_path

    for node, path in file_nodes.items():
        imports = parse_imports(path)
        for imp in imports:
            for target in file_nodes:
                if imp.replace(".", os.sep) in target:
                    graph.edge(node, target, color="#00FFFF", penwidth="2.5", constraint="false")

    graph.render(OUTPUT_NAME, cleanup=True)
    print(f"Refresh Complete")

class DebouncedWatcher(FileSystemEventHandler):
    def __init__(self, delay=0.5):
        self.delay = delay
        self.timer = None

    def on_any_event(self, event):
        if should_ignore(event.src_path) or event.event_type == 'opened':
            return
        
        if self.timer is not None:
            self.timer.cancel()
        
        self.timer = threading.Timer(self.delay, build_graph)
        self.timer.start()

if __name__ == "__main__":
    build_graph()

    observer = Observer()
    event_handler = DebouncedWatcher(delay=0.5)
    observer.schedule(event_handler, PROJECT_DIR, recursive=True)
    observer.start()

    print(f"Live Sync Active (Flicker-Free): {PROJECT_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
