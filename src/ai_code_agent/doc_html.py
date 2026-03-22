import ast
import os
import html
import datetime
from typing import List, Dict


class DocItem:
    """Small container for doc info about one object."""

    def __init__(self, kind: str, name: str, filepath: str, lineno: int, docstring: str):
        self.kind = kind        # "module", "function", "class"
        self.name = name
        self.filepath = filepath
        self.lineno = lineno
        self.docstring = docstring or ""


class HTMLDocFromDocstrings:
    """
    Generate a modern HTML documentation page
    based only on docstrings present in the code.
    """

    def __init__(self, title: str = "AI Code Agent – Docstrings Overview"):
        self.title = title

    def run(self, path: str, output_path: str = "docstrings_report.html"):
        items: List[DocItem] = []

        if os.path.isfile(path) and path.endswith(".py"):
            items.extend(self._extract_from_file(path))
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    if f.endswith(".py"):
                        full = os.path.join(root, f)
                        items.extend(self._extract_from_file(full))
        else:
            print(f"[doc-html] Invalid path: {path}")
            return

        html_text = self._build_html(items)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)

        print(f"[doc-html] HTML docstrings report written to: {output_path}")

    # Extraction 
    def _extract_from_file(self, filepath: str) -> List[DocItem]:
        print(f"[doc-html] Scanning {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            print(f"[doc-html] Cannot read {filepath}: {e}")
            return []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            print(f"[doc-html] Syntax error in {filepath}: {e}")
            return []

        items: List[DocItem] = []

        # Module-level docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            items.append(
                DocItem(
                    kind="module",
                    name=os.path.basename(filepath),
                    filepath=filepath,
                    lineno=1,
                    docstring=module_doc,
                )
            )

        # Functions / classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    items.append(
                        DocItem(
                            kind="function",
                            name=node.name,
                            filepath=filepath,
                            lineno=node.lineno,
                            docstring=doc,
                        )
                    )
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                if doc:
                    items.append(
                        DocItem(
                            kind="class",
                            name=node.name,
                            filepath=filepath,
                            lineno=node.lineno,
                            docstring=doc,
                        )
                    )

        return items

    # HTML generation 
    def _build_html(self, items: List[DocItem]) -> str:
        def esc(x) -> str:
            # Use stdlib html.escape for correctness
            return html.escape("" if x is None else str(x))

        # Group items by file
        items_by_file: Dict[str, List[DocItem]] = {}
        for it in items:
            items_by_file.setdefault(it.filepath, []).append(it)

        generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_items = len(items)
        total_files = len(items_by_file)

        out: List[str] = []

        out.append(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(self.title)}</title>

<style>
  :root {{
    --bg0:#0b1020; --bg1:#070a12;
    --card:rgba(255,255,255,.06); --card2:rgba(255,255,255,.09);
    --stroke:rgba(255,255,255,.12);
    --text:rgba(255,255,255,.92);
    --muted:rgba(255,255,255,.62);
    --shadow:0 14px 44px rgba(0,0,0,.45);
    --radius:18px;

    --module:#38bdf8;
    --class:#22c55e;
    --function:#a78bfa;

    --mono:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    --sans:ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
  }}

  @media (prefers-color-scheme: light) {{
    :root {{
      --bg0:#f5f7ff; --bg1:#eef2ff;
      --card:rgba(0,0,0,.03); --card2:rgba(0,0,0,.05);
      --stroke:rgba(0,0,0,.10);
      --text:rgba(10,15,25,.92);
      --muted:rgba(10,15,25,.55);
      --shadow:0 14px 44px rgba(10,15,25,.12);
    }}
  }}

  *{{box-sizing:border-box}}
  body{{
    margin:0; font-family:var(--sans); color:var(--text);
    background:
      radial-gradient(900px 600px at 15% -10%, rgba(124,58,237,.25), transparent 60%),
      radial-gradient(800px 600px at 110% 20%, rgba(34,197,94,.18), transparent 55%),
      linear-gradient(180deg,var(--bg0),var(--bg1));
  }}

  .wrap{{max-width:1100px;margin:0 auto;padding:22px 16px 40px}}

  .header{{
    border:1px solid var(--stroke);
    background:linear-gradient(180deg,var(--card2),var(--card));
    border-radius:var(--radius);
    box-shadow:var(--shadow);
    padding:18px;
  }}

  .title b{{font-size:20px}}
  .title span{{color:var(--muted);font-size:13px}}

  .meta{{margin-top:10px;display:flex;gap:10px;flex-wrap:wrap}}
  .pill{{
    font-size:12px;color:var(--muted);
    border:1px solid var(--stroke);
    padding:6px 10px;border-radius:999px;
    background:rgba(255,255,255,.04);
  }}

  .files{{margin-top:18px;display:grid;gap:14px}}

  details.file{{
    border:1px solid var(--stroke);
    background:linear-gradient(180deg,var(--card2),var(--card));
    border-radius:16px;
    overflow:hidden;
    box-shadow:0 10px 28px rgba(0,0,0,.22);
  }}

  summary.file__summary{{
    list-style:none;cursor:pointer;
    padding:14px;
    display:flex;justify-content:space-between;gap:12px;align-items:center;
  }}
  summary::-webkit-details-marker{{display:none}}

  .file__name{{font-weight:900}}
  .file__path{{font-size:12px;color:var(--muted);text-align:right;max-width:65%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}

  .items{{padding:0 14px 14px;display:grid;gap:12px}}

  .doc{{
    border:1px solid var(--stroke);
    border-radius:14px;
    padding:12px;
    background:rgba(255,255,255,.04);
  }}
  @media (prefers-color-scheme: light) {{
    .doc{{background:rgba(0,0,0,.02)}}
  }}

  .doc__head{{display:flex;justify-content:space-between;align-items:center;gap:10px}}
  .doc__title{{font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .badge{{font-size:12px;padding:4px 10px;border-radius:999px;border:1px solid;font-weight:800}}
  .badge.module{{color:var(--module);border-color:rgba(56,189,248,.55);background:rgba(56,189,248,.10)}}
  .badge.class{{color:var(--class);border-color:rgba(34,197,94,.55);background:rgba(34,197,94,.10)}}
  .badge.function{{color:var(--function);border-color:rgba(167,139,250,.55);background:rgba(167,139,250,.10)}}

  .doc__meta{{color:var(--muted);font-size:12px;margin-top:4px}}

  pre{{
    margin:10px 0 0;
    background:rgba(0,0,0,.25);
    padding:12px;border-radius:12px;
    overflow:auto;
    font-family:var(--mono);
    font-size:12.5px;
    line-height:1.45;
    white-space:pre-wrap;
    word-break:break-word;
    border:1px solid rgba(255,255,255,.10);
  }}
  @media (prefers-color-scheme: light) {{
    pre{{background:rgba(0,0,0,.05);border-color:rgba(0,0,0,.08)}}
  }}

  .empty{{
    margin-top:14px;
    padding:14px;
    border:1px dashed var(--stroke);
    border-radius:16px;
    color:var(--muted);
  }}

  .footer{{
    margin-top:14px;
    color:var(--muted);
    font-size:12px;
    display:flex;
    justify-content:space-between;
    gap:12px;
    flex-wrap:wrap;
  }}
</style>
</head>

<body>
<div class="wrap">

  <div class="header">
    <div class="title">
      <b>{esc(self.title)}</b><br/>
      <span>Docstrings extracted from source code</span>
    </div>
    <div class="meta">
      <span class="pill">Generated: {esc(generated)}</span>
      <span class="pill">Files: {total_files}</span>
      <span class="pill">Docstrings: {total_items}</span>
    </div>
  </div>

  <div class="files">
""")

        if not items_by_file:
            out.append('<div class="empty"><b>No docstrings found.</b> Add module/class/function docstrings to see them here.</div>')
        else:
            for filepath, file_items in sorted(items_by_file.items()):
                file_items_sorted = sorted(file_items, key=lambda x: x.lineno)
                out.append(f"""
    <details class="file" open>
      <summary class="file__summary">
        <div class="file__name">{esc(os.path.basename(filepath))}</div>
        <div class="file__path">{esc(filepath)}</div>
      </summary>

      <div class="items">
""")
                for it in file_items_sorted:
                    title = esc(it.name) if it.kind != "module" else "Module docstring"
                    out.append(f"""
        <div class="doc">
          <div class="doc__head">
            <div class="doc__title">{title}</div>
            <span class="badge {esc(it.kind)}">{esc(it.kind)}</span>
          </div>
          <div class="doc__meta">Line {it.lineno}</div>
          <pre>{esc(it.docstring)}</pre>
        </div>
""")
                out.append("""
      </div>
    </details>
""")

        out.append("""
  </div>

  <div class="footer">
    <span>Generated by HTMLDocFromDocstrings</span>
    <span>Tip: Add docstrings to improve readability and documentation quality.</span>
  </div>

</div>
</body>
</html>
""")

        return "\n".join(out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m ai_code_agent.doc_html <path_to_file_or_folder> [output.html]")
        sys.exit(1)

    path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) >= 3 else "docstrings_report.html"

    generator = HTMLDocFromDocstrings()
    generator.run(path, output_path=output)
