import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pymysql
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import traceback
from decimal import Decimal

class SalesPredictionModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.features = None
        
    def connect_db(self):
        """连接数据库"""
        try:
            conn = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                passwd='123456',
                db='new_retail',
                charset='utf8mb4',
                connect_timeout=10
            )
            return conn
        except Exception as e:
            print(f"数据库连接失败: {e}")
            traceback.print_exc()
            return None
    
    def get_historical_data(self, days=90):
        """获取历史销售数据"""
        conn = None
        cursor = None
        try:
            conn = self.connect_db()
            if not conn:
                print("数据库连接失败")
                return None
                
            cursor = conn.cursor()
            
            # 查询最近90天的销售数据
            sql = """
            SELECT 
                DATE(create_time) as order_date,
                COUNT(*) as order_count,
                SUM(payment_amount) as total_amount
            FROM 
                sales_order
            GROUP BY 
                DATE(create_time)
            ORDER BY 
                order_date
            """
            
            cursor.execute(sql,)
            results = cursor.fetchall()
            
            if not results:
                print("没有找到历史销售数据")
                return None
            
            # 创建DataFrame
            df = pd.DataFrame(results, columns=['date', 'order_count', 'total_amount'])
            df['date'] = pd.to_datetime(df['date'])
            
            # 确保数据连续，填充缺失日期
            date_range = pd.date_range(start=df['date'].min(), end=df['date'].max())
            df = df.set_index('date').reindex(date_range).reset_index()
            df = df.rename(columns={'index': 'date'})
            
            # 填充缺失值
            df['order_count'] = df['order_count'].fillna(0)
            df['total_amount'] = df['total_amount'].fillna(0)
            
            # 将Decimal类型转换为float，避免类型不匹配问题
            df['total_amount'] = df['total_amount'].astype(float)
            
            return df
            
        except Exception as e:
            print(f"获取历史销售数据出错: {e}")
            traceback.print_exc()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def prepare_features(self, df):
        """准备特征数据"""
        if df is None or len(df) < 14:  # 至少需要两周的数据
            return None, None
        
        # 创建时间特征
        df['dayofweek'] = df['date'].dt.dayofweek  # 周几 (0-6)
        df['month'] = df['date'].dt.month  # 月份 (1-12)
        df['day'] = df['date'].dt.day  # 日期 (1-31)
        df['is_weekend'] = df['dayofweek'].apply(lambda x: 1 if x >= 5 else 0)  # 是否周末
        
        # 创建滞后特征 (前7天的销售额)
        for i in range(1, 8):
            df[f'lag_{i}'] = df['total_amount'].shift(i)
        
        # 创建滚动平均特征
        df['rolling_mean_7'] = df['total_amount'].rolling(window=7).mean()  # 7天滚动平均
        df['rolling_mean_14'] = df['total_amount'].rolling(window=14).mean()  # 14天滚动平均
        
        # 丢弃有NaN的行
        df = df.dropna()
        
        # 分离特征和目标
        features = ['dayofweek', 'month', 'day', 'is_weekend', 
                   'lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_5', 'lag_6', 'lag_7',
                   'rolling_mean_7', 'rolling_mean_14']
        
        X = df[features]
        y = df['total_amount']
        
        self.features = features
        
        return X, y
    
    def train_model(self, model_type='random_forest'):
        """训练预测模型"""
        try:
            # 获取历史数据
            df = self.get_historical_data(days=90)
            if df is None:
                return False, "无法获取足够的历史数据"
            
            # 准备特征
            X, y = self.prepare_features(df)
            if X is None:
                return False, "无法准备足够的特征数据"
            
            # 标准化特征
            X_scaled = self.scaler.fit_transform(X)
            
            # 选择模型
            if model_type == 'linear':
                self.model = LinearRegression()
            else:  # 默认使用随机森林
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # 训练模型
            self.model.fit(X_scaled, y)
            
            # 评估模型
            y_pred = self.model.predict(X_scaled)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            print(f"模型训练完成: MSE={mse:.2f}, R^2={r2:.2f}")
            
            return True, {"mse": mse, "r2": r2}
            
        except Exception as e:
            print(f"模型训练出错: {e}")
            traceback.print_exc()
            return False, str(e)
    
    def predict_future_sales(self, days=30):
        """预测未来销售额"""
        try:
            if self.model is None:
                success, result = self.train_model()
                if not success:
                    return None, result
            
            # 获取历史数据
            df = self.get_historical_data(days=90)
            if df is None:
                return None, "无法获取足够的历史数据"
            
            # 准备特征
            _, _ = self.prepare_features(df)
            
            # 最后一天的日期
            last_date = df['date'].max()
            
            # 创建未来日期的DataFrame
            future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
            future_df = pd.DataFrame({'date': future_dates})
            
            # 复制最后一行的数据作为初始预测基础
            last_row = df.iloc[-1:].copy()
            
            # 预测结果列表
            predictions = []
            
            # 逐天预测
            for i, future_date in enumerate(future_dates):
                # 创建新行
                new_row = last_row.copy()
                new_row['date'] = future_date
                
                # 更新时间特征
                new_row['dayofweek'] = future_date.dayofweek
                new_row['month'] = future_date.month
                new_row['day'] = future_date.day
                new_row['is_weekend'] = 1 if future_date.dayofweek >= 5 else 0
                
                # 如果是第一天预测，使用历史数据的滞后值
                if i == 0:
                    for j in range(1, 8):
                        new_row[f'lag_{j}'] = float(df['total_amount'].iloc[-(j+1)]) if j <= len(df) else 0.0
                else:
                    # 更新滞后特征
                    for j in range(1, 8):
                        if j <= i:
                            new_row[f'lag_{j}'] = float(predictions[i-j])
                        else:
                            new_row[f'lag_{j}'] = float(df['total_amount'].iloc[-(j-i)]) if (j-i) <= len(df) else 0.0
                
                # 更新滚动平均 - 确保所有值都是float类型
                if i < 7:
                    recent_values = [float(val) for val in df['total_amount'].iloc[-7+i:]] + [float(val) for val in predictions[:i]]
                    new_row['rolling_mean_7'] = sum(recent_values) / len(recent_values)
                else:
                    new_row['rolling_mean_7'] = sum([float(val) for val in predictions[i-7:i]]) / 7
                
                if i < 14:
                    recent_values = [float(val) for val in df['total_amount'].iloc[-14+i:]] + [float(val) for val in predictions[:i]]
                    new_row['rolling_mean_14'] = sum(recent_values) / len(recent_values)
                else:
                    new_row['rolling_mean_14'] = sum([float(val) for val in predictions[i-14:i]]) / 14
                
                # 提取特征并预测
                X_pred = new_row[self.features]
                X_pred_scaled = self.scaler.transform(X_pred)
                prediction = self.model.predict(X_pred_scaled)[0]
                
                # 确保预测值为正
                prediction = max(0, prediction)
                
                # 添加到预测列表
                predictions.append(prediction)
                
                # 更新最后一行
                last_row = new_row.copy()
                last_row['total_amount'] = prediction
            
            # 创建结果DataFrame
            result_df = pd.DataFrame({
                'date': future_dates,
                'predicted_amount': predictions
            })
            
            # 计算预测总额和增长率
            historical_total = float(df['total_amount'].sum())
            predicted_total = float(sum(predictions))
            
            # 计算同期增长率
            if len(df) >= days:
                previous_period = float(df['total_amount'].iloc[-days:].sum())
                growth_rate = ((predicted_total - previous_period) / previous_period * 100) if previous_period > 0 else 0
            else:
                growth_rate = 0
            
            # 评估模型
            X, y = self.prepare_features(df)
            X_scaled = self.scaler.transform(X)
            y_pred = self.model.predict(X_scaled)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            # 准备返回数据
            historical_data = df[['date', 'total_amount']].values.tolist()
            prediction_data = result_df[['date', 'predicted_amount']].values.tolist()
            
            # 合并历史数据和预测数据
            all_dates = [d[0].strftime('%m-%d') for d in historical_data] + [d[0].strftime('%m-%d') for d in prediction_data]
            all_values = [float(d[1]) for d in historical_data] + [None] * len(prediction_data)
            predicted_values = [None] * len(historical_data) + [float(d[1]) for d in prediction_data]
            
            # 生成预测结论
            if growth_rate > 10:
                conclusion = "预测未来30天销售额将显著增长，建议增加库存和营销投入。"
            elif growth_rate > 0:
                conclusion = "预测未来30天销售额将稳定增长，建议维持当前经营策略。"
            elif growth_rate > -10:
                conclusion = "预测未来30天销售额将略有下降，建议适当调整促销策略。"
            else:
                conclusion = "预测未来30天销售额将显著下降，建议加大促销力度并分析下降原因。"
            
            # 修复准确率计算方法，使用R²分数作为基础，确保准确率在0-100%之间
            accuracy = round(max(0, min(100, 100 * r2)), 2) if r2 > 0 else round(max(0, min(100, 100 * (1 - mse / (df['total_amount'].max() - df['total_amount'].min())**2))), 2)
            
            return {
                'dates': all_dates,
                'historical': all_values,
                'predicted': predicted_values,
                'prediction_start_index': len(historical_data),
                'model_type': 'Random Forest' if isinstance(self.model, RandomForestRegressor) else 'Linear Regression',
                'accuracy': accuracy,  # 使用修复后的准确率
                'mse': round(mse, 2),
                'r2_score': round(r2, 2),
                'growth_rate': round(growth_rate, 2),
                'predicted_total': round(predicted_total, 2),
                'conclusion': conclusion
            }, None
            
        except Exception as e:
            print(f"预测未来销售额出错: {e}")
            traceback.print_exc()
            return None, str(e)

# 测试代码
if __name__ == "__main__":
    model = SalesPredictionModel()
    success, result = model.train_model()
    if success:
        predictions, error = model.predict_future_sales(days=30)
        if predictions:
            print("预测成功!")
            print(f"预测增长率: {predictions['growth_rate']}%")
            print(f"预测总额: {predictions['predicted_total']}")
        else:
            print(f"预测失败: {error}")
    else:
        print(f"模型训练失败: {result}") 