"""
Code Optimizer - Safran Tech
"""

import json
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
import sys
import shutil


class CodeOptimizer:
    """
    Optimizer intelligent qui :
    - Lit l'audit JSON en profondeur
    - Applique Black/isort AVANT les suppressions (évite réintroduction)
    - Supprime précisément les lignes listées dans l'audit
    - Protège les variables underscore et commentaires
    - Vérifie les suppressions avec double-check
    """

    def __init__(self, path: str, inplace: bool = False):
        self.path = Path(path)
        self.inplace = inplace
        self.corrections = []
        self.protected_lines = set()
        self.backup_dir = None

    def run_with_audit(self, audit_path: str = "audit.json"):
        """Mode intelligent : Lit l'audit JSON et applique corrections ciblées."""
        print(f"[Smart Optimizer] Using audit: {audit_path}")
        print("="*60)
        
        # 1. Charger l'audit
        try:
            with open(audit_path, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] Audit file not found: {audit_path}")
            print("[INFO] Falling back to autonomous mode")
            return self.run()
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in audit: {e}")
            return

        # 2. Vérifier outils installés
        self._check_tools_installed()

        # 3. Extraire fichiers
        files_to_process = audit_data.get("files", [])
        if not files_to_process:
            print("[WARNING] No files found in audit.")
            return

        print(f"[✓] Processing {len(files_to_process)} file(s)")

        # 4. Backup si nécessaire
        if self.inplace:
            self._create_backup(files_to_process)

        # 5. NOUVEAU : Formater AVANT suppression
        print("\n[1/3] Pre-formatting with Black and isort...")
        target_files = self._get_target_files_for_formatting(files_to_process)
        self._run_black(target_files)
        self._run_isort(target_files)

        # 6. Suppressions ciblées APRÈS formatage
        print("\n[2/3] Applying targeted removals from audit...")
        for filepath in files_to_process:
            if not os.path.exists(filepath):
                print(f"[WARNING] File not found: {filepath}")
                continue
            
            print(f"\n[Processing] {filepath}")
            self._optimize_file_smart(filepath, audit_data)

        # 7. Vérification finale
        print("\n[3/3] Verifying suppressions...")
        self._verify_suppressions(files_to_process, audit_data)

        # 8. Résumé
        self._print_summary()
        
        print("\n" + "="*60)
        print("[Smart Optimizer] Optimization complete!")
        if self.backup_dir:
            print(f"[✓] Backup saved in: {self.backup_dir}")

    def run(self):
        """Mode autonome (fallback)."""
        print(f"[Smart Optimizer] Running autonomous mode")
        print("="*60)
        
        self._check_tools_installed()
        
        files = []
        if self.path.is_file() and self.path.suffix == ".py":
            files.append(str(self.path))
        elif self.path.is_dir():
            files = [str(f) for f in self.path.rglob("*.py")]

        if self.inplace:
            target_files = files
        else:
            # créer les *_optimized.py avant d'appliquer les outils
            target_files = self._get_target_files_for_formatting(files)  

        print("\n[1/3] Removing unused code...")
        self._run_autoflake_generic(target_files)
        print("\n[2/3] Sorting imports...")
        self._run_isort(target_files)
        print("\n[3/3] Formatting code...")
        self._run_black(target_files)
        
        self._print_summary()

    # OPTIMISATION APRÈS FORMATAGE

    def _optimize_file_smart(self, filepath: str, audit_data: dict):
        """
        CORRIGÉ : Supprime après que Black/isort ont tourné.
        """
        # Déterminer le fichier cible
        if self.inplace:
            target_file = filepath
        else:
            p = Path(filepath)
            target_file = str(p.with_name(p.stem + "_optimized" + p.suffix))
        
        # Lire le fichier déja formaté
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[ERROR] Cannot read {target_file}: {e}")
            return

        # Détecter protections
        protected = self._detect_protected_lines(lines)
        
        # Extraire issues depuis audit
        issues = self._extract_file_issues(filepath, audit_data)
        
        # NOUVEAU : Mapper les numéros de ligne (fichier formaté ≠ original)
        issues = self._remap_line_numbers(lines, issues, filepath)
        
        # Supprimer imports inutilisés
        lines = self._remove_unused_imports_smart(lines, issues["unused_imports"], protected)
        
        # Supprimer variables inutilisées
        lines = self._remove_unused_variables_smart(lines, issues["unused_variables"], protected)
        
        # Corrections mineures (tabs, whitespace déjà gérés par Black normalement)
        lines = self._fix_spacing_issues(lines, issues["spacing_issues"])
        lines = self._fix_tabs(lines, issues["tab_lines"])
        lines = self._fix_trailing_whitespace(lines, issues["trailing_whitespace"])
        
        # Écrire fichier final
        self._write_optimized_file(target_file, lines)

    def _remap_line_numbers(self, formatted_lines: List[str], issues: dict, original_filepath: str) -> dict:
        """
        NOUVEAU : Remapper les numéros de ligne après formatage.
        Recherche le contenu exact pour trouver la nouvelle ligne.
        """
        # Pour l'instant, on assume que les numéros sont proches
        # (Black ne change pas trop l'ordre des lignes)
        # Une vraie solution serait de faire un diff, mais c'est complexe
        
        # SIMPLIFICATION : On cherche les imports/variables par leur contenu
        remapped = {
            "unused_imports": [],
            "unused_variables": [],
            "spacing_issues": issues["spacing_issues"],
            "tab_lines": issues["tab_lines"],
            "trailing_whitespace": issues["trailing_whitespace"]
        }
        
        # Pour les imports, chercher par nom
        for imp in issues["unused_imports"]:
            import_name = self._extract_import_name_from_message(imp["message"])
            # Chercher la ligne contenant cet import
            for i, line in enumerate(formatted_lines, 1):
                if f"import {import_name}" in line or f"from {import_name}" in line:
                    remapped["unused_imports"].append({
                        "line": i,
                        "message": imp["message"]
                    })
                    break
        
        # Pour les variables, chercher par nom
        for var in issues["unused_variables"]:
            var_name = self._extract_variable_name_from_message(var["message"])
            # Chercher la ligne contenant cette variable
            for i, line in enumerate(formatted_lines, 1):
                if re.search(rf'\b{re.escape(var_name)}\s*=', line):
                    remapped["unused_variables"].append({
                        "line": i,
                        "message": var["message"]
                    })
                    break
        
        return remapped

    def _extract_file_issues(self, filepath: str, audit_data: dict) -> dict:
        """Extrait problèmes de ce fichier depuis l'audit."""
        filepath_normalized = str(Path(filepath)).replace("\\", "/")
        
        issues = {
            "unused_imports": [],
            "unused_variables": [],
            "spacing_issues": [],
            "tab_lines": set(),
            "trailing_whitespace": set()
        }
        
        for issue in audit_data.get("flake8_issues", []):
            issue_file = str(Path(issue["file"])).replace("\\", "/")
            
            if issue_file == filepath_normalized:
                code = issue["code"]
                line = issue["line"]
                
                if code == "F401":
                    issues["unused_imports"].append({
                        "line": line,
                        "message": issue["message"]
                    })
                elif code == "F841":
                    issues["unused_variables"].append({
                        "line": line,
                        "message": issue["message"]
                    })
                elif code in ["E231", "E225"]:
                    issues["spacing_issues"].append({
                        "line": line,
                        "column": issue.get("column", 0),
                        "code": code
                    })
                elif code == "W191":
                    issues["tab_lines"].add(line)
                elif code == "W291":
                    issues["trailing_whitespace"].add(line)
        
        return issues

    def _detect_protected_lines(self, lines: List[str]) -> Set[int]:
        """Détecte lignes protégées."""
        protected = set()
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Protection par commentaire
            if any(keyword in line_stripped.lower() for keyword in [
                "ne pas supprimer", "do not remove", "keep this",
                "intentionnel", "intentional"
            ]):
                protected.add(i)
                continue
            
            # Protection variables _
            if re.match(r'\s*_[a-zA-Z0-9_]+\s*=', line_stripped):
                protected.add(i)
                continue
        
        return protected

    def _remove_unused_imports_smart(self, lines: List[str], unused_imports: List[dict], protected: Set[int]) -> List[str]:
        """Supprime imports inutilisés."""
        lines_to_remove = set()
        
        for issue in unused_imports:
            line_num = issue["line"]
            
            if line_num in protected:
                self.corrections.append(f"PROTECTED: Line {line_num} (import) kept")
                continue
            
            if line_num > len(lines):
                continue  # Ligne invalide
            
            lines_to_remove.add(line_num)
            import_name = self._extract_import_name_from_message(issue["message"])
            self.corrections.append(f"REMOVED: Unused import '{import_name}' at line {line_num}")
        
        new_lines = [line for i, line in enumerate(lines, 1) if i not in lines_to_remove]
        return new_lines

    def _remove_unused_variables_smart(self, lines: List[str], unused_vars: List[dict], protected: Set[int]) -> List[str]:
        """Supprime variables inutilisées."""
        lines_to_remove = set()
        
        for issue in unused_vars:
            line_num = issue["line"]
            
            if line_num in protected:
                var_name = self._extract_variable_name_from_message(issue["message"])
                self.corrections.append(f"PROTECTED: Variable '{var_name}' at line {line_num} kept (_)")
                continue
            
            if line_num > len(lines):
                continue
            
            lines_to_remove.add(line_num)
            var_name = self._extract_variable_name_from_message(issue["message"])
            self.corrections.append(f"REMOVED: Unused variable '{var_name}' at line {line_num}")
        
        new_lines = [line for i, line in enumerate(lines, 1) if i not in lines_to_remove]
        return new_lines

    def _fix_spacing_issues(self, lines: List[str], spacing_issues: List[dict]) -> List[str]:
        """Corrige espacement (normalement déjà fait par Black)."""
        if not spacing_issues:
            return lines
        
        issues_by_line = {}
        for issue in spacing_issues:
            line_num = issue["line"]
            if line_num not in issues_by_line:
                issues_by_line[line_num] = []
            issues_by_line[line_num].append(issue)
        
        new_lines = []
        for i, line in enumerate(lines, 1):
            if i in issues_by_line:
                line = re.sub(r',(?=\S)', ', ', line)
                line = re.sub(r'(\w)=(\w)', r'\1 = \2', line)
                self.corrections.append(f"FIXED: Spacing at line {i}")
            new_lines.append(line)
        
        return new_lines

    def _fix_tabs(self, lines: List[str], tab_lines: Set[int]) -> List[str]:
        """Convertit tabs (normalement déjà fait par Black)."""
        if not tab_lines:
            return lines
        
        new_lines = []
        for i, line in enumerate(lines, 1):
            if i in tab_lines:
                line = line.replace('\t', '    ')
                self.corrections.append(f"FIXED: Tab at line {i}")
            new_lines.append(line)
        
        return new_lines

    def _fix_trailing_whitespace(self, lines: List[str], trailing_lines: Set[int]) -> List[str]:
        """Supprime trailing whitespace."""
        if not trailing_lines:
            return lines
        
        new_lines = []
        for i, line in enumerate(lines, 1):
            if i in trailing_lines:
                line = line.rstrip() + '\n' if line.endswith('\n') else line.rstrip()
                self.corrections.append(f"FIXED: Trailing whitespace at line {i}")
            new_lines.append(line)
        
        return new_lines
    
    # VÉRIFICATION POST-SUPPRESSION

    def _verify_suppressions(self, files: List[str], audit_data: dict):
        """Vérifie que les suppressions ont été appliquées."""
        print("\n[Verification] Checking suppressions...")
        
        for filepath in files:
            target = filepath if self.inplace else str(Path(filepath).with_name(Path(filepath).stem + "_optimized.py"))
            
            if not os.path.exists(target):
                continue
            
            with open(target, "r", encoding="utf-8") as f:
                final_code = f.read()
            
            # Extraire imports inutilisés de l'audit
            issues = self._extract_file_issues(filepath, audit_data)
            
            # Vérifier chaque import inutilisé
            for imp in issues["unused_imports"]:
                import_name = self._extract_import_name_from_message(imp["message"])
                
                # Chercher si l'import est toujours là
                if re.search(rf'^\s*import\s+{re.escape(import_name)}\b', final_code, re.MULTILINE):
                    print(f"WARNING: 'import {import_name}' still present in {Path(target).name}")
                elif re.search(rf'^\s*from\s+{re.escape(import_name)}\s+import', final_code, re.MULTILINE):
                    print(f"WARNING: 'from {import_name} import' still present in {Path(target).name}")

    # HELPERS

    def _extract_import_name_from_message(self, message: str) -> str:
        """Extrait nom import depuis message."""
        match = re.search(r"'([^']+)'", message)
        return match.group(1) if match else "unknown"

    def _extract_variable_name_from_message(self, message: str) -> str:
        """Extrait nom variable depuis message."""
        match = re.search(r"variable '([^']+)'", message)
        return match.group(1) if match else "unknown"

    def _write_optimized_file(self, filepath: str, lines: List[str]):
        """Écrit fichier optimisé."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"   ✓ Written: {filepath}")
        except Exception as e:
            print(f"   ✗ Error writing {filepath}: {e}")

    def _get_target_files(self, source_files: List[str]) -> List[str]:
        """Retourne fichiers cibles."""
        if self.inplace:
            return source_files
        else:
            return [
                str(Path(f).with_name(Path(f).stem + "_optimized" + Path(f).suffix))
                for f in source_files
                if Path(f).with_name(Path(f).stem + "_optimized" + Path(f).suffix).exists()
            ]

    def _get_target_files_for_formatting(self, source_files: List[str]) -> List[str]:
        """NOUVEAU : Prépare fichiers pour formatage initial."""
        targets = []
        
        for src in source_files:
            if self.inplace:
                targets.append(src)
            else:
                # Créer copie pour formatage
                p = Path(src)
                dest = p.with_name(p.stem + "_optimized" + p.suffix)
                try:
                    shutil.copy2(src, dest)
                    targets.append(str(dest))
                except Exception as e:
                    print(f"[ERROR] Could not copy {src}: {e}")
        
        return targets

    # OUTILS EXTERNES

    def _check_tools_installed(self):
        """Vérifie outils."""
        required = ["black", "isort"]
        missing = []
        
        for tool in required:
            if shutil.which(tool) is None:
                missing.append(tool)
        
        if missing:
            print(f"[WARNING] Missing tools: {', '.join(missing)}")
            print(f"Install with: pip install {' '.join(missing)}")

    def _create_backup(self, files: List[str]):
        """Crée backup."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(f"backup_{timestamp}")
        self.backup_dir.mkdir(exist_ok=True)
        
        print(f"Creating backup in: {self.backup_dir}")
        
        for f in files:
            try:
                shutil.copy2(f, self.backup_dir / Path(f).name)
            except Exception as e:
                print(f"[WARNING] Could not backup {f}: {e}")

    def _run_autoflake_generic(self, files: List[str]):
        """Autoflake générique."""
        for filepath in files:
            try:
                subprocess.run([
                    "autoflake", "--in-place",
                    "--remove-all-unused-imports",
                    "--remove-unused-variables",
                    filepath
                ], check=True, capture_output=True)
                self.corrections.append(f"autoflake: cleaned {Path(filepath).name}")
            except subprocess.CalledProcessError:
                pass

    def _run_isort(self, files: List[str]):
        """Trie imports."""
        for filepath in files:
            try:
                subprocess.run(["isort", filepath], check=True, capture_output=True)
                self.corrections.append(f"isort: sorted {Path(filepath).name}")
            except subprocess.CalledProcessError:
                pass

    def _run_black(self, files: List[str]):
        """Formate code."""
        for filepath in files:
            try:
                subprocess.run(["black", "--quiet", filepath], check=True, capture_output=True)
                self.corrections.append(f"black: formatted {Path(filepath).name}")
            except subprocess.CalledProcessError:
                pass

    def _print_summary(self):
        """Affiche résumé."""
        print(f"\n{'='*60}")
        print("OPTIMIZATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total corrections: {len(self.corrections)}")
        
        if self.corrections:
            print("\nSample corrections:")
            for c in self.corrections[:15]:
                print(f"  {c}")
            
            if len(self.corrections) > 15:
                print(f"  ... and {len(self.corrections) - 15} more")
