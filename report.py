"""Render the performance report from SQL results and candidate notes."""
from html import escape

ADDITIVE = (
    "completed_orders", "gross_pence", "refund_pence", "net_revenue_pence",
    "product_cost_pence", "fulfilment_cost_pence", "contribution_pence", "refunded_orders",
)


def business_notes(notes: str) -> str:
    active = False
    lines = []
    for line in notes.splitlines():
        if line.strip() == "## Business recommendation":
            active = True
            continue
        if active and line.startswith("## "):
            break
        if active and not (line.strip().startswith("<!--") and line.strip().endswith("-->")):
            lines.append(line)
    return "\n".join(lines).strip()


def money(pence: int) -> str:
    sign = "−" if pence < 0 else ""
    return f"{sign}£{abs(pence) // 100:,}.{abs(pence) % 100:02d}"


def ratio(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.1%}" if denominator else "n/a"


def delta(value: int, formatter) -> str:
    return ("+" if value > 0 else "") + formatter(value)


def render_report(columns, rows, quality, notes: str) -> str:
    records = [dict(zip(columns, row)) for row in rows]
    totals = {period: dict.fromkeys(ADDITIVE, 0) for period in ("baseline", "current")}
    segments = {}
    for row in records:
        period = row["period"]
        if period not in totals:
            raise ValueError("Report period must be baseline or current")
        for metric in ADDITIVE:
            totals[period][metric] += row[metric]
        key = (row["channel"], row["category"])
        segment = segments.setdefault(key, {p: dict.fromkeys(ADDITIVE, 0) for p in totals})
        for metric in ADDITIVE:
            segment[period][metric] += row[metric]
    baseline, current = totals["baseline"], totals["current"]
    metrics = (
        ("Gross sales", "gross_pence", money),
        ("Refunds", "refund_pence", money),
        ("Net revenue", "net_revenue_pence", money),
        ("Product costs", "product_cost_pence", money),
        ("Fulfilment costs", "fulfilment_cost_pence", money),
        ("Contribution", "contribution_pence", money),
        ("Completed orders", "completed_orders", lambda n: f"{n:,}"),
        ("Refunded orders", "refunded_orders", lambda n: f"{n:,}"),
    )
    overall = []
    for label, key, fmt in metrics:
        before, after = baseline[key], current[key]
        overall.append(f"<tr><th scope='row'>{label}</th><td>{fmt(before)}</td><td>{fmt(after)}</td>"
                       f"<td>{delta(after - before, fmt)}</td><td>{ratio(after - before, abs(before))}</td></tr>")
    for label, numerator, denominator in (
        ("Contribution margin", "contribution_pence", "net_revenue_pence"),
        ("Refunds / gross sales", "refund_pence", "gross_pence"),
    ):
        before = ratio(baseline[numerator], baseline[denominator])
        after = ratio(current[numerator], current[denominator])
        point_change = "n/a"
        if baseline[denominator] and current[denominator]:
            points = 100 * (current[numerator] / current[denominator] - baseline[numerator] / baseline[denominator])
            point_change = f"{points:+.1f} pp"
        overall.append(f"<tr><th scope='row'>{label}</th><td>{before}</td><td>{after}</td><td>{point_change}</td><td>Not applicable</td></tr>")
    segment_rows = []
    ordered = sorted(segments.items(), key=lambda item: (
        -abs(item[1]["current"]["contribution_pence"] - item[1]["baseline"]["contribution_pence"]), item[0]))
    for (channel, category), periods in ordered:
        before, after = periods["baseline"], periods["current"]
        segment_rows.append(
            f"<tr><th scope='row'>{escape(channel)} / {escape(category)}</th>"
            f"<td>{money(before['net_revenue_pence'])}</td><td>{money(after['net_revenue_pence'])}</td>"
            f"<td>{money(before['contribution_pence'])}</td><td>{money(after['contribution_pence'])}</td>"
            f"<td>{delta(after['contribution_pence'] - before['contribution_pence'], money)}</td>"
            f"<td>{ratio(before['refund_pence'], before['gross_pence'])}</td>"
            f"<td>{ratio(after['refund_pence'], after['gross_pence'])}</td></tr>"
        )
    if not segment_rows:
        segment_rows.append("<tr><td colspan='8'>No completed orders appear in these results.</td></tr>")
    bars = []
    maximum = max(1, *(abs(totals[p][k]) for p in totals for k in ("net_revenue_pence", "contribution_pence")))
    for i, (label, metric, period) in enumerate((
        ("Baseline net revenue", "net_revenue_pence", "baseline"),
        ("Current net revenue", "net_revenue_pence", "current"),
        ("Baseline contribution", "contribution_pence", "baseline"),
        ("Current contribution", "contribution_pence", "current"),
    )):
        value = totals[period][metric]
        width = abs(value) / maximum * 215
        x = 455 - width if value < 0 else 455
        y = 24 + i * 48
        colour = "#a5bccb" if period == "baseline" else "#087e8b"
        bars.append(f"<text x='8' y='{y + 17}'>{label}</text><rect x='{x:.2f}' y='{y}' "
                    f"width='{width:.2f}' height='24' fill='{colour}'/><text x='688' y='{y + 17}'>{money(value)}</text>")
    chart = ("<svg viewBox='0 0 880 220' role='img' aria-label='Net revenue and contribution, baseline and current'>"
             "<line x1='455' x2='455' y1='12' y2='200' stroke='#718493'/>" + "".join(bars) + "</svg>")
    quality_labels = {
        "input_rows": "Raw order rows", "accepted_orders": "Accepted orders, including cancelled",
        "duplicate_rows": "Duplicate order deliveries", "rejected_rows": "Rejected order rows",
        "invalid_values": "Rejected for invalid values", "unknown_product": "Rejected for unknown products",
    }
    quality_rows = "".join(f"<tr><th scope='row'>{label}</th><td>{int(quality[key]):,}</td></tr>"
                           for key, label in quality_labels.items())
    narrative = escape(business_notes(notes) or "Recommendation not supplied.")
    empty = "<p class='notice'>The query returned no completed orders. Check the data and SQL before using this report.</p>" if not records else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Technical task performance report</title>
<style>
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f8;color:#172c3b;font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1140px;margin:0 auto;padding:36px 24px 64px}}h1{{font-size:34px;line-height:1.15;margin:8px 0 16px}}h2{{font-size:22px;margin:0 0 14px}}
header{{padding-bottom:20px}}.eyebrow{{color:#087e8b;text-transform:uppercase;letter-spacing:.12em;font-size:13px;font-weight:700}}
section{{background:white;border:1px solid #d9e2e8;border-radius:12px;padding:24px;margin:20px 0}}p{{margin:8px 0 16px}}.muted,small{{color:#516675}}.notice{{padding:16px;background:#fff4db;border-left:4px solid #ac7622}}
.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}}th,td{{padding:12px 10px;border-bottom:1px solid #e4eaf0;text-align:right;white-space:nowrap}}th:first-child{{text-align:left}}thead th{{background:#eff5f7;font-size:12px;white-space:normal}}tbody th{{font-weight:500}}.narrative{{white-space:pre-wrap}}svg{{width:100%;height:auto;min-width:600px}}svg text{{font:12px system-ui,sans-serif;fill:#172c3b}}footer{{font-size:13px;color:#516675}}@media print{{body{{background:white}}main{{padding:0}}section{{break-inside:avoid}}}}
</style></head><body><main>
<header><div class="eyebrow">Technical task · synthetic retailer</div><h1>Sales performance and business actions</h1>
<p>The baseline covers 1 to 28 May 2026 and the current period covers 1 to 28 June 2026. Both include a complete 30-day refund follow-up.</p>
<p class="muted">This report uses the submitted calculations. Matching runs can still contain calculation errors.</p></header>{empty}
<section><h2>Business recommendation</h2><div class="narrative">{narrative}</div></section>
<section><h2>Overall performance</h2><div class="scroll">{chart}</div><div class="scroll"><table><thead><tr><th scope="col">Measure</th><th scope="col">Baseline</th><th scope="col">Current</th><th scope="col">Change</th><th scope="col">Change %</th></tr></thead><tbody>{''.join(overall)}</tbody></table></div>
<p><small>Net revenue = gross sales − refunds. Contribution = net revenue − product costs − fulfilment costs. Contribution excludes fixed overhead, tax and acquisition spend. It is not profit. Refunded orders still incur product and fulfilment costs.</small></p>
<p><small>Ratios divide period totals. Contribution margin divides contribution by net revenue. The refund ratio divides refunds by gross sales. Change % uses the absolute baseline. n/a marks a zero denominator. pp means percentage points.</small></p></section>
<section><h2>Channel and category changes</h2><p class="muted">Sorted by the size of the contribution change. These figures do not show what caused the change.</p>
<div class="scroll"><table><thead><tr><th scope="col">Channel / category</th><th scope="col">Baseline net revenue</th><th scope="col">Current net revenue</th><th scope="col">Baseline contribution</th><th scope="col">Current contribution</th><th scope="col">Contribution change</th><th scope="col">Baseline refunds / gross</th><th scope="col">Current refunds / gross</th></tr></thead><tbody>{''.join(segment_rows)}</tbody></table></div></section>
<section><h2>Data quality</h2><table><tbody>{quality_rows}</tbody></table><p><small>Order preparation produces these counts. SQL calculates performance for completed orders.</small></p></section>
<footer>Opportunity estimates illustrate a possible outcome under the stated assumptions. They are not forecasts or realised savings.</footer>
</main></body></html>
"""
