from datetime import datetime
from pathlib import Path


class Exporter:

    _STATUS_COLORS = {
        "full support": ("#15803d", "#dcfce7"),
        "maintenance": ("#854d0e", "#fef9c3"),
        "end of life": ("#991b1b", "#fee2e2"),
        "end of life (eol)": ("#991b1b", "#fee2e2"),
        "unsupported": ("#991b1b", "#fee2e2"),
        "extended support": ("#0e7490", "#cffafe"),
    }

    _COMPAT_COLORS = {
        "yes": ("#15803d", "#dcfce7"),
        "no": ("#991b1b", "#fee2e2"),
        "n/a": ("#6b7280", "#f3f4f6"),
    }

    COLUMNS = [
        "NAME", "CHANNEL", "PRODUCT VERSION",
        "OCP COMPATIBLE", "SUPPORT STATUS", "END OF LIFE (EOL)",
    ]

    def _has_eol(self, results):
        for r in results:
            s = r.get("support_status", "").lower()
            if "end of life" in s or "unsupported" in s:
                return True
        return False

    def _row_values(self, res):
        return [
            res["name"],
            res.get("channel", "N/A"),
            res.get("product_version", res.get("version", "N/A")),
            res["ocp_compatible"],
            res["support_status"],
            res["end_date"],
        ]

    def _resolve_path(self, fmt, output_dir):
        d = Path(output_dir)
        d.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d")
        return d / f"compliance-report-{ts}.{fmt}"

    # ── public entry point ────────────────────────────────────────

    def export(self, results, fmt, output_dir="."):
        filepath = self._resolve_path(fmt, output_dir)
        if fmt == "html":
            content = self._render_html(results)
        else:
            content = self._render_markdown(results)
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)

    # ── HTML rendering ────────────────────────────────────────────

    def _status_pill_html(self, value):
        key = value.lower()
        for pattern, (fg, bg) in self._STATUS_COLORS.items():
            if pattern in key:
                return (
                    f'<span style="display:inline-block;padding:4px 14px;'
                    f"border-radius:12px;font-size:13px;font-weight:600;"
                    f'background:{bg};color:{fg}">{value}</span>'
                )
        return f'<span style="color:#6b7280">{value}</span>'

    def _compat_pill_html(self, value):
        fg, bg = self._COMPAT_COLORS.get(value.lower(), ("#6b7280", "#f3f4f6"))
        return (
            f'<span style="display:inline-block;padding:4px 14px;'
            f"border-radius:12px;font-size:13px;font-weight:600;"
            f'background:{bg};color:{fg}">{value}</span>'
        )

    def _render_html(self, results):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows_html = []
        for res in results:
            vals = self._row_values(res)
            compat_cell = self._compat_pill_html(vals[3])
            status_cell = self._status_pill_html(vals[4])
            rows_html.append(
                "<tr>"
                f"<td>{vals[0]}</td>"
                f"<td>{vals[1]}</td>"
                f"<td>{vals[2]}</td>"
                f'<td style="text-align:center">{compat_cell}</td>'
                f"<td>{status_cell}</td>"
                f"<td>{vals[5]}</td>"
                "</tr>"
            )

        alert_html = ""
        if self._has_eol(results):
            alert_html = (
                '<div style="margin:24px 0;padding:16px 20px;'
                "border-radius:12px;border:1px solid #fca5a5;"
                'background:#fef2f2;color:#991b1b;font-size:14px">'
                "<strong>Compliance Alert:</strong> "
                "One or more operators are End of Life (EOL) or out of the support window. "
                "We recommend planning the upgrade of these operators to a supported version "
                "as soon as possible to ensure security patches and official Red Hat support."
                "</div>"
            )

        header_cells = "".join(f"<th>{c}</th>" for c in self.COLUMNS)

        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Operator Compliance Diagnostics - ComplianShift</title>
<style>
  *,*::before,*::after{{box-sizing:border-box}}
  body{{
    margin:0;padding:40px 20px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
    background:linear-gradient(145deg,#fef9e7 0%,#fdf6e3 40%,#f5f0dc 100%);
    min-height:100vh;color:#1f2937;
  }}
  .container{{
    max-width:1200px;margin:0 auto;
    background:#fffefb;border-radius:20px;
    box-shadow:0 4px 24px rgba(0,0,0,.06);
    padding:32px;
  }}
  h1{{
    font-size:22px;font-weight:700;margin:0 0 4px;color:#1f2937;
  }}
  .subtitle{{
    font-size:13px;color:#9ca3af;margin:0 0 28px;
  }}
  table{{
    width:100%;border-collapse:separate;border-spacing:0;
  }}
  thead th{{
    text-align:left;font-size:12px;font-weight:600;
    color:#9ca3af;text-transform:uppercase;letter-spacing:.5px;
    padding:12px 16px;border-bottom:1px dashed #e5e7eb;
  }}
  tbody tr{{
    transition:background .15s;
  }}
  tbody tr:hover{{
    background:#fefce8;
  }}
  tbody td{{
    padding:14px 16px;font-size:14px;
    border-bottom:1px solid #f3f4f6;color:#374151;
  }}
  tbody tr:last-child td{{
    border-bottom:none;
  }}
  .footer{{
    margin-top:20px;padding-top:16px;
    border-top:1px solid #f3f4f6;
    font-size:12px;color:#9ca3af;text-align:right;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>Operator Compliance Diagnostics</h1>
  <p class="subtitle">ComplianShift &mdash; Red Hat Operators lifecycle analysis on OpenShift</p>
  <table>
    <thead><tr>{header_cells}</tr></thead>
    <tbody>
{"".join(rows_html)}
    </tbody>
  </table>
  {alert_html}
  <div class="footer">Generated on {timestamp}</div>
</div>
</body>
</html>"""

    # ── Markdown rendering ────────────────────────────────────────

    def _render_markdown(self, results):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        widths = [len(c) for c in self.COLUMNS]
        all_rows = []
        for res in results:
            vals = self._row_values(res)
            all_rows.append(vals)
            for i, v in enumerate(vals):
                widths[i] = max(widths[i], len(str(v)))

        header = "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(self.COLUMNS)) + " |"
        sep = "| " + " | ".join("-" * widths[i] for i in range(len(self.COLUMNS))) + " |"

        lines = [
            "# Operator Compliance Diagnostics (ComplianShift)\n",
            header,
            sep,
        ]
        for vals in all_rows:
            lines.append("| " + " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(vals)) + " |")

        lines.append("")

        if self._has_eol(results):
            lines.append(
                "> **Compliance Alert:** One or more operators are End of Life (EOL) "
                "or out of the support window. We recommend planning the upgrade of "
                "these operators to a supported version as soon as possible to ensure "
                "security patches and official Red Hat support."
            )
            lines.append("")

        lines.append(f"*Generated on {timestamp}*")
        return "\n".join(lines) + "\n"
