from flask import Blueprint, jsonify
from Dao.DataAnalysisConnect import DataAnalysisDao
from Predictive.SalesPrediction import SalesPredictionModel
from Predictive.XgbLgbSalesForecast import XgbLgbSalesForecaster
import traceback
from datetime import datetime

# 有条件地导入UserBehaviorAnalysis
try:
    from Predictive.UserBehaviorAnalysis import UserBehaviorAnalysis
    USER_BEHAVIOR_AVAILABLE = True
except ImportError:
    USER_BEHAVIOR_AVAILABLE = False
    print("Warning: UserBehaviorAnalysis模块导入失败，用户行为分析功能将不可用")

# 创建蓝图
data_analysis_api = Blueprint('data_analysis_api', __name__)
dao = DataAnalysisDao()

@data_analysis_api.route('/sales_trend', methods=['GET'])
def get_sales_trend():
    """获取销售趋势数据"""
    try:
        result = dao.get_sales_trend()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/user_distribution', methods=['GET'])
def get_user_distribution():
    """获取用户地域分布数据"""
    try:
        result = dao.get_user_distribution()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/category_sales', methods=['GET'])
def get_category_sales():
    """获取商品类别销售占比数据"""
    try:
        result = dao.get_category_sales()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/channel_analysis', methods=['GET'])
def get_channel_analysis():
    """获取销售渠道分析数据"""
    try:
        result = dao.get_channel_analysis()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/user_behavior', methods=['GET'])
def get_user_behavior():
    """获取用户行为分析数据"""
    try:
        result = dao.get_user_behavior()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/payment_methods', methods=['GET'])
def get_payment_methods():
    """获取支付方式分布数据"""
    try:
        result = dao.get_payment_methods()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/hot_products', methods=['GET'])
def get_hot_products():
    """获取热销商品排行数据"""
    try:
        result = dao.get_hot_products()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/member_consumption', methods=['GET'])
def get_member_consumption():
    """获取会员等级消费分析数据"""
    try:
        result = dao.get_member_consumption()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_analysis_api.route('/seasonality', methods=['GET'])
def get_seasonality():
    """获取季节波动（月度汇总）"""
    try:
        result = dao.get_seasonality()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_analysis_api.route('/customer_structure', methods=['GET'])
def get_customer_structure():
    """获取客户结构（性别/年龄段）"""
    try:
        result = dao.get_customer_structure()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_analysis_api.route('/price_distribution', methods=['GET'])
def get_price_distribution():
    """获取价格分布（分桶）"""
    try:
        result = dao.get_price_distribution()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_analysis_api.route('/sales_heatmap', methods=['GET'])
def get_sales_heatmap():
    """获取销售热力图（周几*小时）"""
    try:
        result = dao.get_sales_heatmap()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_analysis_api.route('/return_exchange', methods=['GET'])
def get_return_exchange():
    """获取退换货/退款情况（订单状态分布）"""
    try:
        result = dao.get_return_exchange()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/sales_prediction', methods=['GET'])
def get_sales_prediction():
    """获取销售预测数据"""
    try:
        model = SalesPredictionModel()
        predictions, error = model.predict_future_sales(days=30)
        
        if predictions:
            # 添加编码处理，确保中文不会出现编码问题
            return jsonify(predictions)
        else:
            # 处理error可能是None的情况
            error_msg = str(error) if error else "未知错误"
            return jsonify({
                'error': error_msg,
                'dates': [datetime.now().strftime('%m-%d')],
                'historical': [0],
                'predicted': [0],
                'prediction_start_index': 0,
                'model_type': 'N/A',
                'accuracy': 0,
                'mse': 0,
                'r2_score': 0,
                'growth_rate': 0,
                'predicted_total': 0,
                'conclusion': '无法生成预测，请确保有足够的历史数据。'
            }), 500
    except Exception as e:
        print(f"销售预测API错误: {e}")
        traceback.print_exc()
        # 处理异常的情况
        error_msg = str(e) if e else "未知错误"
        return jsonify({
            'error': error_msg,
            'dates': [datetime.now().strftime('%m-%d')],
            'historical': [0],
            'predicted': [0],
            'prediction_start_index': 0,
            'model_type': 'N/A',
            'accuracy': 0,
            'mse': 0,
            'r2_score': 0,
            'growth_rate': 0,
            'predicted_total': 0,
            'conclusion': '预测过程中发生错误，请稍后再试。'
        }), 500


@data_analysis_api.route('/sales_forecast', methods=['GET'])
def sales_forecast():
    """XGBoost/LightGBM 销售预测（含库存预警/补货建议）"""
    try:
        # model 参数：xgb / lgb
        from flask import request
        model_type = request.args.get('model', 'lgb')
        days = int(request.args.get('days', 30))
        forecaster = XgbLgbSalesForecaster()
        result = forecaster.predict_next_days(model_type=model_type, days=days)
        status = 200 if 'error' not in result else 500
        return jsonify(result), status
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@data_analysis_api.route('/sales_model_eval', methods=['GET'])
def sales_model_eval():
    """训练并输出模型性能（保存 ROC/PR/混淆矩阵/mAP 对比图到 static/images/model_eval）"""
    try:
        forecaster = XgbLgbSalesForecaster()
        result = forecaster.train_and_evaluate()
        status = 200 if 'error' not in result else 500
        return jsonify(result), status
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@data_analysis_api.route('/user_analysis', methods=['GET'])
def get_user_analysis():
    """获取用户行为分析数据"""
    try:
        # 检查用户行为分析模块是否可用
        if not USER_BEHAVIOR_AVAILABLE:
            return jsonify({
                'error': '用户行为分析模块不可用，请先安装lightgbm库',
                'clusters': [
                    {'id': 1, 'behavior_type': '高价值', 'user_count': 0},
                    {'id': 2, 'behavior_type': '潜力型', 'user_count': 0},
                    {'id': 3, 'behavior_type': '活跃浏览', 'user_count': 0}
                ],
                'user_points': [],
                'total_users': 0,
                'avg_purchase_intention': 0,
                'model_accuracy': 0,
                'auc': 0,
                'second_model': 'KMeans',
                'purchase_prediction': {'likely_to_purchase': 0, 'unlikely_to_purchase': 100},
                'marketing_suggestions': ['用户行为分析模块不可用，请安装所需的依赖库']
            })
            
        # 获取用户行为数据
        user_data = dao.get_user_behavior_data()
        
        # 如果没有足够的用户数据，返回默认数据
        if len(user_data) < 5:
            return jsonify({
                'error': '没有足够的用户行为数据',
                'clusters': [
                    {'id': 1, 'behavior_type': '高价值', 'user_count': 0},
                    {'id': 2, 'behavior_type': '潜力型', 'user_count': 0},
                    {'id': 3, 'behavior_type': '活跃浏览', 'user_count': 0}
                ],
                'user_points': [],
                'total_users': 0,
                'avg_purchase_intention': 0,
                'model_accuracy': 0,
                'auc': 0,
                'second_model': 'KMeans',
                'purchase_prediction': {'likely_to_purchase': 0, 'unlikely_to_purchase': 100},
                'marketing_suggestions': ['暂无足够数据进行分析，建议收集更多用户行为数据']
            })
        
        # 使用UserBehaviorAnalysis模型进行分析
        analysis_model = UserBehaviorAnalysis()
        result = analysis_model.analyze(user_data)
        
        return jsonify(result)
    except Exception as e:
        print(f"用户行为分析API错误: {e}")
        traceback.print_exc()
        
        # 处理异常的情况
        error_msg = str(e) if e else "未知错误"
        return jsonify({
            'error': error_msg,
            'clusters': [
                {'id': 1, 'behavior_type': '高价值', 'user_count': 0},
                {'id': 2, 'behavior_type': '潜力型', 'user_count': 0},
                {'id': 3, 'behavior_type': '活跃浏览', 'user_count': 0}
            ],
            'user_points': [],
            'total_users': 0,
            'avg_purchase_intention': 0,
            'model_accuracy': 0,
            'auc': 0,
            'second_model': 'KMeans',
            'purchase_prediction': {'likely_to_purchase': 0, 'unlikely_to_purchase': 100},
            'marketing_suggestions': ['分析过程中发生错误，请稍后再试']
        }), 500
