"""
高级分析报表：从数据库聚合各模块数据（供导出 PDF/Excel 使用）
"""
from Dao.DataAnalysisConnect import DataAnalysisDao


SECTION_KEYS = {
    "category_sales": "品类分布",
    "sales_trend": "销售趋势",
    "seasonality": "季节波动",
    "channel_analysis": "渠道对比",
    "customer_structure": "客户结构",
    "price_distribution": "价格分布",
    "return_exchange": "退换货/订单状态",
    "sales_heatmap": "销售热力图",
}


class ReportExportDao:
    def __init__(self):
        self.dao = DataAnalysisDao()

    def collect_sql_sections(self, section_ids):
        """仅聚合基于 Dao/SQL 的模块"""
        out = {}
        for sid in section_ids:
            if sid == "category_sales":
                out[sid] = self.dao.get_category_sales()
            elif sid == "sales_trend":
                out[sid] = self.dao.get_sales_trend()
            elif sid == "seasonality":
                out[sid] = self.dao.get_seasonality()
            elif sid == "channel_analysis":
                out[sid] = self.dao.get_channel_analysis()
            elif sid == "customer_structure":
                out[sid] = self.dao.get_customer_structure()
            elif sid == "price_distribution":
                out[sid] = self.dao.get_price_distribution()
            elif sid == "return_exchange":
                out[sid] = self.dao.get_return_exchange()
            elif sid == "sales_heatmap":
                out[sid] = self.dao.get_sales_heatmap()
        return out
