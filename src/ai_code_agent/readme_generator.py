from pathlib import Path
import ast
import os
import requests


class ReadmeGenerator:
    def __init__(self, path: str, model: str = "codellama"):
        self.path = Path(path)
        self.model = model

    def _collect_py_files(self):
        if self.path.is_file() and self.path.suffix == ".py":
            return [self.path]
        elif self.path.is_dir():
            return list(self.path.rglob("*.py"))
        return []

    def _extract_project_info(self):
        files = self._collect_py_files()

        info = {
            "project_name": self.path.name if self.path.is_dir() else self.path.stem,
            "python_files": [],
            "imports": set(),
            "classes": [],
            "functions": [],
            "entry_points": [],
        }

        entry_candidates = {
            "main.py", "app.py", "run.py", "run_gui.py", "web_gui.py", "cli.py"
        }

        for file_path in files:
            rel = str(file_path.relative_to(self.path)) if self.path.is_dir() else file_path.name
            info["python_files"].append(rel)

            if file_path.name in entry_candidates:
                info["entry_points"].append(rel)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            info["imports"].add(alias.name.split(".")[0])

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            info["imports"].add(node.module.split(".")[0])

                    elif isinstance(node, ast.ClassDef):
                        info["classes"].append({
                            "name": node.name,
                            "file": rel
                        })

                    elif isinstance(node, ast.FunctionDef):
                        info["functions"].append({
                            "name": node.name,
                            "file": rel
                        })

            except Exception:
                continue

        info["imports"] = sorted(info["imports"])
        return info

    def _build_prompt(self, info: dict) -> str:
        return f"""
You are writing a README.md for a Python project.

Write a project-specific README in clear natural English.
Do not be generic.
Base your writing only on the project information below.

Project name:
{info["project_name"]}

Python files:
{chr(10).join("- " + f for f in info["python_files"][:50])}

Detected entry points:
{chr(10).join("- " + f for f in info["entry_points"]) or "- None detected"}

Detected imports:
{", ".join(info["imports"][:50])}

Detected classes:
{chr(10).join("- " + c["name"] + " (" + c["file"] + ")" for c in info["classes"][:30]) or "- None"}

Detected functions:
{chr(10).join("- " + fn["name"] + " (" + fn["file"] + ")" for fn in info["functions"][:50]) or "- None"}

Write a README with:
- project overview
- main features
- project structure
- installation
- usage
- output files if relevant
- notes and limitations if relevant

Be specific to the project.
Do not invent features that are not supported by the detected files.
Output only markdown.
"""

    def _query_ollama(self, prompt: str) -> str:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=600
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def run(self, output_path: str = "README.md"):
        info = self._extract_project_info()
        prompt = self._build_prompt(info)

        try:
            readme = self._query_ollama(prompt)
        except Exception as e:
            readme = f"# {info['project_name']}\n\nREADME generation failed.\n\nError: {e}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme)

        print(f"README.md generated at: {output_path}")