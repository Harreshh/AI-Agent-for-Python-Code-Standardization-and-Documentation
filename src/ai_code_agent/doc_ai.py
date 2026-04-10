import ast
import os
import requests

class LocalLLMClient:
    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", "http://localhost:11434/api/generate"
        )
        # We default to "codellama" because that is what you pulled.
        self.model = model or os.getenv("LLM_MODEL", "codellama")

    def generate_docstring(self, func_name: str, source: str, language: str = "English") -> str:
        # Improved Prompt: Forces the AI to be brief.
        prompt = (
            f"You are a strict code documentation tool. "
            f"Write a single sentence describing what the Python function '{func_name}' does. "
            f"CRITICAL RULES:\n"
            f"1. MUST be written in {language}.\n"
            f"2. DO NOT write code. DO NOT repeat the 'def' line or function signature.\n"
            f"3. Start the sentence with an action verb (e.g., 'Saves the...', 'Calculates the...').\n"
            f"4. Output ONLY the description text, no quotes or markdown.\n\n"
            f"Function Source Code:\n{source}\n\n"
            f"Docstring description:"
        )

        try:
            print(f"[LLM] Calling Ollama at {self.base_url} with model={self.model} for {func_name}")

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 60,
                    "temperature": 0.2
                },
            }

            resp = requests.post(self.base_url, json=payload, timeout=180)
            
            if resp.status_code != 200:
                print(f"[LLM ERROR] Status {resp.status_code}: {resp.text}")
                return f"TODO: Fix docstring generation for {func_name}"

            data = resp.json()
            text = (data.get("response") or "").strip()

            if not text:
                return f"TODO: {func_name} (AI returned empty response)"

            # Cleanup
            text = text.replace('"""', "").replace("'''", "").strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if lines:
                return lines[0]
            
            return text

        except Exception as e:
            print(f"[LLM WARNING] Ollama not available or error occurred: {e}")
            return f"TODO: {func_name} function (AI Unavailable)"


class AIDocstringGenerator:
    def __init__(self, path: str, inplace: bool = False, language: str = "en"):
        self.path = path
        self.inplace = inplace
        self.language = language
        self.llm = LocalLLMClient()

    def run(self):
        if os.path.isfile(self.path) and self.path.endswith(".py"):
            self._process_file(self.path)
        elif os.path.isdir(self.path):
            for root, _, files in os.walk(self.path):
                for f in files:
                    if f.endswith(".py"):
                        self._process_file(os.path.join(root, f))
        else:
            print(f"[ERROR] Invalid path: {self.path}")

    def _process_file(self, filepath: str):
        print(f"[doc-ai] Processing {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
        except UnicodeDecodeError:
            print(f"[doc-ai] Skipped {filepath} (encoding error)")
            return

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            print(f"[doc-ai] Syntax error in {filepath}: {e}")
            return

        targets = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    targets.append(node)

        if not targets:
            print("[doc-ai] No missing docstrings found.")
            return

        lines = code.splitlines()
        targets_sorted = sorted(targets, key=lambda n: n.lineno, reverse=True)

        for node in targets_sorted:
            self._insert_docstring(lines, node)

        new_code = "\n".join(lines) + "\n"

        if self.inplace:
            outpath = filepath
        else:
            base, ext = os.path.splitext(filepath)
            outpath = base + "_doc_ai.py"

        with open(outpath, "w", encoding="utf-8") as f:
            f.write(new_code)

        print(f"[doc-ai] Documented file written to: {outpath}")

    def _insert_docstring(self, lines, node):
        source = self._extract_source_snippet(lines, node)
        name = getattr(node, "name", "object")

        doc = self.llm.generate_docstring(name, source, self.language)

        indent = self._get_indent(lines, node)
        doc_line = indent + '"""' + doc + '"""'

        insert_index = node.body[0].lineno - 1
        lines.insert(insert_index, doc_line)

    def _get_indent(self, lines, node):
        if node.body:
            first_body_line_index = node.body[0].lineno - 1
            if first_body_line_index < len(lines):
                first_line = lines[first_body_line_index]
                return first_line[: len(first_line) - len(first_line.lstrip())]
        return "    "

    def _extract_source_snippet(self, lines, node, max_lines: int = 50):
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            start = node.lineno - 1
            end = node.end_lineno
            return "\n".join(lines[start:end])
        start = node.lineno - 1
        end = min(len(lines), start + max_lines)
        return "\n".join(lines[start:end])
