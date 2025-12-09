import os
import sys

BASE_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from ai_code_agent.analyzer import CodeAnalyzer
from ai_code_agent.reporter import HTMLReporter

def main():
    # 1) Run the analysis on the entire package
    analyzer = CodeAnalyzer(os.path.join(SRC_DIR, "ai_code_agent"))
    analyzer.run()

    # 2) Generate the HTML report
    output_path = os.path.join(BASE_DIR, "analysis_report.html")
    reporter = HTMLReporter("AI Code Agent – Report")
    reporter.save(analyzer.results, output_path)


if __name__ == "__main__":
    main()
