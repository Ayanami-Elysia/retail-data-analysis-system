import requests

def test_sales_prediction():
    try:
        print("测试销售预测API...")
        response = requests.get('http://localhost:5000/api/data_analysis/sales_prediction')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"数据键: {list(data.keys())}")
            print(f"准确率: {data.get('accuracy')}")
            print(f"增长率: {data.get('growth_rate')}%")
            print(f"预测总额: {data.get('predicted_total')}")
            print(f"结论: {data.get('conclusion')}")
            print(f"历史数据点数: {len([x for x in data.get('historical', []) if x is not None])}")
            print(f"预测数据点数: {len([x for x in data.get('predicted', []) if x is not None])}")
            return True
        else:
            print(f"API请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"测试出错: {e}")
        return False

if __name__ == "__main__":
    test_sales_prediction()
