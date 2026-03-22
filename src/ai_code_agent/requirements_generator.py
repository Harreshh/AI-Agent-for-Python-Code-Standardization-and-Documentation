import subprocess
from pathlib import Path


class RequirementsGenerator:

    def __init__(self, path: str):
        self.path = Path(path)

    def run(self, output_path="requirements.txt"):
        project_path = self.path

        if project_path.is_file():
            project_path = project_path.parent

        try:
            subprocess.run(
                [
                    "pipreqs",
                    str(project_path),
                    "--force",
                    "--savepath",
                    str(output_path)
                ],
                check=True
            )

            print(f"requirements.txt generated at {output_path}")

        except subprocess.CalledProcessError as e:
            print("Error generating requirements:", e)