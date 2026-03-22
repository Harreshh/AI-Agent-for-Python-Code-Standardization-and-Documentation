"""
Professional Code Analyzer - Safran Tech
Orchestrate des outils industriels au lieu de réinventer la roue.
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import sys


class CodeAnalyzer:
    """
    Analyzer qui délègue aux outils professionnels :
    - Flake8 pour PEP8
    - Pylint pour la qualité du code
    - Radon pour la complexité
    - Autoflake pour détecter les imports/variables inutilisés
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.results = {
            "metadata": {
                "analyzed_path": str(self.path),
                "timestamp": datetime.now().isoformat(),
                "total_files": 0,
                "analyzer_version": "2.0-professional"
            },
            "files": [],
            "flake8_issues": [],      # Issues PEP8
            "pylint_issues": [],      # Issues qualité code
            "complexity": {},         # Complexité par fichier
            "unused_code": [],        # Imports/variables inutilisés
            "summary": {}             # Résumé des scores
        }

    def run(self):
        """Point d'entrée principal : lance toutes les analyses."""
        print(f"[Professional Analyzer] Starting analysis: {self.path}")
        print("="*60)

        # 1. Vérifier que les outils sont installés
        self._check_tools_installed()

        # 2. Collecter les fichiers Python
        self._collect_files()

        # 3. Lancer les analyses
        print("\n[1/4] Running Flake8 (PEP8 checker)...")
        self._run_flake8()

        print("\n[2/4] Running Pylint (Code quality)...")
        self._run_pylint()

        print("\n[3/4] Running Radon (Complexity)...")
        self._run_radon()

        print("\n[4/4] Running Autoflake (Unused code)...")
        self._run_autoflake()

        # 4. Générer le résumé
        self._generate_summary()

        # 5. Afficher le rapport
        self._print_summary()

        print("\n" + "="*60)
        print("[Professional Analyzer] Analysis complete!")

    # VÉRIFICATION DES OUTILS
    def _check_tools_installed(self):
        """
        Vérifie que tous les outils nécessaires sont installés.
        Si un outil manque, affiche un message clair.
        """
        required_tools = ["flake8", "pylint", "radon", "autoflake"]
        missing_tools = []

        for tool in required_tools:
            try:
                # Essayer d'exécuter 'tool --version'
                subprocess.run(
                    [tool, "--version"],
                    capture_output=True,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)

        if missing_tools:
            print(f"\n[ERROR] Missing tools: {', '.join(missing_tools)}")
            print(f"Install them with: pip install {' '.join(missing_tools)}")
            sys.exit(1)

        print(" All required tools are installed")

    # COLLECTE DES FICHIERS
    def _collect_files(self):
        """
        Parcourt le chemin et collecte tous les fichiers .py
        """
        if self.path.is_file() and self.path.suffix == ".py":
            self.results["files"].append(str(self.path))
        elif self.path.is_dir():
            for py_file in self.path.rglob("*.py"):
                self.results["files"].append(str(py_file))
        else:
            print(f"[ERROR] Invalid path: {self.path}")
            sys.exit(1)

        self.results["metadata"]["total_files"] = len(self.results["files"])
        print(f"[✓] Found {len(self.results['files'])} Python file(s)")

    # FLAKE8 (PEP8 + Erreurs de base)
    def _run_flake8(self):
        """
        Flake8 vérifie :
        - Respect de PEP8 (espaces, longueur de ligne)
        - Erreurs de syntaxe basiques
        - Imports inutilisés (code F401)
        """
        try:
            result = subprocess.run(
                ["flake8", str(self.path), "--format=json"],
                capture_output=True,
                text=True
            )

            # Flake8 retourne du JSON avec --format=json
            # Mais par défaut, il utilise un format texte
            # On va utiliser le format par défaut et parser
            result = subprocess.run(
                ["flake8", str(self.path)],
                capture_output=True,
                text=True
            )

            # Parser la sortie ligne par ligne
            # Format: fichier:ligne:colonne: code message
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue

                parts = line.split(":", 3)
                if len(parts) >= 4:
                    filepath, lineno, col, message = parts
                    # Extraire le code d'erreur (ex: E501, F401)
                    code = message.strip().split()[0]

                    self.results["flake8_issues"].append({
                        "file": filepath.strip(),
                        "line": int(lineno.strip()),
                        "column": int(col.strip()),
                        "code": code,
                        "message": message.strip()
                    })

            print(f"   Found {len(self.results['flake8_issues'])} PEP8 issues")

        except Exception as e:
            print(f"[WARNING] Flake8 failed: {e}")

    # PYLINT (Qualité du code)
    def _run_pylint(self):
        """
        Pylint vérifie :
        - Conventions de nommage
        - Complexité des fonctions
        - Code dupliqué
        - Erreurs logiques potentielles
        """
        try:
            result = subprocess.run(
                ["pylint", str(self.path), "--output-format=json"],
                capture_output=True,
                text=True
            )

            # Pylint retourne du JSON
            if result.stdout:
                pylint_data = json.loads(result.stdout)

                for issue in pylint_data:
                    self.results["pylint_issues"].append({
                        "file": issue.get("path", ""),
                        "line": issue.get("line", 0),
                        "column": issue.get("column", 0),
                        "type": issue.get("type", ""),
                        "symbol": issue.get("symbol", ""),
                        "message": issue.get("message", "")
                    })

            print(f"   Found {len(self.results['pylint_issues'])} quality issues")

        except json.JSONDecodeError:
            print("[WARNING] Pylint output is not valid JSON")
        except Exception as e:
            print(f"[WARNING] Pylint failed: {e}")

    # RADON (Complexité)
    def _run_radon(self):
        """
        Radon calcule la complexité cyclomatique :
        - A : Très simple (1-5)
        - B : Simple (6-10)
        - C : Modéré (11-20)
        - D : Complexe (21-50)
        - F : Très complexe (50+)
        """
        try:
            result = subprocess.run(
                ["radon", "cc", str(self.path), "-j"],
                capture_output=True,
                text=True
            )

            # Radon retourne du JSON avec -j
            if result.stdout:
                radon_data = json.loads(result.stdout)

                for filepath, functions in radon_data.items():
                    total_complexity = 0
                    for func in functions:
                        total_complexity += func.get("complexity", 0)

                    self.results["complexity"][filepath] = {
                        "total": total_complexity,
                        "functions": len(functions),
                        "details": functions
                    }

            print(f"   Analyzed complexity for {len(self.results['complexity'])} file(s)")

        except json.JSONDecodeError:
            print("[WARNING] Radon output is not valid JSON")
        except Exception as e:
            print(f"[WARNING] Radon failed: {e}")

    # AUTOFLAKE (Code inutilisé)
    def _run_autoflake(self):
        """
        Autoflake détecte :
        - Imports inutilisés (plus fiable que notre code maison)
        - Variables inutilisées
        """
        for filepath in self.results["files"]:
            try:
                result = subprocess.run(
                    [
                        "autoflake",
                        "--check",  # Ne modifie pas, juste vérifie
                        "--remove-all-unused-imports",
                        "--remove-unused-variables",
                        filepath
                    ],
                    capture_output=True,
                    text=True
                )

                # Si autoflake trouve des problèmes, il affiche un diff
                if result.stdout:
                    self.results["unused_code"].append({
                        "file": filepath,
                        "message": "Contains unused imports or variables",
                        "details": result.stdout
                    })

            except Exception as e:
                print(f"[WARNING] Autoflake failed on {filepath}: {e}")

        print(f"   Found {len(self.results['unused_code'])} file(s) with unused code")

    # GÉNÉRATION DU RÉSUMÉ
    def _generate_summary(self):
        """
        Calcule un score global de qualité du code :
        - Nombre total de problèmes
        - Score Pylint
        - Complexité moyenne
        """
        self.results["summary"] = {
            "total_flake8_issues": len(self.results["flake8_issues"]),
            "total_pylint_issues": len(self.results["pylint_issues"]),
            "files_with_unused_code": len(self.results["unused_code"]),
            "average_complexity": self._calculate_avg_complexity(),
            "health_score": self._calculate_health_score()
        }

    def _calculate_avg_complexity(self) -> float:
        """Calcule la complexité moyenne par fichier."""
        if not self.results["complexity"]:
            return 0.0

        total = sum(
            data["total"]
            for data in self.results["complexity"].values()
        )
        return round(total / len(self.results["complexity"]), 2)

    def _calculate_health_score(self) -> str:
        """
        Score de santé du code (A-F) :
        - A : Excellent (< 5 problèmes)
        - B : Bon (5-20)
        - C : Moyen (20-50)
        - D : Faible (50-100)
        - F : Critique (100+)
        """
        total_issues = (
            len(self.results["flake8_issues"]) +
            len(self.results["pylint_issues"]) +
            len(self.results["unused_code"])
        )

        if total_issues < 5:
            return "A (Excellent)"
        elif total_issues < 20:
            return "B (Good)"
        elif total_issues < 50:
            return "C (Average)"
        elif total_issues < 100:
            return "D (Poor)"
        else:
            return "F (Critical)"

    # AFFICHAGE DU RAPPORT
    def _print_summary(self):
        """Affiche un résumé lisible dans le terminal."""
        print("\n" + "="*60)
        print("PROFESSIONAL ANALYSIS SUMMARY")
        print("="*60)

        summary = self.results["summary"]
        print(f"Health Score: {summary['health_score']}")
        print(f"Average Complexity: {summary['average_complexity']}")
        print(f"\nIssues Found:")
        print(f"  - Flake8 (PEP8): {summary['total_flake8_issues']}")
        print(f"  - Pylint (Quality): {summary['total_pylint_issues']}")
        print(f"  - Unused Code: {summary['files_with_unused_code']} file(s)")

        # Afficher quelques exemples
        if self.results["flake8_issues"]:
            print(f"\nTop 5 Flake8 Issues:")
            for issue in self.results["flake8_issues"][:5]:
                print(f"  - {issue['file']}:{issue['line']} {issue['message']}")

        if self.results["pylint_issues"]:
            print(f"\nTop 5 Pylint Issues:")
            for issue in self.results["pylint_issues"][:5]:
                print(f"  - {issue['file']}:{issue['line']} {issue['message']}")

    # EXPORT JSON
    def export_results(self, output_path: str = "professional_audit.json"):
        """
        Exporte les résultats au format JSON pour l'Optimizer.
        Ce fichier servira de "mémoire" entre les modules.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n  Professional audit saved: {output_path}")
        print(f"    Use with: code-agent optimize --audit {output_path}")
