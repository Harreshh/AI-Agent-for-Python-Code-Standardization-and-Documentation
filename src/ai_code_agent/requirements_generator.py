import subprocess
from pathlib import Path
import sys

class RequirementsGenerator:

    def __init__(self, path: str):
        self.path = Path(path)

    def run(self, output_path="requirements.txt"):
        project_path = self.path

        if project_path.is_file():
            project_path = project_path.parent

        try:
            # On utilise sys.executable (le chemin vers ton python Anaconda)
            # On appelle le module interne exact : "pipreqs.pipreqs"
            subprocess.run(
                [
                    sys.executable, "-m", "pipreqs.pipreqs",
                    str(project_path),
                    "--force",
                    "--savepath", str(output_path)
                ],
                check=True,
                capture_output=True,
                text=True
            )

            print(f"requirements.txt generated at {output_path}")

        except subprocess.CalledProcessError as e:
            # Affiche l'erreur réelle renvoyée par l'outil
            print(f"Error generating requirements: {e.stderr}")
        except Exception as e:
            print(f"Unexpected error: {e}")
