import datetime


class LocalReport:
    """
    Résumé texte pour le Professional Analyzer.
    On s'appuie sur:
      - files
      - flake8_issues
      - pylint_issues
      - complexity
      - unused_code
      - summary (optionnel)
    """

    def build_summary(self, results: dict) -> str:
        files = len(results.get("files", []))
        flake8 = len(results.get("flake8_issues", []))
        pylint = len(results.get("pylint_issues", []))
        unused = len(results.get("unused_code", []))

        # Complexity: dict {filepath: {total, functions, details}}
        complexity = results.get("complexity", {}) or {}
        complexity_files = len(complexity)

        # Score (si ton analyzer l’a déjà calculé)
        health_score = ""
        avg_complexity = ""
        summary = results.get("summary", {}) or {}
        if summary:
            health_score = summary.get("health_score", "")
            avg_complexity = summary.get("average_complexity", "")

        lines = []
        lines.append(f"This project contains {files} analyzed Python file(s).")

        if flake8:
            lines.append(f"Flake8 found {flake8} PEP8/style issue(s).")
        else:
            lines.append("Flake8 found no PEP8/style issues.")

        if pylint:
            lines.append(f"Pylint reported {pylint} code quality issue(s).")
        else:
            lines.append("Pylint reported no code quality issues.")

        if unused:
            lines.append(f"{unused} file(s) contain unused imports or variables (Autoflake).")
        else:
            lines.append("No unused imports/variables were detected by Autoflake.")

        if complexity_files:
            lines.append(f"Radon analyzed complexity for {complexity_files} file(s).")
        else:
            lines.append("No complexity data available (Radon).")

        if health_score:
            lines.append(f"Overall health score: {health_score}.")
        if avg_complexity != "":
            lines.append(f"Average complexity: {avg_complexity}.")

        # Suggestions simples
        suggestions = []
        if flake8:
            suggestions.append("Fix Flake8 issues (formatting, line length, imports).")
        if pylint:
            suggestions.append("Fix Pylint issues (naming, structure, potential bugs).")
        if unused:
            suggestions.append("Remove unused imports/variables.")
        if complexity_files:
            # si tu veux: suggestion si complexité moyenne > seuil
            try:
                ac = float(avg_complexity) if avg_complexity != "" else 0.0
            except Exception:
                ac = 0.0
            if ac >= 10:
                suggestions.append("Reduce complexity in high-complexity functions (split logic).")

        if suggestions:
            lines.append("Main improvement suggestions:")
            for s in suggestions:
                lines.append(f"- {s}")

        return " ".join(lines)


class HTMLReporter:
    """
    HTML report pour le Professional Analyzer.
    """

    def __init__(self, title: str = "AI Code Agent Report"):
        self.title = title
        self.ai = LocalReport()

    def build_html(self, results: dict) -> str:
        summary_text = self.ai.build_summary(results)

        files = len(results.get("files", []))
        flake8 = len(results.get("flake8_issues", []))
        pylint = len(results.get("pylint_issues", []))
        unused = len(results.get("unused_code", []))
        complexity_files = len((results.get("complexity", {}) or {}))

        generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def esc(x):
            if x is None:
                return ""
            s = str(x)
            return (
                s.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace('"', "&quot;")
                 .replace("'", "&#39;")
            )

        def badge_class(n, kind):
            if kind == "error":
                return "badge badge--error" if n else "badge badge--ok"
            if kind == "warn":
                return "badge badge--warn" if n else "badge badge--ok"
            return "badge badge--info"

        def section(title, items, kind="info", empty_text="No items."):
            n = len(items)
            bcls = badge_class(n, "error" if kind == "error" else ("warn" if kind == "warn" else "info"))
            html = []
            html.append(f"""
<details class="section" open>
  <summary class="section__summary">
    <div class="section__left">
      <span class="section__title">{esc(title)}</span>
      <span class="{bcls}">{n}</span>
    </div>
    <span class="section__hint">Click to collapse</span>
  </summary>
  <div class="section__body">
""")
            if not items:
                html.append(f'<p class="muted">{esc(empty_text)}</p>')
            else:
                html.append('<ul class="list">')
                for item in items:
                    html.append(f'<li class="list__item"><code class="code">{esc(item)}</code></li>')
                html.append("</ul>")
            html.append("  </div>\n</details>")
            return "\n".join(html)

        # Convert issues dicts -> strings for display
        flake8_items = []
        for it in results.get("flake8_issues", []):
            flake8_items.append(f'{it.get("file")}:{it.get("line")} {it.get("code")} {it.get("message")}')

        pylint_items = []
        for it in results.get("pylint_issues", []):
            pylint_items.append(f'{it.get("file")}:{it.get("line")} {it.get("type")} {it.get("symbol")} {it.get("message")}')

        unused_items = []
        for it in results.get("unused_code", []):
            # it may contain details/diff
            unused_items.append(f'{it.get("file")}: {it.get("message")}')

        complexity_items = []
        complexity = results.get("complexity", {}) or {}
        for fp, data in sorted(complexity.items()):
            complexity_items.append(f"{fp}: total={data.get('total')} functions={data.get('functions')}")

        html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(self.title)}</title>
<style>
  :root {{
    --bg0: #0b1020;
    --bg1: #070a12;
    --card: rgba(255,255,255,0.06);
    --card2: rgba(255,255,255,0.09);
    --stroke: rgba(255,255,255,0.12);
    --text: rgba(255,255,255,0.92);
    --muted: rgba(255,255,255,0.64);
    --muted2: rgba(255,255,255,0.48);
    --shadow: 0 14px 44px rgba(0,0,0,0.45);
    --radius: 18px;

    --ok: #22c55e;
    --warn: #f59e0b;
    --err: #ef4444;

    --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
  }}

  @media (prefers-color-scheme: light) {{
    :root {{
      --bg0: #f5f7ff;
      --bg1: #eef2ff;
      --card: rgba(0,0,0,0.03);
      --card2: rgba(0,0,0,0.04);
      --stroke: rgba(0,0,0,0.10);
      --text: rgba(10,15,25,0.92);
      --muted: rgba(10,15,25,0.62);
      --muted2: rgba(10,15,25,0.48);
      --shadow: 0 14px 44px rgba(10,15,25,0.12);
    }}
  }}

  * {{ box-sizing: border-box; }}
  html, body {{ height: 100%; }}
  body {{
    margin: 0;
    font-family: var(--sans);
    color: var(--text);
    background:
      radial-gradient(1000px 600px at 15% -10%, rgba(124,58,237,0.30), transparent 60%),
      radial-gradient(900px 600px at 110% 20%, rgba(34,197,94,0.18), transparent 55%),
      radial-gradient(900px 700px at 50% 120%, rgba(56,189,248,0.16), transparent 60%),
      linear-gradient(180deg, var(--bg0), var(--bg1));
  }}

  .wrap {{
    max-width: 1120px;
    margin: 0 auto;
    padding: 22px 16px 40px;
  }}

  .header {{
    border: 1px solid var(--stroke);
    background: linear-gradient(180deg, var(--card2), var(--card));
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
  }}

  .header__top {{
    padding: 18px 18px 14px;
    display: flex;
    gap: 14px;
    align-items: center;
    justify-content: space-between;
  }}

  .brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 220px;
  }}

  .logo {{
    width: 38px;
    height: 38px;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(124,58,237,0.95), rgba(56,189,248,0.75));
    box-shadow: 0 14px 36px rgba(124,58,237,0.24);
    position: relative;
    border: 1px solid rgba(255,255,255,0.14);
  }}
  .logo:after {{
    content: "";
    position: absolute;
    inset: 1px;
    border-radius: 13px;
    background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.35), transparent 55%);
  }}

  .title {{
    display: flex;
    flex-direction: column;
    line-height: 1.1;
  }}
  .title b {{ font-size: 16px; letter-spacing: 0.2px; }}
  .title span {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}

  .meta {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
    align-items: center;
  }}
  .pill {{
    font-size: 12px;
    color: var(--muted);
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.05);
    padding: 8px 10px;
    border-radius: 999px;
  }}

  .content {{
    padding: 0 18px 18px;
  }}

  .grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-top: 8px;
  }}
  @media (max-width: 920px) {{
    .grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}

  .kpi {{
    border: 1px solid var(--stroke);
    background: linear-gradient(180deg, var(--card2), var(--card));
    border-radius: 16px;
    padding: 12px 12px;
  }}
  .kpi__label {{
    color: var(--muted);
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    gap: 10px;
    align-items: center;
  }}
  .kpi__value {{
    margin-top: 8px;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 0.2px;
  }}

  .card {{
    margin-top: 14px;
    border: 1px solid var(--stroke);
    background: linear-gradient(180deg, var(--card2), var(--card));
    border-radius: var(--radius);
    padding: 14px 14px;
    box-shadow: var(--shadow);
  }}

  .card h2 {{
    margin: 0 0 8px;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.35px;
    color: var(--muted);
  }}

  .summary {{
    line-height: 1.55;
    font-size: 14px;
  }}

  details.section {{
    margin-top: 12px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.04);
    border-radius: 16px;
    overflow: hidden;
  }}
  summary.section__summary {{
    list-style: none;
    cursor: pointer;
    padding: 12px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }}
  summary.section__summary::-webkit-details-marker {{ display: none; }}

  .section__left {{
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }}
  .section__title {{
    font-weight: 900;
    font-size: 14px;
  }}
  .section__hint {{ color: var(--muted2); font-size: 12px; }}
  .section__body {{ padding: 0 12px 12px; }}

  .badge {{
    font-size: 12px;
    padding: 5px 10px;
    border-radius: 999px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.05);
    color: var(--muted);
    font-weight: 900;
  }}
  .badge--ok {{ color: rgba(34,197,94,0.95); border-color: rgba(34,197,94,0.30); background: rgba(34,197,94,0.10); }}
  .badge--warn {{ color: rgba(245,158,11,0.95); border-color: rgba(245,158,11,0.30); background: rgba(245,158,11,0.10); }}
  .badge--error {{ color: rgba(239,68,68,0.95); border-color: rgba(239,68,68,0.30); background: rgba(239,68,68,0.10); }}
  .badge--info {{ color: rgba(56,189,248,0.95); border-color: rgba(56,189,248,0.30); background: rgba(56,189,248,0.10); }}

  .list {{
    margin: 10px 0 0;
    padding: 0;
    list-style: none;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--stroke);
  }}
  .list__item {{
    padding: 10px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.10);
  }}
  .list__item:nth-child(2n) {{ background: rgba(255,255,255,0.04); }}
  .list__item:last-child {{ border-bottom: none; }}

  .code {{
    font-family: var(--mono);
    font-size: 12.5px;
    color: var(--text);
  }}
  .muted {{ color: var(--muted); }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="header__top">
        <div class="brand">
          <div class="logo" aria-hidden="true"></div>
          <div class="title">
            <b>{esc(self.title)}</b>
            <span>Professional analysis report</span>
          </div>
        </div>
        <div class="meta">
          <span class="pill">Generated: {esc(generated)}</span>
          <span class="pill">Files: {files}</span>
        </div>
      </div>

      <div class="content">
        <div class="grid">
          <div class="kpi"><div class="kpi__label"><span>Flake8</span><span class="{badge_class(flake8,'warn')}">{flake8}</span></div><div class="kpi__value">{flake8}</div></div>
          <div class="kpi"><div class="kpi__label"><span>Pylint</span><span class="{badge_class(pylint,'warn')}">{pylint}</span></div><div class="kpi__value">{pylint}</div></div>
          <div class="kpi"><div class="kpi__label"><span>Unused code</span><span class="{badge_class(unused,'warn')}">{unused}</span></div><div class="kpi__value">{unused}</div></div>
          <div class="kpi"><div class="kpi__label"><span>Complexity files</span><span class="{badge_class(complexity_files,'info')}">{complexity_files}</span></div><div class="kpi__value">{complexity_files}</div></div>
          <div class="kpi"><div class="kpi__label"><span>Total files</span><span class="{badge_class(files,'info')}">{files}</span></div><div class="kpi__value">{files}</div></div>
        </div>

        <div class="card">
          <h2>Summary</h2>
          <div class="summary">{esc(summary_text)}</div>
        </div>

        {section("Flake8 issues", flake8_items, kind="warn")}
        {section("Pylint issues", pylint_items, kind="warn")}
        {section("Unused code (Autoflake)", unused_items, kind="warn")}
        {section("Complexity (Radon)", complexity_items, kind="info")}

      </div>
    </div>
  </div>
</body>
</html>
"""
        return html

    def save(self, results: dict, output_path: str = "analysis_report.html"):
        html = self.build_html(results)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML report written to: {output_path}")
