import os
import shutil
from pathlib import Path
from datetime import datetime

from .optimizer import CodeOptimizer
from .analyzer import CodeAnalyzer
from .reporter import HTMLReporter
from .doc_ai import AIDocstringGenerator
from .doc_html import HTMLDocFromDocstrings
from .readme_generator import ReadmeGenerator
from .requirements_generator import RequirementsGenerator


class AllInOneRunner:
    def __init__(self, path: str):
        self.path = Path(path)

    def _copy_source_to_output(self, output_dir: Path) -> Path:
        """
        Copy uploaded source into a working directory inside output_dir.
        Returns the copied target path.
        """
        source_copy_root = output_dir / "source"

        if self.path.is_file():
            source_copy_root.mkdir(parents=True, exist_ok=True)
            dst = source_copy_root / self.path.name
            shutil.copy2(self.path, dst)
            return dst

        elif self.path.is_dir():
            if source_copy_root.exists():
                shutil.rmtree(source_copy_root)
            shutil.copytree(self.path, source_copy_root)
            return source_copy_root

        raise ValueError(f"Invalid path: {self.path}")

    def run(self, output_dir: str):
        output_dir = os.path.expanduser(output_dir)

        if not output_dir or output_dir == "all_output":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.expanduser(f"~/Downloads/CodePilot_Result_{timestamp}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print("(All) Starting full pipeline")
        print("=" * 60)

        # 1) Copy input into output folder so everything stays together
        working_target = self._copy_source_to_output(output_dir)
        print(f"(All) Working copy created: {working_target}")

        # 2) Add docstrings with AI
        print("\n(1/6) Generate AI docstrings")
        docgen = AIDocstringGenerator(str(working_target), inplace=True, language="en")
        docgen.run()

        # 3) Optimize
        print("\n(2/6) Optimize")
        optimizer = CodeOptimizer(str(working_target), inplace=False)
        optimizer.run()

        # 4) Generate HTML from docstrings
        print("\n(3/6) Generate docstrings HTML")
        doc_html_output = output_dir / "docstrings_report.html"
        doc_html = HTMLDocFromDocstrings()
        doc_html.run(str(working_target), output_path=str(doc_html_output))

        # 5) Run analyzer and create analysis HTML
        print("\n(4/6) Generate analysis HTML")
        analyzer = CodeAnalyzer(str(working_target))
        analyzer.run()
        report_output = output_dir / "analysis_report.html"
        reporter = HTMLReporter("AI Code Agent – Full Report")
        reporter.save(analyzer.results, str(report_output))

        # 6) Generate README
        print("\n(5/6) Generate README")
        readme_output = output_dir / "README.md"
        readme = ReadmeGenerator(str(working_target))
        readme.run(str(readme_output))

        # 7) Generate requirements
        print("\n(6/6) Generate requirements")
        req_output = output_dir / "requirements.txt"
        req = RequirementsGenerator(str(working_target))
        req.run(str(req_output))

        print("\n" + "=" * 60)
        print("(All) Done!")
        print(f"(All) Output folder: {output_dir}")

        # 8) Restore pure original files for the "Before/After" comparison
        print("\n(7/7) Restoring raw unoptimized files...")
        if self.path.is_file():
            import shutil
            shutil.copy2(self.path, working_target)
        elif self.path.is_dir():
            import shutil
            for py_file in self.path.rglob("*.py"):
                rel_path = py_file.relative_to(self.path)
                shutil.copy2(py_file, working_target / rel_path)