# HTML Template Extraction Plan

_Future refactor: extract the 3,000+ line HTML f-string from `generate_dashboard_html()` into a proper template system._

## Current State
- ~1,450 lines of CSS (lines 4771-6219 of agentic_briefing.py)
- ~1,420 lines of JS (lines 6304-7726)
- All inside a Python f-string with `{{` `}}` brace escaping
- Contains Python interpolations: `{generated_utc}`, `{driver_trends_json}`, `{chart_data_json}`, etc.
- The `_add_driver_id` regex function modifies HTML before the f-string renders

## Why This Matters
- Silent bugs from JS inside Python f-strings (the `const` duplication bug)
- No JS linting possible on embedded code
- IDE syntax highlighting breaks inside the f-string
- CSS changes require Python knowledge

## Recommended Approach
1. Create `templates/dashboard.html` with Jinja2-style `{{ variable }}` placeholders
2. Create `templates/dashboard.css` (extracted, un-escaped CSS)
3. Create `templates/dashboard.js` (extracted, un-escaped JS)
4. Have `generate_dashboard_html()` read the template and do `str.replace()` or `jinja2.render()`
5. The JS and CSS files can then be linted independently

## Migration Steps
1. Extract CSS into `templates/dashboard.css` — un-escape all `{{` → `{`
2. Extract JS into `templates/dashboard.js` — un-escape all `{{` → `{`
3. Replace CSS/JS blocks in the f-string with `{css_content}` and `{js_content}` placeholders
4. Read the files at the start of `generate_dashboard_html()` and inject them
5. Run full test pass: verify HTML output is byte-identical before and after

## Risk Mitigation
- Generate both old and new HTML, diff them, confirm identical output
- Add a test that generates a dashboard and checks for key elements
- Do this on a separate branch with a dedicated PR
