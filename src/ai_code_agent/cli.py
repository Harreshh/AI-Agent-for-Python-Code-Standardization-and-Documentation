import argparse

from .analyzer import CodeAnalyzer
from .optimizer import CodeOptimizer
from .reporter import HTMLReporter
from .doc_ai import AIDocstringGenerator
from .doc_html import HTMLDocFromDocstrings


def main():
    parser = argparse.ArgumentParser(
        prog="code-agent",
        description="Local AI agent for analyzing, optimizing, documenting and reporting on Python projects."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze
    analyze = subparsers.add_parser("analyze", help="Analyze Python code quality & structure.")
    analyze.add_argument("path", help="Path to a .py file or a folder containing Python files.")
    analyze.add_argument(
        "--output", "-o",
        default="professional_audit.json",
        help="Output JSON audit file (default: professional_audit.json)."
    )

    # optimize
    optimize = subparsers.add_parser("optimize", help="Optimize Python code (imports, unused vars, formatting).")
    optimize.add_argument("path", help="Path to a .py file or a folder containing Python files.")
    optimize.add_argument("--inplace", action="store_true", help="Modify files in place.")
    optimize.add_argument(
        "--audit",
        default="professional_audit.json",
        help="Audit JSON file to use (default: professional_audit.json)."
    )

    readme = subparsers.add_parser(
        "readme",
        help="Generate a README.md file from a Python file or folder."
    )
    readme.add_argument("path", help="Path to a .py file or folder.")
    readme.add_argument(
        "--output",
        "-o",
        default="README.md",
        help="Output README path."
    )

    requirements = subparsers.add_parser(
        "requirements",
        help="Generate a requirements.txt file from a Python file or folder."
    )
    requirements.add_argument("path", help="Path to a .py file or folder.")
    requirements.add_argument(
        "--output",
        "-o",
        default="requirements.txt",
        help="Output requirements file path."
    )

    # report-html
    report = subparsers.add_parser("report-html", help="Run analyzer and generate a HTML report.")
    report.add_argument("path", help="Path to a .py file or a folder containing Python files.")
    report.add_argument("--output", "-o", default="analysis_report.html",
                        help="Output HTML file path (default: analysis_report.html).")

    # doc-ai
    doc_ai = subparsers.add_parser("doc-ai", help="Generate docstrings using a local LLM (Ollama).")
    doc_ai.add_argument("path", help="Path to a .py file or folder.")
    doc_ai.add_argument("--inplace", action="store_true", help="Write changes directly into the file(s).")
    doc_ai.add_argument("--lang", default="en", help="Docstring language (default: en).")

    # doc-html
    doc_html = subparsers.add_parser("doc-html", help="Generate HTML from existing docstrings.")
    doc_html.add_argument("path", help="Path to a .py file or folder.")
    doc_html.add_argument("--output", "-o", default="docstrings_report.html", help="Output HTML file path.")

    all_cmd = subparsers.add_parser(
    "all",
    help="Run all actions: optimize, doc-ai, doc-html, report-html, readme, requirements."
    )
    all_cmd.add_argument("path", help="Path to a .py file or folder.")
    all_cmd.add_argument(
        "--output-dir",
        default="all_output",
        help="Output directory for all generated files."
    )

    args = parser.parse_args()

    # dispatch
    if args.command == "analyze":
        analyzer = CodeAnalyzer(args.path)
        analyzer.run()
        analyzer.export_results(args.output)

    elif args.command == "optimize":
        # Pipeline: analyzer first, then optimizer using the audit
        analyzer = CodeAnalyzer(args.path)
        analyzer.run()
        analyzer.export_results(args.audit)

        optimizer = CodeOptimizer(args.path, inplace=args.inplace)
        optimizer.run_with_audit(args.audit)

    elif args.command == "report-html":
        analyzer = CodeAnalyzer(args.path)
        analyzer.run()
        reporter = HTMLReporter("AI Code Agent – Report")
        reporter.save(analyzer.results, args.output)

    elif args.command == "doc-ai":
        generator = AIDocstringGenerator(args.path, inplace=args.inplace, language=args.lang)
        generator.run()

    elif args.command == "doc-html":
        generator = HTMLDocFromDocstrings()
        generator.run(args.path, output_path=args.output)
    elif args.command == "readme":
        from .readme_generator import ReadmeGenerator
        generator = ReadmeGenerator(args.path)
        generator.run(args.output)

    elif args.command == "requirements":
        from .requirements_generator import RequirementsGenerator
        generator = RequirementsGenerator(args.path)
        generator.run(args.output)
    elif args.command == "all":
        from .all_in_one import AllInOneRunner
        runner = AllInOneRunner(args.path)
        runner.run(args.output_dir)


if __name__ == "__main__":
    main()
