from flask import Blueprint, request, send_file, jsonify
import io
import re
from datetime import datetime

from Dao.ReportExportDao import ReportExportDao, SECTION_KEYS
from Utils.AdvancedReportExporter import build_excel_bytes, build_pdf_bytes

try:
    from Predictive.XgbLgbSalesForecast import XgbLgbSalesForecaster
    FORECAST_AVAILABLE = True
except Exception:
    FORECAST_AVAILABLE = False

report_export_api = Blueprint("report_export_api", __name__)
report_dao = ReportExportDao()

DEFAULT_SECTIONS = list(SECTION_KEYS.keys()) + ["sales_forecast"]


def _safe_filename(name: str, ext: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", (name or "report").strip()) or "report"
    return f"{name}.{ext}"


def _build_report_payload(section_ids, forecast_model="lgb", forecast_days=30):
    sql_ids = [s for s in section_ids if s != "sales_forecast"]
    data = report_dao.collect_sql_sections(sql_ids)

    if "sales_forecast" in section_ids:
        if FORECAST_AVAILABLE:
            try:
                fc = XgbLgbSalesForecaster()
                fr = fc.predict_next_days(model_type=forecast_model, days=int(forecast_days))
                if "error" not in fr:
                    data["sales_forecast"] = fr
                else:
                    data["sales_forecast"] = {"error": fr.get("error", "预测失败")}
            except Exception as e:
                data["sales_forecast"] = {"error": str(e)}
        else:
            data["sales_forecast"] = {"error": "预测模块不可用"}

    labels = []
    order = []
    for sid in section_ids:
        if sid in SECTION_KEYS:
            labels.append(SECTION_KEYS[sid])
            order.append((sid, SECTION_KEYS[sid]))
        elif sid == "sales_forecast":
            labels.append("销售预测与库存预警")
            order.append((sid, "销售预测与库存预警"))

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "section_labels": labels,
        "section_order": order,
        "data": data,
        "notes": "本报告由系统根据当前数据库与模型自动生成，仅供分析参考。",
    }


@report_export_api.route("/preview", methods=["POST"])
def report_preview():
    """返回将要导出的数据结构摘要（JSON）"""
    try:
        body = request.get_json(silent=True) or {}
        sections = body.get("sections") or DEFAULT_SECTIONS
        forecast_model = body.get("forecast_model", "lgb")
        forecast_days = int(body.get("forecast_days", 30))
        report = _build_report_payload(sections, forecast_model, forecast_days)
        # 精简体积：不重复大数组的每个元素
        summary = {
            "generated_at": report["generated_at"],
            "section_labels": report["section_labels"],
            "keys": list(report["data"].keys()),
        }
        return jsonify({"ok": True, "summary": summary})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@report_export_api.route("/excel", methods=["POST"])
def export_excel():
    try:
        body = request.get_json(silent=True) or {}
        title = body.get("title") or "高级数据分析报告"
        sections = body.get("sections") or DEFAULT_SECTIONS
        forecast_model = body.get("forecast_model", "lgb")
        forecast_days = int(body.get("forecast_days", 30))
        report = _build_report_payload(sections, forecast_model, forecast_days)
        raw = build_excel_bytes(report, title=title)
        return send_file(
            io.BytesIO(raw),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=_safe_filename(title, "xlsx"),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_export_api.route("/pdf", methods=["POST"])
def export_pdf():
    try:
        body = request.get_json(silent=True) or {}
        title = body.get("title") or "高级数据分析报告"
        sections = body.get("sections") or DEFAULT_SECTIONS
        forecast_model = body.get("forecast_model", "lgb")
        forecast_days = int(body.get("forecast_days", 30))
        report = _build_report_payload(sections, forecast_model, forecast_days)
        raw = build_pdf_bytes(report, title=title)
        return send_file(
            io.BytesIO(raw),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=_safe_filename(title, "pdf"),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
