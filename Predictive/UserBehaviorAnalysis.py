import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
import lightgbm as lgb
import traceback
from datetime import datetime, timedelta
import random

class UserBehaviorAnalysis:
    """用户行为分析模型
    
    使用LightGBM进行购买意向预测和KMeans用于用户分群
    """
    
    def __init__(self):
        self.lgb_model = None
        self.kmeans_model = None
        self.scaler = StandardScaler()
        
    def _prepare_features(self, user_data):
        """准备特征数据"""
        if not user_data:
            return None, None
        
        # 转换为DataFrame
        df = pd.DataFrame(user_data)
        
        # 特征工程
        # 1. 行为比率
        df['view_to_cart_ratio'] = df.apply(lambda row: row['cart_count'] / row['view_count'] if row['view_count'] > 0 else 0, axis=1)
        df['cart_to_purchase_ratio'] = df.apply(lambda row: row['purchase_count'] / row['cart_count'] if row['cart_count'] > 0 else 0, axis=1)
        df['view_to_purchase_ratio'] = df.apply(lambda row: row['purchase_count'] / row['view_count'] if row['view_count'] > 0 else 0, axis=1)
        
        # 2. 活跃度指标
        # 活动天数比例（过去90天）
        df['activity_frequency'] = df['activity_days'] / 90
        
        # 3. 最后活动距今天数
        df['days_since_last_activity'] = df['days_since_last_activity'].fillna(90)  # 默认为90天
        df['recency_score'] = 1 - (df['days_since_last_activity'] / 90).clip(0, 1)  # 0-1之间，越接近1表示越近
        
        # 4. 购物车放弃率
        df['cart_abandonment_rate'] = df.apply(lambda row: 1 - (row['purchase_count'] / row['cart_count'] if row['cart_count'] > 0 else 0), axis=1)
        
        # 5. 客单价
        df['average_order_value'] = df.apply(lambda row: row['total_amount'] / row['order_count'] if row['order_count'] > 0 else 0, axis=1)
        
        # 6. 商品多样性
        df['product_diversity'] = df['unique_products'] / (df['view_count'] + 1)
        
        # 7. 购买标记（是否有购买行为）
        df['has_purchase'] = (df['purchase_count'] > 0).astype(int)
        
        # 8. 购买可能性得分（历史数据计算，非预测值）
        # 基于活跃度、最近购买时间、购买比例等计算一个购买可能性得分
        df['purchase_probability'] = (
            0.3 * df['recency_score'] +  # 最近活动
            0.3 * df['activity_frequency'] +  # 活跃频率
            0.2 * df['view_to_purchase_ratio'] +  # 浏览到购买转化率
            0.2 * (1 - df['cart_abandonment_rate'])  # 购物车完成率
        )
        
        # 选择特征列
        feature_cols = [
            'view_count', 'search_count', 'cart_count', 'purchase_count', 
            'unique_products', 'activity_days', 'order_count', 'total_amount',
            'view_to_cart_ratio', 'cart_to_purchase_ratio', 'view_to_purchase_ratio',
            'activity_frequency', 'recency_score', 'cart_abandonment_rate',
            'average_order_value', 'product_diversity'
        ]
        
        # 标准化特征
        X = df[feature_cols]
        y = df['has_purchase']
        
        # 替换无穷值和NaN
        X = X.replace([np.inf, -np.inf], 0).fillna(0)
        
        return X, y, df
    
    def _train_lightgbm(self, X, y):
        """训练LightGBM模型预测购买意向"""
        if X is None or len(X) < 10:  # 至少需要10个样本
            return None, 0, 0
        
        try:
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # LightGBM参数
            params = {
                'objective': 'binary',
                'metric': 'auc',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'verbose': -1
            }
            
            # 创建数据集
            train_data = lgb.Dataset(X_train, label=y_train)
            
            # 训练模型
            model = lgb.train(params, train_data, num_boost_round=100)
            
            # 评估模型
            y_pred_prob = model.predict(X_test)
            y_pred = (y_pred_prob > 0.5).astype(int)
            
            accuracy = accuracy_score(y_test, y_pred) * 100
            auc = roc_auc_score(y_test, y_pred_prob)
            
            return model, accuracy, auc
            
        except Exception as e:
            print(f"训练LightGBM模型出错: {e}")
            traceback.print_exc()
            return None, 0, 0
    
    def _cluster_users(self, X, df):
        """使用KMeans对用户进行分群"""
        if X is None or len(X) < 5:  # 至少需要5个样本
            return None, []
        
        try:
            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)
            
            # 确定最佳聚类数 (简化版，实际中可以使用肘部法则或轮廓系数)
            n_clusters = min(5, len(X))  # 最多5个群体或样本数
            
            # KMeans聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # 将聚类标签添加到原始数据
            df['cluster'] = cluster_labels
            
            # 分析各聚类特征
            cluster_analysis = []
            for i in range(n_clusters):
                cluster_df = df[df['cluster'] == i]
                
                # 确定行为类型
                behavior_type = self._determine_behavior_type(cluster_df)
                
                cluster_info = {
                    'id': i,
                    'behavior_type': behavior_type,
                    'user_count': len(cluster_df),
                    'avg_view': cluster_df['view_count'].mean(),
                    'avg_cart': cluster_df['cart_count'].mean(),
                    'avg_purchase': cluster_df['purchase_count'].mean(),
                    'avg_recency': cluster_df['recency_score'].mean(),
                    'avg_activity': cluster_df['activity_frequency'].mean(),
                    'avg_purchase_probability': cluster_df['purchase_probability'].mean()
                }
                cluster_analysis.append(cluster_info)
            
            return kmeans, cluster_analysis
            
        except Exception as e:
            print(f"用户聚类出错: {e}")
            traceback.print_exc()
            return None, []
    
    def _determine_behavior_type(self, cluster_df):
        """根据聚类特征确定行为类型"""
        avg_purchase = cluster_df['purchase_count'].mean()
        avg_cart = cluster_df['cart_count'].mean()
        avg_view = cluster_df['view_count'].mean()
        avg_recency = cluster_df['recency_score'].mean()
        avg_purchase_probability = cluster_df['purchase_probability'].mean()
        cart_abandonment = cluster_df['cart_abandonment_rate'].mean()
        
        # 显著降低分类阈值，确保能将用户分为不同类型
        # 高价值用户：购买行为多
        if avg_purchase > 1.5 and avg_purchase_probability > 0.4:
            return 'high_value'
        
        # 潜力用户：浏览多，购买较少
        elif avg_view > 5 and avg_purchase < 1.5 and avg_recency > 0.4:
            return 'potential'
        
        # 活跃浏览者：浏览多，购买很少
        elif avg_view > 3 and avg_purchase < 1:
            return 'active_browser'
        
        # 购物车弃用者：添加购物车但不购买
        elif avg_cart > 0.5 and cart_abandonment > 0.5:
            return 'cart_abandoner'
        
        # 流失风险：最近不活跃
        elif avg_recency < 0.4:
            return 'at_risk'
        
        # 默认情况下，根据主要特征指定一个类别，而不是统一归为general
        else:
            # 根据最突出的特征确定类型，避免全部归为general
            features = {
                'high_value': avg_purchase * avg_recency,
                'potential': avg_view * avg_recency * (1 - avg_purchase/10 if avg_purchase > 0 else 1),
                'active_browser': avg_view * (1 - avg_purchase/10 if avg_purchase > 0 else 1),
                'cart_abandoner': avg_cart * cart_abandonment,
                'at_risk': 1 - avg_recency
            }
            
            # 返回得分最高的类型
            return max(features.items(), key=lambda x: x[1])[0]
    
    def _generate_user_points(self, X, cluster_labels, df):
        """生成用户聚类散点图数据"""
        if X is None or len(X) < 1:
            return []
            
        try:
            # 从原始特征中提取活跃度、购买倾向和流失风险指标
            active_score = df['activity_frequency'].values  # 活跃度
            purchase_score = df['purchase_probability'].values  # 购买倾向
            churn_risk = 1 - df['recency_score'].values  # 流失风险
            behavior_types = [self._get_behavior_name(cluster_labels[i]) for i in range(len(cluster_labels))]
            
            # 生成散点图数据点 [活跃度, 购买倾向, 流失风险, 聚类ID, 行为类型]
            points = []
            for i in range(len(X)):
                points.append([
                    float(active_score[i]),
                    float(purchase_score[i]),
                    float(churn_risk[i]),
                    int(cluster_labels[i]),
                    behavior_types[int(cluster_labels[i])]
                ])
            
            return points
            
        except Exception as e:
            print(f"生成用户聚类散点图数据出错: {e}")
            traceback.print_exc()
            return []
    
    def _get_behavior_name(self, cluster_id):
        """获取行为类型的中文名称"""
        behavior_map = {
            'high_value': '高价值',
            'potential': '潜力型',
            'active_browser': '活跃浏览',
            'cart_abandoner': '购物车弃用',
            'at_risk': '流失风险',
            'general': '普通用户'
        }
        
        # 这里简化处理，实际中应根据聚类分析结果确定
        behavior_types = ['high_value', 'potential', 'active_browser', 'cart_abandoner', 'at_risk']
        behavior = behavior_types[cluster_id % len(behavior_types)]
        
        return behavior_map.get(behavior, behavior)
    
    def _generate_marketing_suggestions(self, cluster_analysis):
        """生成营销策略建议"""
        suggestions = []
        
        for cluster in cluster_analysis:
            behavior = cluster['behavior_type']
            cluster_id = cluster['id']
            user_count = cluster['user_count']
            
            if behavior == 'high_value':
                suggestions.append(f"对高价值用户群体(群体{cluster_id}，{user_count}人)实施会员忠诚计划，提供专属优惠和VIP服务，增强用户粘性。")
                suggestions.append(f"为高价值用户群体{cluster_id}提供专属客服和个性化产品推荐，提高复购率。")
            
            elif behavior == 'potential':
                suggestions.append(f"向潜力型用户群体(群体{cluster_id}，{user_count}人)发送个性化促销信息，针对其浏览但未购买的商品提供限时优惠。")
                suggestions.append(f"对潜力用户群体{cluster_id}进行精准营销，设计转化漏斗，提供首单优惠券激励购买。")
            
            elif behavior == 'active_browser':
                suggestions.append(f"对活跃浏览用户群体(群体{cluster_id}，{user_count}人)进行精准内容推送，增加首单优惠力度，提高转化率。")
                suggestions.append(f"改进活跃浏览用户群体{cluster_id}的产品展示页面，突出用户评价和产品优势，消除购买障碍。")
            
            elif behavior == 'cart_abandoner':
                suggestions.append(f"针对购物车弃用群体(群体{cluster_id}，{user_count}人)设置购物车提醒机制，提供满减或免运费等激励完成订单。")
                suggestions.append(f"简化购物车群体{cluster_id}的结账流程，设置限时优惠倒计时，增加购买紧迫感。")
            
            elif behavior == 'at_risk':
                suggestions.append(f"对流失风险用户群体(群体{cluster_id}，{user_count}人)进行挽回活动，发送个性化优惠券和回归礼包，重新激活用户。")
                suggestions.append(f"对流失风险群体{cluster_id}进行问卷调查，了解流失原因，有针对性地改进产品和服务。")
        
        # 根据用户分群情况，生成整体营销建议
        types_count = {}
        for cluster in cluster_analysis:
            b_type = cluster['behavior_type']
            if b_type in types_count:
                types_count[b_type] += cluster['user_count']
            else:
                types_count[b_type] = cluster['user_count']
        
        # 找出最大的两个用户群体类型
        if types_count:
            sorted_types = sorted(types_count.items(), key=lambda x: x[1], reverse=True)
            top_types = sorted_types[:min(2, len(sorted_types))]
            
            behavior_desc = {
                'high_value': '高价值',
                'potential': '潜力型',
                'active_browser': '活跃浏览',
                'cart_abandoner': '购物车弃用',
                'at_risk': '流失风险'
            }
            
            if len(top_types) >= 1:
                top_type = top_types[0][0]
                top_count = top_types[0][1]
                suggestions.append(f"平台用户中{behavior_desc.get(top_type, top_type)}类型占比最高({top_count}人)，建议重点优化此类用户的购物体验。")
            
            if len(top_types) >= 2:
                second_type = top_types[1][0]
                second_count = top_types[1][1]
                suggestions.append(f"针对{behavior_desc.get(second_type, second_type)}类型用户({second_count}人)进行专项营销活动，提升转化率。")
        
        # 添加一些更有针对性的通用建议
        avg_view_cart_ratio = sum(c['avg_cart'] / max(c['avg_view'], 1) for c in cluster_analysis) / len(cluster_analysis)
        avg_cart_purchase_ratio = sum(c['avg_purchase'] / max(c['avg_cart'], 1) for c in cluster_analysis) / len(cluster_analysis)
        
        if avg_view_cart_ratio < 0.3:
            suggestions.append("全站浏览到加购转化率较低，建议优化商品展示页面和价格策略，增加加购率。")
        
        if avg_cart_purchase_ratio < 0.3:
            suggestions.append("购物车到下单转化率低，建议简化结账流程，提供结账优惠，优化支付体验。")
        
        return suggestions
    
    def _predict_purchase_intention(self, lgb_model, X):
        """预测未来购买意向"""
        if lgb_model is None or X is None:
            return {'likely_to_purchase': 45, 'unlikely_to_purchase': 55}
        
        try:
            # 预测购买概率
            purchase_probs = lgb_model.predict(X)
            
            # 计算有购买意向的用户比例
            likely_percent = (purchase_probs > 0.5).mean() * 100
            unlikely_percent = 100 - likely_percent
            
            return {
                'likely_to_purchase': round(likely_percent),
                'unlikely_to_purchase': round(unlikely_percent)
            }
            
        except Exception as e:
            print(f"预测购买意向出错: {e}")
            traceback.print_exc()
            return {'likely_to_purchase': 45, 'unlikely_to_purchase': 55}
    
    def analyze(self, user_data):
        """分析用户行为数据"""
        try:
            # 准备特征
            X, y, df = self._prepare_features(user_data)
            
            if X is None or len(X) < 5:
                # 返回默认数据
                return {
                    'error': '没有足够的用户行为数据',
                    'clusters': [
                        {'id': 1, 'behavior_type': 'high_value', 'user_count': 0},
                        {'id': 2, 'behavior_type': 'potential', 'user_count': 0}
                    ],
                    'user_points': [],
                    'total_users': 0,
                    'avg_purchase_intention': 0,
                    'model_accuracy': 0,
                    'auc': 0,
                    'second_model': 'KMeans',
                    'purchase_prediction': {'likely_to_purchase': 45, 'unlikely_to_purchase': 55},
                    'marketing_suggestions': ['暂无足够数据进行分析，建议收集更多用户行为数据']
                }
            
            # 1. 训练LightGBM模型预测购买意向
            self.lgb_model, accuracy, auc = self._train_lightgbm(X, y)
            
            # 2. 使用KMeans进行用户分群
            self.kmeans_model, cluster_analysis = self._cluster_users(X, df)
            
            # 3. 生成用户聚类散点图数据
            user_points = self._generate_user_points(X, df['cluster'].values, df)
            
            # 4. 预测未来购买意向
            purchase_prediction = self._predict_purchase_intention(self.lgb_model, X)
            
            # 5. 生成营销策略建议
            marketing_suggestions = self._generate_marketing_suggestions(cluster_analysis)
            
            # 6. 整合分析结果
            result = {
                'clusters': cluster_analysis,
                'user_points': user_points,
                'total_users': len(df),
                'avg_purchase_intention': float(df['purchase_probability'].mean()),
                'model_accuracy': float(accuracy),
                'auc': float(auc),
                'second_model': 'KMeans',  # 第二种算法
                'purchase_prediction': purchase_prediction,
                'marketing_suggestions': marketing_suggestions
            }
            
            return result
            
        except Exception as e:
            print(f"用户行为分析出错: {e}")
            traceback.print_exc()
            # 返回默认数据
            return {
                'error': str(e),
                'clusters': [
                    {'id': 1, 'behavior_type': 'high_value', 'user_count': 0},
                    {'id': 2, 'behavior_type': 'potential', 'user_count': 0}
                ],
                'user_points': [],
                'total_users': 0,
                'avg_purchase_intention': 0,
                'model_accuracy': 0,
                'auc': 0,
                'second_model': 'KMeans',
                'purchase_prediction': {'likely_to_purchase': 45, 'unlikely_to_purchase': 55},
                'marketing_suggestions': ['分析过程中发生错误，请稍后再试']
            }

# 测试代码
if __name__ == "__main__":
    # 创建一些测试数据
    test_data = []
    for i in range(20):
        test_data.append({
            'user_id': i,
            'user_name': f'用户{i}',
            'view_count': random.randint(5, 100),
            'search_count': random.randint(2, 30),
            'cart_count': random.randint(0, 20),
            'purchase_count': random.randint(0, 10),
            'unique_products': random.randint(5, 30),
            'activity_days': random.randint(1, 30),
            'last_activity': (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d'),
            'order_count': random.randint(0, 8),
            'total_amount': random.uniform(0, 5000),
            'last_order': (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d') if random.random() > 0.3 else None,
            'days_since_last_activity': random.randint(0, 60)
        })
    
    # 测试分析
    analyzer = UserBehaviorAnalysis()
    result = analyzer.analyze(test_data)
    print("用户分析结果:", result) 