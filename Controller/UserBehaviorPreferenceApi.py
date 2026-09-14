from flask import Blueprint, jsonify, request
from Dao.DataAnalysisConnect import DataAnalysisDao
import traceback


behavior_preference_api = Blueprint('behavior_preference_api', __name__)
dao = DataAnalysisDao()


@behavior_preference_api.route('/browse_preference', methods=['GET'])
def browse_preference():
    """
    浏览偏好：基于 user_behavior(view) 统计 Top 类目/Top 商品
    """
    try:
        limit = int(request.args.get('limit', 10))
        result = dao.get_browse_preference(limit=limit)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@behavior_preference_api.route('/purchase_preference', methods=['GET'])
def purchase_preference():
    """
    购物偏好：基于 user_behavior(purchase) 统计 Top 类目/Top 商品
    """
    try:
        limit = int(request.args.get('limit', 10))
        result = dao.get_purchase_preference(limit=limit)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@behavior_preference_api.route('/favorite_preference', methods=['GET'])
def favorite_preference():
    """
    收藏偏好：当前表结构没有 favorite/collect 行为，使用 cart(加购) 作为“收藏意向”代理指标
    """
    try:
        limit = int(request.args.get('limit', 10))
        result = dao.get_favorite_preference(limit=limit)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@behavior_preference_api.route('/refund_patterns', methods=['GET'])
def refund_patterns():
    """
    退款高发场景：结合 sales_order(退款状态) 与 user_behavior(购买行为时间) 做维度统计
    """
    try:
        result = dao.get_refund_patterns()
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

