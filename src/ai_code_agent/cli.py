import argparse

from .analyzer import CodeAnalyzer
from .optimizer import CodeOptimizer
from .reporter import HTMLReporter


def main():
    parser = argparse.ArgumentParser(
        prog="code-agent",
        description="Local AI agent for analyzing, optimizing, documenting and reporting on Python projects."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze
    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze Python code quality & structure."
    )
    analyze.add_argument(
        "path",
        help="Path to a .py file or a folder containing Python files."
    )

    # optimize
    optimize = subparsers.add_parser(
        "optimize",
        help="Optimize Python code (imports, unused vars, formatting)."
    )
    optimize.add_argument(
        "path",
        help="Path to a .py file or a folder containing Python files."
    )
    optimize.add_argument(
        "--inplace",
        action="store_true",
        help="Modify files in place instead of creating *_optimized.py files."
    )


    # report-html
    report = subparsers.add_parser(
        "report-html",
        help="Run analyzer and generate a HTML report."
    )
    report.add_argument(
        "path",
        help="Path to a .py file or a folder containing Python files."
    )
    report.add_argument(
        "--output",
        "-o",
        default="analysis_report.html",
        help="Output HTML file path (default: analysis_report.html)."
    )

    args = parser.parse_args()

    # dispatch
    if args.command == "analyze":
        analyzer = CodeAnalyzer(args.path)
        analyzer.run()

    elif args.command == "optimize":
        optimizer = CodeOptimizer(args.path, inplace=args.inplace)
        optimizer.run()

    elif args.command == "report-html":
        analyzer = CodeAnalyzer(args.path)
        analyzer.run()
        reporter = HTMLReporter("AI Code Agent – Report")
        reporter.save(analyzer.results, args.output)


if __name__ == "__main__":
    main()
