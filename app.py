from flask import Flask, render_template, request, redirect, url_for, session, jsonify
# from Controller.dapin import *
# from Controller.admin import *
from Controller.UserAPI import *
from Controller.DataAnalysisApi import data_analysis_api
from Controller.UserBehaviorPreferenceApi import behavior_preference_api
from Controller.ReportExportApi import report_export_api
# from Controller.data import *
# from Controller.postspl import *
from flask_cors import CORS
import traceback
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key-123'  # 添加secret key
# app.register_blueprint(dapin_api, url_prefix='/dapin')
# app.register_blueprint(data_api, url_prefix='/data')
app.register_blueprint(user_api, url_prefix='/user')
# app.register_blueprint(admin_api, url_prefix='/admin')
# app.register_blueprint(sql_api, url_prefix='/sql')
app.register_blueprint(data_analysis_api, url_prefix='/api/data_analysis')
app.register_blueprint(behavior_preference_api, url_prefix='/api/behavior_analysis')
app.register_blueprint(report_export_api, url_prefix='/api/report')



@app.route('/')
def hello_world():  # put application's code here
    return render_template("login.html")

@app.route('/Signup')
def Login():  # put application's code here
    return render_template("signup.html")

@app.route('/home')
def home():
    # 从 session 或其他地方获取用户名
    username = session.get('username', '用户')  
    return render_template('Home.html', username=username)

@app.route('/admin')
def Admin():  # put application's code here
    return render_template("adminlist.html")

@app.route('/User')
def User():  # put application's code here
    return render_template("userlist.html")

@app.route('/logout')
def logout():
    try:
        # 清除所有会话数据
        session.clear()
        # 设置响应对象，重定向到登录页面
        response = redirect(url_for('hello_world'))
        # 清除所有相关的Cookie
        response.set_cookie('userId', '', expires=0)  # 添加清除userId
        response.set_cookie('username', '', expires=0)
        response.set_cookie('role', '', expires=0)
        return response
    except Exception as e:
        print(f"Logout error: {str(e)}")  # 添加错误日志
        return redirect(url_for('hello_world'))


@app.route('/DataAnalysis')
def DataAnalysis():  # put application's code here
    return render_template("DataAnalysis.html")

@app.route('/AdvancedAnalysis')
def AdvancedAnalysis():
    return render_template("AdvancedAnalysis.html")

@app.route('/SalesPrediction')
def SalesPrediction():
    return render_template("SalesPrediction.html")

@app.route('/BehaviorAnalysis')
def BehaviorAnalysis():
    return render_template("BehaviorAnalysis.html")

@app.route('/Screen')
def Screen():  # put application's code here
    return render_template("Screen.html")

# 数据分析API路由已移至Controller/DataAnalysisApi.py

if __name__ == '__main__':
    app.run(debug=True)

