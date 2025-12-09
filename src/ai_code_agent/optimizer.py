import subprocess
import sys
import logging
import shutil
import os
from pathlib import Path

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Optimizer] - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("CodeOptimizer")

class CodeOptimizer:
    """
    Orchestrateur de Standardisation (Wrapper Blindé).
    """

    # --- Ajout de l'argument 'inplace' pour compatibilité CLI ---
    def __init__(self, path: str, inplace: bool = True):
        self.path = Path(path).resolve()
        self.inplace = inplace 
        
        # Liste des outils requis
        self.required_tools = ["autoflake", "isort", "black"]
        self._check_environment()

    def _check_environment(self):
        """RISK MITIGATION #1: L'Échec de l'Environnement."""
        missing = []
        for tool in self.required_tools:
            if not shutil.which(tool):
                missing.append(tool)
        
        if missing:
            logger.critical(f" Outils manquants : {', '.join(missing)}")
            logger.critical(" Veuillez installer : pip install autoflake isort black")
            sys.exit(1)
        else:
            logger.info(" Environnement validé.")

    def run(self):
        """Point d'entrée principal."""
        logger.info(f" Démarrage de l'optimisation sur : {self.path}")
        
        # Avertissement si l'utilisateur espérait ne pas modifier les fichiers
        if not self.inplace:
            logger.warning(" Attention : Avec les outils standards, les modifications sont appliquées directement sur les fichiers.")

        if self.path.is_file():
            self._optimize_file(self.path)
        elif self.path.is_dir():
            for py_file in self.path.rglob("*.py"):
                # Exclusion des dossiers virtuels (venv, .git, etc.)
                if "venv" in py_file.parts or ".git" in py_file.parts:
                    continue
                self._optimize_file(py_file)
        else:
            logger.error(f" Chemin invalide : {self.path}")

    def _optimize_file(self, file_path: Path):
        str_path = str(file_path)
        
        try:
            # --- ÉTAPE 1 : Nettoyage (Autoflake) ---
            cmd_autoflake = [
                "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                "--ignore-init-module-imports", 
                "--remove-unused-variables",
                str_path
            ]
            self._run_subprocess(cmd_autoflake, "Nettoyage (Autoflake)")

            # --- ÉTAPE 2 : Organisation des imports (Isort) ---
            cmd_isort = ["isort", "--profile", "black", str_path]
            self._run_subprocess(cmd_isort, "Tri des imports (Isort)")

            # --- ÉTAPE 3 : Formatage (Black) ---
            cmd_black = ["black", "--quiet", str_path]
            self._run_subprocess(cmd_black, "Formatage (Black)")
            
            logger.info(f" Optimisé : {file_path.name}")

        except Exception as e:
            logger.error(f" Echec sur {file_path.name}: {e}")

    def _run_subprocess(self, command, task_name):
        """Wrapper d'exécution sécurisé."""
        try:
            subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Erreur inconnue"
            raise RuntimeError(f"{task_name} a échoué : {error_msg}")
