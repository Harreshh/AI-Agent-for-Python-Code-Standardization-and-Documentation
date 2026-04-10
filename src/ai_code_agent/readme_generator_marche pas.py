from pathlib import Path
import re
import requests


# ---------------------------------------------------------------------------
# HtmlReportParser
# Lit le fichier docstrings_report.html généré à l'étape 3/6 et en extrait
# toutes les données structurées (fichier, nom, type, docstring).
# Aucune dépendance externe : on utilise uniquement le module re de la stdlib.
# ---------------------------------------------------------------------------

class HtmlReportParser:
    def __init__(self, report_path: str):
        self.report_path = Path(report_path)

    # -- Utilitaire : supprime les balises HTML et décode les entités de base --
    @staticmethod
    def _strip_html(text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace(
            "&gt;", ">"
        ).replace("&quot;", '"').replace("&#x27;", "'").replace("&nbsp;", " ")
        return text.strip()

    def parse(self) -> dict:
        """
        Retourne un dict :
        {
            "project_name": str,
            "generated": str,
            "files": [
                {
                    "name": str,          # ex: "test_demo_2.py"
                    "path": str,          # chemin complet extrait du HTML
                    "items": [
                        {
                            "name": str,          # ex: "add"
                            "type": str,          # "function" | "class" | "module"
                            "line": str,          # ex: "Line 3"
                            "docstring": str      # texte propre, "" si absent
                        },
                        ...
                    ]
                },
                ...
            ]
        }
        """
        if not self.report_path.exists():
            raise FileNotFoundError(
                f"Rapport introuvable : {self.report_path}\n"
                "Vérifiez le chemin passé à ReadmeGenerator."
            )

        with open(self.report_path, "r", encoding="utf-8") as f:
            html = f.read()

        result = {
            "project_name": "",
            "generated": "",
            "files": [],
        }

        # -- Nom du projet : balise <title> --
        m = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        if m:
            result["project_name"] = self._strip_html(m.group(1))

        # -- Date de génération : première pill "Generated: ..." --
        m = re.search(r"Generated:\s*([^<]+)", html)
        if m:
            result["generated"] = m.group(1).strip()

        # -- Blocs fichiers : chaque <details class="file"> ... </details> --
        file_blocks = re.split(r"<details[^>]*class=['\"]file['\"][^>]*>", html)[1:]

        for block in file_blocks:
            # Nom du fichier : <div class="file__name">...</div>
            m_name = re.search(
                r'<div[^>]*class=["\']file__name["\'][^>]*>(.*?)</div>',
                block, re.DOTALL
            )
            file_name = self._strip_html(m_name.group(1)) if m_name else "unknown.py"

            # Chemin complet : <div class="file__path">...</div>
            m_path = re.search(
                r'<div[^>]*class=["\']file__path["\'][^>]*>(.*?)</div>',
                block, re.DOTALL
            )
            file_path = self._strip_html(m_path.group(1)) if m_path else ""

            file_entry = {"name": file_name, "path": file_path, "items": []}

            # -- Blocs docstrings : chaque <div class="doc"> --
            doc_blocks = re.split(r'<div[^>]*class=["\']doc["\'][^>]*>', block)[1:]

            for doc in doc_blocks:
                # Nom de l'item : <div class="doc__title">...</div>
                m_title = re.search(
                    r'<div[^>]*class=["\']doc__title["\'][^>]*>(.*?)</div>',
                    doc, re.DOTALL
                )
                item_name = self._strip_html(m_title.group(1)) if m_title else ""

                # Type : classe CSS du badge (function / class / module)
                m_badge = re.search(
                    r'<span[^>]*class=["\']badge\s+(function|class|module)["\'][^>]*>',
                    doc
                )
                item_type = m_badge.group(1) if m_badge else "function"

                # Numéro de ligne : <div class="doc__meta">Line X</div>
                m_meta = re.search(
                    r'<div[^>]*class=["\']doc__meta["\'][^>]*>(.*?)</div>',
                    doc, re.DOTALL
                )
                item_line = self._strip_html(m_meta.group(1)) if m_meta else ""

                # Docstring : contenu de <pre>...</pre>
                m_pre = re.search(r"<pre[^>]*>(.*?)</pre>", doc, re.DOTALL)
                raw_doc = self._strip_html(m_pre.group(1)) if m_pre else ""

                # Si le <pre> contient une signature brute ("def ..."),
                # ce n'est pas une vraie docstring — on la marque comme absente
                if raw_doc.startswith("def "):
                    raw_doc = ""

                file_entry["items"].append({
                    "name": item_name,
                    "type": item_type,
                    "line": item_line,
                    "docstring": raw_doc,
                })

            result["files"].append(file_entry)

        return result

    def build_context_block(self) -> str:
        """
        Produit un bloc texte structuré, prêt à être injecté dans le prompt.

        Exemple de sortie :
            [test_demo_2.py]  (C:\\...\\test_demo_2.py)
              - function `add` (Line 3): Adds two numbers together and returns the result.
              - function `area_circle` (Line 7): Returns the area of a circle given its radius.
        """
        data = self.parse()
        lines = []

        for f in data["files"]:
            lines.append(f"[{f['name']}]  ({f['path']})")
            for item in f["items"]:
                doc = item["docstring"] if item["docstring"] else "No description provided."
                lines.append(
                    f"  - {item['type']} `{item['name']}` ({item['line']}): {doc}"
                )
            lines.append("")  # ligne vide entre fichiers

        return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# ReadmeGenerator
# Utilise HtmlReportParser comme unique source de vérité.
# Plus aucune analyse AST, plus aucun scan de fichiers .py.
# ---------------------------------------------------------------------------

class ReadmeGenerator:
    def __init__(self, model: str = "codellama"):
        self.model = model

    def _build_prompt(self, context: str, project_name: str) -> str:
        return f"""
You are a professional technical writer for a Python project.
Write a README.md based EXCLUSIVELY on the documented facts provided below.

STRICT RULES:
1. DO NOT INVENT features, algorithms, or behaviors not mentioned in the facts.
2. TRANSLATION: If a description is in Spanish or any other language, translate it into clear English.
3. SPECIFICITY: Use the function/class descriptions to write the 'Main Features' section.
4. NO HALLUCINATIONS: Never mention formulas, libraries, or techniques (e.g. Bailey-Borwein-Plouffe, numpy) unless they explicitly appear in the facts below.
5. HONESTY: If an item has "No description provided.", list it by name only — do not guess its purpose.
6. STRUCTURE: Use the file names to build the 'Project Structure' section.

---

Project name: {project_name}

DOCUMENTED FACTS (extracted from docstrings report):
{context}

---

Write a README.md with these sections:
- Project overview
- Main features (based strictly on the descriptions above)
- Project structure (based on the file names above)
- Installation
- Usage
- Notes and limitations (if relevant)

Output only Markdown.
"""

    def _query_ollama(self, prompt: str) -> str:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def run(self, html_report_path: str, output_path: str = "README.md"):
        """
        Point d'entrée principal.

        Paramètres
        ----------
        html_report_path : str
            Chemin vers docstrings_report.html (n'importe quel dossier).
            Exemple Windows : r"C:\\Users\\User\\Downloads\\CodePilot_Result\\docstrings_report.html"
            Exemple Mac/Linux : "/home/user/downloads/docstrings_report.html"
        output_path : str
            Chemin de sortie du README. Par défaut "README.md" (dossier courant).
        """
        # 1. Parser le rapport HTML — source de vérité unique
        parser = HtmlReportParser(html_report_path)

        try:
            data = parser.parse()
            context = parser.build_context_block()
            project_name = data["project_name"]
        except FileNotFoundError as e:
            print(f"[ERREUR] {e}")
            return

        # 2. Construire le prompt à partir des faits réels
        prompt = self._build_prompt(context, project_name)

        # 3. Générer le README via Ollama
        try:
            readme = self._query_ollama(prompt)
        except Exception as e:
            readme = (
                f"# {project_name}\n\n"
                f"README generation failed.\n\nError: {e}\n"
            )

        # 4. Sauvegarder
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme)

        print(f"README.md generated at: {output_path}")


# ---------------------------------------------------------------------------
# Exemple d'utilisation
# ---------------------------------------------------------------------------
# if __name__ == "__main__":
#     generator = ReadmeGenerator(model="codellama")
#     generator.run(
#         html_report_path=r"C:\Users\User\Downloads\CodePilot_Result\docstrings_report.html",
#         output_path="README.md"
#     )
