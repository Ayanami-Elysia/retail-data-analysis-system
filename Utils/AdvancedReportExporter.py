"""
高级分析报表导出：Excel (openpyxl) / PDF (reportlab)
"""
import io
from datetime import datetime

import os

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _safe_sheet_name(name: str) -> str:
    name = name.replace("/", "-")[:31]
    return name or "Sheet"


def build_excel_bytes(report: dict, title: str = "高级数据分析报告") -> bytes:
    wb = Workbook()
    ws0 = wb.active
    ws0.title = "报告说明"
    ws0["A1"] = title
    ws0["A1"].font = Font(size=16, bold=True)
    ws0["A2"] = f"生成时间：{report.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
    ws0["A3"] = f"包含模块：{', '.join(report.get('section_labels', []))}"
    ws0["A4"] = report.get("notes", "")
    ws0.column_dimensions["A"].width = 80

    sections = report.get("data", {})
    for key, label in report.get("section_order", []):
        if key not in sections:
            continue
        data = sections[key]
        ws = wb.create_sheet(_safe_sheet_name(label))
        ws.append([label])
        ws["A1"].font = Font(bold=True, size=14)
        row = 3

        if key == "category_sales":
            ws.append(["品类", "销售额"])
            for item in (data.get("data") or []):
                ws.append([item.get("name"), item.get("value")])
        elif key == "sales_trend":
            ws.append(["日期", "订单数", "销售额"])
            dates = data.get("dates") or []
            orders = data.get("orders") or []
            amounts = data.get("amounts") or []
            for i, d in enumerate(dates):
                ws.append([d, orders[i] if i < len(orders) else "", amounts[i] if i < len(amounts) else ""])
        elif key == "seasonality":
            ws.append(["月份", "订单数", "销售额"])
            months = data.get("months") or []
            for i, m in enumerate(months):
                ws.append([m, (data.get("orders") or [])[i] if i < len(data.get("orders") or []) else "",
                          (data.get("amounts") or [])[i] if i < len(data.get("amounts") or []) else ""])
        elif key == "channel_analysis":
            ws.append(["渠道", "订单数", "销售额"])
            ch = data.get("channels") or []
            for i, c in enumerate(ch):
                ws.append([c, (data.get("orders") or [])[i] if i < len(data.get("orders") or []) else "",
                          (data.get("amounts") or [])[i] if i < len(data.get("amounts") or []) else ""])
        elif key == "customer_structure":
            ws.append(["性别", "人数"])
            for item in (data.get("sex") or []):
                ws.append([item.get("name"), item.get("value")])
            row = ws.max_row + 2
            ws.cell(row=row, column=1, value="年龄段")
            ws.cell(row=row, column=2, value="人数")
            row += 1
            buckets = data.get("age_buckets") or []
            counts = data.get("age_counts") or []
            for i, b in enumerate(buckets):
                ws.cell(row=row, column=1, value=b)
                ws.cell(row=row, column=2, value=counts[i] if i < len(counts) else "")
                row += 1
        elif key == "price_distribution":
            ws.append(["价格区间", "商品数"])
            bks = data.get("buckets") or []
            cnts = data.get("counts") or []
            for i, b in enumerate(bks):
                ws.append([b, cnts[i] if i < len(cnts) else ""])
        elif key == "return_exchange":
            ws.append(["订单状态", "数量"])
            for item in (data.get("data") or []):
                ws.append([item.get("name"), item.get("value")])
        elif key == "sales_heatmap":
            ws.append(["小时", "星期(0-6)", "订单数"])
            for triple in (data.get("data") or []):
                if len(triple) >= 3:
                    ws.append([triple[0], triple[1], triple[2]])
        elif key == "sales_forecast":
            ws.append(["说明", "值"])
            inv = (data.get("inventory_alert") or {})
            ws.append(["模型", data.get("model_type", "")])
            ws.append(["预警等级", inv.get("level", "")])
            ws.append(["未来7天趋势(%)", inv.get("growth_7d_pct", "")])
            ws.append(["补货建议", inv.get("suggestion", "")])
            ws.append([])
            ws.append(["日期", "历史销售额", "预测销售额"])
            dates = data.get("dates") or []
            hist = data.get("historical") or []
            pred = data.get("predicted") or []
            for i, d in enumerate(dates):
                h = hist[i] if i < len(hist) else None
                p = pred[i] if i < len(pred) else None
                ws.append([d, h if h is not None else "", p if p is not None else ""])
        else:
            ws.append(["原始数据(JSON 见 metrics.json 或接口)"])

        if ws.max_column:
            for col_idx in range(1, ws.max_column + 1):
                col_letter = ws.cell(row=1, column=col_idx).column_letter
                max_len = 10
                for r in range(1, ws.max_row + 1):
                    v = ws.cell(row=r, column=col_idx).value
                    if v is not None:
                        max_len = max(max_len, len(str(v)))
                ws.column_dimensions[col_letter].width = min(max_len + 2, 55)

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _register_cn_font():
    """Windows 下注册微软雅黑，便于 PDF 中文显示"""
    if getattr(_register_cn_font, "_done", False):
        return getattr(_register_cn_font, "font_name", "Helvetica")
    font_name = "Helvetica"
    candidates = []
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates.extend(
        [
            os.path.join(windir, "Fonts", "simhei.ttf"),
            os.path.join(windir, "Fonts", "msyh.ttc"),
            os.path.join(windir, "Fonts", "msyhbd.ttc"),
            os.path.join(windir, "Fonts", "simsun.ttc"),
        ]
    )
    for path in candidates:
        if os.path.isfile(path):
            try:
                name = "ReportCN"
                pdfmetrics.registerFont(TTFont(name, path))
                font_name = name
                break
            except Exception:
                continue
    _register_cn_font._done = True
    _register_cn_font.font_name = font_name
    return font_name


def build_pdf_bytes(report: dict, title: str = "高级数据分析报告") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    fn = _register_cn_font()
    story = []
    title_style = ParagraphStyle(
        "T", parent=styles["Heading1"], fontName=fn, fontSize=16, spaceAfter=12
    )
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName=fn, fontSize=12, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("B", parent=styles["Normal"], fontName=fn, fontSize=9, leading=14)

    story.append(Paragraph(title.replace("&", "&amp;"), title_style))
    story.append(Paragraph(f"生成时间：{report.get('generated_at', '')}", body))
    story.append(Paragraph(f"包含模块：{', '.join(report.get('section_labels', []))}", body))
    story.append(Spacer(1, 0.4 * cm))

    sections = report.get("data", {})
    for key, label in report.get("section_order", []):
        if key not in sections:
            continue
        data = sections[key]
        story.append(Paragraph(f"{label}", h2))

        lines = []
        if key == "category_sales":
            for item in (data.get("data") or [])[:30]:
                lines.append(f"{item.get('name')}: {item.get('value')}")
        elif key == "sales_trend":
            dates = data.get("dates") or []
            for i, d in enumerate(dates[:40]):
                o = (data.get("orders") or [])[i] if i < len(data.get("orders") or []) else ""
                a = (data.get("amounts") or [])[i] if i < len(data.get("amounts") or []) else ""
                lines.append(f"{d} 订单:{o} 销售额:{a}")
            if len(dates) > 40:
                lines.append(f"... 共 {len(dates)} 条，详见 Excel")
        elif key == "seasonality":
            months = data.get("months") or []
            for i, m in enumerate(months[:24]):
                o = (data.get("orders") or [])[i] if i < len(data.get("orders") or []) else ""
                a = (data.get("amounts") or [])[i] if i < len(data.get("amounts") or []) else ""
                lines.append(f"{m} 订单:{o} 销售额:{a}")
        elif key == "channel_analysis":
            ch = data.get("channels") or []
            for i, c in enumerate(ch):
                o = (data.get("orders") or [])[i] if i < len(data.get("orders") or []) else ""
                a = (data.get("amounts") or [])[i] if i < len(data.get("amounts") or []) else ""
                lines.append(f"{c} 订单:{o} 销售额:{a}")
        elif key == "customer_structure":
            lines.append("性别分布：")
            for item in (data.get("sex") or []):
                lines.append(f"  {item.get('name')}: {item.get('value')}")
            lines.append("年龄段：")
            buckets = data.get("age_buckets") or []
            counts = data.get("age_counts") or []
            for i, b in enumerate(buckets):
                lines.append(f"  {b}: {counts[i] if i < len(counts) else ''}")
        elif key == "price_distribution":
            bks = data.get("buckets") or []
            cnts = data.get("counts") or []
            for i, b in enumerate(bks):
                lines.append(f"{b}: {cnts[i] if i < len(cnts) else ''}")
        elif key == "return_exchange":
            for item in (data.get("data") or []):
                lines.append(f"{item.get('name')}: {item.get('value')}")
        elif key == "sales_heatmap":
            lines.append("（热力图明细较多，PDF 仅展示前 50 条）")
            for triple in (data.get("data") or [])[:50]:
                lines.append(f"小时 {triple[0]} 周几 {triple[1]} 订单 {triple[2]}")
        elif key == "sales_forecast":
            inv = data.get("inventory_alert") or {}
            lines.append(f"模型：{data.get('model_type', '')}")
            lines.append(f"预警：{inv.get('level', '')} 未来7天趋势：{inv.get('growth_7d_pct', '')}%")
            lines.append(f"建议：{inv.get('suggestion', '')}")
        else:
            lines.append("(无摘要)")

        for line in lines:
            safe = str(line).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, body))
        story.append(Spacer(1, 0.2 * cm))

    doc.build(story)
    return buffer.getvalue()
