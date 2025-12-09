import datetime


class LocalReport:

    def build_summary(self, results: dict) -> str:
        files = len(results.get("files", []))
        errors = len(results.get("errors", []))
        warnings = len(results.get("warnings", []))
        missing_docs = len(results.get("missing_docstrings", []))
        pep8 = len(results.get("pep8", []))
        cycles = len(results.get("import_cycles", []))
        duplicates = len(results.get("duplicates", []))

        lines = []
        lines.append(f"This project contains {files} analyzed Python file(s).")

        if errors:
            lines.append(f"There are {errors} error(s) that should be fixed first.")
        else:
            lines.append("No critical syntax errors were detected.")

        if warnings:
            lines.append(f"The analyzer reported {warnings} warning(s) about code structure or complexity.")
        if missing_docs:
            lines.append(f"There are {missing_docs} element(s) without docstrings (functions or classes).")
        if pep8:
            lines.append(f"{pep8} PEP8 style issue(s) were found (spacing, line length, tabs, etc.).")
        if cycles:
            lines.append(f"{cycles} potential import cycle(s) were detected.")
        if duplicates:
            lines.append(f"{duplicates} possible code duplication(s) were identified.")

        # Suggestions simples
        suggestions = []
        if missing_docs:
            suggestions.append("Add docstrings to undocumented functions and classes.")
        if pep8:
            suggestions.append("Apply a code formatter or fix basic PEP8 issues.")
        if warnings:
            suggestions.append("Reduce nesting and complexity where the analyzer reported warnings.")
        if cycles:
            suggestions.append("Break import cycles by restructuring modules.")

        if suggestions:
            lines.append("Main improvement suggestions:")
            for s in suggestions:
                lines.append(f"- {s}")

        return " ".join(lines)


class HTMLReporter:
    """
    Generates an HTML report from CodeAnalyzer results
    and a summary produced by the LocalReport class.
    """

    def __init__(self, title: str = "AI Code Agent Report"):
        self.title = title
        self.ai = LocalReport()

    def build_html(self, results: dict) -> str:
        summary = self.ai.build_summary(results)

        html = []
        html.append("<html><head>")
        html.append(f"<title>{self.title}</title>")
        html.append("<meta charset='utf-8'/>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; padding: 20px; }")
        html.append("h1 { color: #004c97; }")
        html.append("h2 { color: #0077cc; margin-top: 24px; }")
        html.append("ul { margin-left: 20px; }")
        html.append("li { margin-bottom: 4px; }")
        html.append("p { line-height: 1.4; }")
        html.append("</style>")
        html.append("</head><body>")

        html.append(f"<h1>{self.title}</h1>")
        html.append(f"<p>Generated on {datetime.datetime.now()}</p>")

        html.append("<h2>Summary</h2>")
        html.append(f"<p>{summary}</p>")

        # Detailed sections
        def add_section(title, key):
            items = results.get(key, [])
            html.append(f"<h2>{title}</h2>")
            if not items:
                html.append("<p>No items.</p>")
                return
            html.append("<ul>")
            for item in items:
                html.append(f"<li>{item}</li>")
            html.append("</ul>")

        add_section("Errors", "errors")
        add_section("Warnings", "warnings")
        add_section("Missing docstrings", "missing_docstrings")
        add_section("PEP8 issues", "pep8")
        add_section("Import cycles", "import_cycles")
        add_section("Duplicate code", "duplicates")

        html.append("</body></html>")
        return "\n".join(html)

    def save(self, results: dict, output_path: str = "analysis_report.html"):
        html = self.build_html(results)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML report written to: {output_path}")
