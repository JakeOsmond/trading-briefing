#!/usr/bin/env python3
"""Generate the context manager HTML page.

Standalone script — no heavy dependencies (no openai, anthropic, bigquery).
Can be run independently by the deploy workflow without installing the
full pipeline requirements.

Usage: python3 scripts/generate-context-manager.py [output_path]
Default output: briefings/context-manager.html
"""
import sys
from pathlib import Path


def generate_context_manager_html():
    """Generate the context management page — view, remove, add AI-learned context."""
    project_root = Path(__file__).parent.parent
    context_dir = project_root / "context"
    tpl_dir = project_root / "templates"

    # Load context manager CSS
    css_path = tpl_dir / "context-manager.css"
    cm_css = css_path.read_text() if css_path.exists() else ""

    # Build category sections
    categories = [
        ("universal", "Universal (all domains)", False, "Foundational context shared across all domains. Managed by engineering."),
        ("insurance", "Insurance", True, "Insurance-specific context. AI-learned items can be removed."),
        ("operational", "Operational", True, "Operational context including market events and intelligence sources."),
    ]

    sections_html = ""
    for cat_key, cat_label, editable, cat_desc in categories:
        cat_path = context_dir / cat_key
        if not cat_path.exists():
            continue

        files_html = ""
        for md_file in sorted(cat_path.glob("*.md")):
            if md_file.name in ("index.md", "pending-context.md", "context-removals.json"):
                continue
            text = md_file.read_text()
            lines = text.strip().split("\n")
            title = lines[0].replace("#", "").strip() if lines else md_file.stem
            total_lines = len(lines)
            file_id = f"file-{cat_key}-{md_file.stem}"

            # Escape full content for preview popup
            preview_content = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Find AI-added items (lines with "— Source:" attribution)
            ai_items = [l.strip() for l in lines if "— Source:" in l and l.strip().startswith("-")]

            items_html = ""
            if ai_items and editable:
                for ai_idx, ai_line in enumerate(ai_items):
                    clean = ai_line.lstrip("- ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    file_rel = f"{cat_key}/{md_file.name}"
                    escaped_text = ai_line.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "")
                    item_id = f"cm-{cat_key}-{md_file.stem}-{ai_idx}"
                    items_html += (
                        f'<div class="cm-ai-item" id="{item_id}">'
                        f'<span class="cm-ai-text">{clean}</span>'
                        f'<button class="cm-remove-btn" onclick="cmRemove(\'{file_rel}\',\'{escaped_text}\',\'{item_id}\')">'
                        f'✕ Remove</button>'
                        f'</div>\n'
                    )
            elif ai_items:
                for ai_line in ai_items:
                    clean = ai_line.lstrip("- ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    items_html += f'<div class="cm-ai-item"><span class="cm-ai-text">{clean}</span></div>\n'

            ai_count = f' <span class="cm-ai-count">{len(ai_items)} AI-learned</span>' if ai_items else ""

            files_html += (
                f'<div class="cm-file">'
                f'<div class="cm-file-header cm-file-clickable" onclick="cmPreview(\'{file_id}\')">'
                f'<span class="cm-file-icon">📄</span> '
                f'<span class="cm-file-name">{md_file.name}</span>'
                f'<span class="cm-file-meta">{total_lines} lines{ai_count}</span>'
                f'</div>\n'
                f'<div class="cm-file-title">{title}</div>\n'
                f'{items_html}'
                f'<div class="cm-file-preview" id="{file_id}" style="display:none">'
                f'<pre class="cm-preview-content">{preview_content}</pre>'
                f'</div>\n'
                f'</div>\n'
            )

        edit_note = "" if editable else ' <span class="cm-readonly">(read-only)</span>'
        sections_html += (
            f'<div class="cm-category">'
            f'<h2 class="cm-cat-header">{cat_label}{edit_note}</h2>'
            f'<p class="cm-cat-desc">{cat_desc}</p>'
            f'{files_html}'
            f'</div>\n'
        )

    # Load JS template
    js_path = tpl_dir / "context-manager.js"
    if js_path.exists():
        cm_js = js_path.read_text()
    else:
        cm_js = "/* context-manager.js not found */"

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Context Manager — Trading Covered</title>
<link rel="icon" type="image/png" href="https://dmy0b9oeprz0f.cloudfront.net/holidayextras.co.uk/brand-guidelines/logo-tags/png/better-future.png">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{cm_css}</style>
</head><body>
<div class="cm-container">

<div class="cm-warning">
⚠ Context shown here is used by Trading Covered to understand the business. Changes affect all future briefings.
</div>

<div class="cm-header">
<h1>Context Manager</h1>
<p class="cm-subtitle">AI-learned context from Google Drive, meetings, and manual entries</p>
<a href="latest.html" class="cm-back-link">← Back to briefing</a>
</div>

{sections_html}

<div class="cm-add-section">
<h2>➕ Add Context</h2>
<p class="cm-add-desc">Add something you know that the AI should learn. It will be reformatted and categorised automatically.</p>
<div class="cm-add-form">
<textarea id="cmAddText" class="cm-add-input" rows="3" placeholder="e.g. We just signed On the Beach as a partner, worth about 150k a year in insurance referrals"></textarea>
<div class="cm-add-row">
<input type="text" id="cmAddName" class="cm-add-password" placeholder="Your name" style="max-width:160px">
<input type="password" id="cmAddPassword" class="cm-add-password" placeholder="Verification password">
<button class="cm-add-btn" onclick="cmAddContext()">Add Context</button>
</div>
</div>
</div>

<div class="cm-footer">
If you need to remove any of this context please speak to a member of commercial finance.
</div>

</div>

<script>
{cm_js}
</script>
</body></html>"""


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "briefings/context-manager.html"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    html = generate_context_manager_html()
    Path(output).write_text(html)
    print(f"Context manager generated: {output} ({len(html):,} chars)")
