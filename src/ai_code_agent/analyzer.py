import ast
import os
import re
from collections import defaultdict

class CodeAnalyzer:
    """
    Enterprise-grade static analyzer:
    - PEP8 checks
    - AST structural analysis
    - Complexity computation
    - Duplicate code detection
    - Missing documentation
    - Import circularity detection
    """

    def __init__(self, path):
        self.path = path
        self.results = {
            "files": [],
            "errors": [],
            "warnings": [],
            "complexity": {},
            "missing_docstrings": [],
            "duplicates": [],
            "import_cycles": [],
            "pep8": []
        }

    def run(self):
        print(f"[Analyzer] Starting analysis: {self.path}")

        if os.path.isfile(self.path) and self.path.endswith(".py"):
            self._analyze_file(self.path)

        elif os.path.isdir(self.path):
            for root, _, files in os.walk(self.path):
                for f in files:
                    if f.endswith(".py"):
                        self._analyze_file(os.path.join(root, f))
        else:
            print("[ERROR] Invalid path.")
            return

        self._detect_import_cycles()
        self._detect_duplicates()

        self._print_summary()

    # File analysis

    def _analyze_file(self, filepath):
        self.results["files"].append(filepath)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
        except:
            self.results["errors"].append(f"Cannot read file: {filepath}")
            return

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.results["errors"].append(f"Syntax error in {filepath}: {e}")
            return

        # Ast analyses
        self._analyze_docstrings(filepath, tree)
        self._compute_complexity(filepath, tree)
        self._analyze_structure(filepath, tree)

        # Pep8 checks (light but essential)
        self._check_pep8(filepath, code)

        # Register imports for cycle detection
        self._register_imports(filepath, tree)

    # Docstring analysis

    def _analyze_docstrings(self, filepath, tree):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    self.results["missing_docstrings"].append(
                        f"{filepath}:{node.lineno} -> Missing docstring in {node.__class__.__name__} '{node.name}'"
                    )

    # Complexity 

    def _compute_complexity(self, filepath, tree):
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (
                ast.If, ast.For, ast.While,
                ast.And, ast.Or,
                ast.Try, ast.With,
                ast.ExceptHandler,
            )):
                complexity += 1

        self.results["complexity"][filepath] = complexity

        if complexity > 12:
            self.results["warnings"].append(
                f"{filepath} has high cyclomatic complexity: {complexity}"
            )

    # structural analysis

    def _analyze_structure(self, filepath, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                depth = self._nesting_depth(node)
                if depth > 4:
                    self.results["warnings"].append(
                        f"{filepath}:{node.lineno} -> Deep nesting ({depth} levels)"
                    )

    def _nesting_depth(self, node, current=0):
        if not isinstance(node, ast.If):
            return current
        return max(
            [current] + [
                self._nesting_depth(child, current + 1)
                for child in ast.iter_child_nodes(node)
            ]
        )

    # Pep8 Checker

    def _check_pep8(self, filepath, code):
        for i, line in enumerate(code.splitlines(), 1):

            # Line too long
            if len(line) > 120:
                self.results["pep8"].append(
                    f"{filepath}:{i} -> Line too long ({len(line)} > 120)"
                )

            # Trailing spaces
            if line.endswith(" "):
                self.results["pep8"].append(
                    f"{filepath}:{i} -> Trailing whitespace"
                )

            # Missing space after comma
            if re.search(r",[A-Za-z0-9_]", line):
                self.results["pep8"].append(
                    f"{filepath}:{i} -> Missing space after comma"
                )

            # Incorrect indent (tab)
            if "\t" in line:
                self.results["pep8"].append(
                    f"{filepath}:{i} -> Tab indent found (use 4 spaces)"
                )

    # Import cycle detection

    def _register_imports(self, filepath, tree):
        basename = os.path.splitext(os.path.basename(filepath))[0]

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports += [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])

        self.results.setdefault("imports_graph", {})[basename] = imports

    def _detect_import_cycles(self):
        graph = self.results.get("imports_graph", {})
        visited = set()

        def dfs(node, path):
            if node in path:
                cycle = " -> ".join(path + [node])
                self.results["import_cycles"].append(f"Cycle detected: {cycle}")
                return

            for nxt in graph.get(node, []):
                dfs(nxt, path + [node])

        for mod in graph:
            dfs(mod, [])

    # Duplicate code detection 

    def _detect_duplicates(self):
        seen = defaultdict(list)

        for fpath in self.results["files"]:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            snippet = tuple(lines[:10])  # first 10 lines heuristic
            seen[snippet].append(fpath)

        for snippet, files in seen.items():
            if len(files) > 1:
                self.results["duplicates"].append(
                    f"Possible duplicate code in: {', '.join(files)}"
                )

    # Report

    def _print_summary(self):
        print("\nANALYSIS SUMMARY")
        print(f"Analyzed files: {len(self.results['files'])}")

        if self.results["errors"]:
            print("\nErrors:")
            for e in self.results["errors"]:
                print("  -", e)

        if self.results["warnings"]:
            print("\nWarnings:")
            for w in self.results["warnings"]:
                print("  -", w)

        if self.results["missing_docstrings"]:
            print("\nMissing docstrings:")
            for d in self.results["missing_docstrings"]:
                print("  -", d)

        if self.results["pep8"]:
            print("\nPEP8 issues:")
            for p in self.results["pep8"]:
                print("  -", p)

        if self.results["import_cycles"]:
            print("\nImport cycles:")
            for c in self.results["import_cycles"]:
                print("  -", c)

        if self.results["duplicates"]:
            print("\nDuplicate code warnings:")
            for c in self.results["duplicates"]:
                print("  -", c)

        print("\nEND OF REPORT\n")
