# AI Code Agent – Python Static Analysis & Optimization Suite

AI Code Agent is a fully local, secure toolkit to analyze, optimize, and report on Python codebases.  

---

# Main Capabilities

# 1. Static Code Analysis — `analyze`

The `CodeAnalyzer` module performs a structural analysis of Python files or directories:

- AST-based syntax inspection  
- Cyclomatic complexity estimation  
- Detection of deep nesting (complex conditional logic)  
- Missing docstrings (functions / classes)  
- Light PEP8 checks:
  - line length
  - tabs vs spaces
  - space after comma
  - trailing whitespace  
- Simple import cycle detection  
- Simple duplicate code detection

Results are printed as a clear console report and can also be consumed by the reporting module.

---

# 2. Code Optimization — `optimize`

The `CodeOptimizer` module performs safe, conservative cleanups while preserving behavior:

- Remove unused simple imports (`import x` when `x` is never used)  
- Keep star imports and `from x import y` (to avoid breaking code)  
- Remove simple unused assignments like `x = 1` (excluding variables starting with `_`)  
- Normalize indentation (tabs → 4 spaces)  
- Remove trailing spaces  
- Collapse excessive blank lines  
- Deduplicate import lines  
- Optionally write changes:
  - to a new file `*_optimized.py`, or  
  - directly in place via `--inplace`

---

# 3. Reporting — `report`

The `HTMLReporter` module generates an HTML report from analyzer results:

- High-level natural language summary of the project  
- Counts and lists of:
  - errors
  - warnings
  - missing docstrings
  - PEP8 issues
  - import cycles
  - duplicate code  
- Rendered as a readable HTML dashboard, ready to be attached to audits or internal reviews.


# Installation & Setup

# 1. Unzip the project

Extract the archive anywhere on your machine

# 2. Open a terminal in the project folder

cd ai-code-agent

# 3. Create and activate a virtual environment

python3 -m venv venv

# macOS / Linux
source venv/bin/activate
# windows
.\venv\Scripts\Activate

# 4. Install the project in editable mode

pip install -e .

# 5. CLI Usage

Analyze the project source itself:
- code-agent analyze src/ai_code_agent/test_demo.py

Optimize a module and write changes in other document:
- code-agent optimize src/ai_code_agent/test_demo.py

Generate an HTML report for a folder:
- code-agent report-html src/ai_code_agent
