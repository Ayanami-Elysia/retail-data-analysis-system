from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from Dao.UserDao import *
import pymysql
from werkzeug.security import generate_password_hash

# from urllib import request
from flask import Blueprint, jsonify, request

user_api = Blueprint('user_api', __name__)

# 添加 secret key
user_api.secret_key = 'your_secret_key_here'  # 建议使用随机生成的复杂字符串

conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='new_retail')


@user_api.route('/loginApi', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    res = loginDao(username, password, role)

    if res and len(res) > 0:
        user = res[0]
        body = {
            'id': user[0],
            'username': user[1],
            'password': user[2],
            'nickname': user[3],
            'sex': user[4],
            'age': user[5],
            'phone': user[6],
            'email': user[7],
            'birthday': user[8],
            'card': user[9],
            'content': user[10],
            'remarks': user[11],
            'role': user[12],  # 直接使用数据库中存储的角色
            'token': str(user[0])
        }
        data = {
            'msg': '登录成功',
            'data': body,
            'code': 200
        }
        return jsonify(data)
    else:
        data = {
            'msg': '账号或密码不正确',
            'code': 200
        }
        return jsonify(data)

    return jsonify({
        'msg': '接口报错',
        'code': 500
    })


@user_api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([username, password, confirm_password]):
        return jsonify({
            'code': 400,
            'msg': '请填写所有必填字段'
        })

    if password != confirm_password:
        return jsonify({
            'code': 400,
            'msg': '两次输入的密码不一致'
        })

    # 检查用户名是否已存在
    if UserDao.check_username_exists(username):
        return jsonify({
            'code': 400,
            'msg': '该用户名已被注册'
        })

    # 创建新用户
    if UserDao.create_user(username, password):
        return jsonify({
            'code': 200,
            'msg': '注册成功'
        })
    else:
        return jsonify({
            'code': 500,
            'msg': '注册失败，请重试'
        })


@user_api.route('/userlist', methods=['POST'])
def getuserlist():
    try:
        data = request.get_json()
        username = data.get('username')
        page = int(data.get('page', 1))
        limit = int(data.get('limit', 20))  # 默认每页显示20条

        result = ListDao(username=username, page=page, limit=limit)
        datalist = []
        for user in result['data']:
            body = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'nickname': user[3],
                'sex': user[4],
                'age': user[5],
                'phone': user[6],
                'email': user[7],
                'brithday': user[8],
                'card': user[9],
                'content': user[10],
                'remarks': user[11],
                'role': user[12],
                'token': user[0]
            }
            datalist.append(body)

        return jsonify({
            'msg': '查询成功',
            'data': datalist,
            'total': result['total'],
            'page': page,
            'limit': limit,
            'pages': (result['total'] + limit - 1) // limit,
            'code': 200
        })
    except Exception as e:
        return jsonify({
            'msg': f'查询失败：{str(e)}',
            'code': 500
        })


@user_api.route('/delete/<int:id>', methods=['POST'])
def delete_user(id):
    try:
        DeleteUserDao(id)
        return jsonify({
            'msg': '删除成功',
            'code': 200
        })
    except Exception as e:
        return jsonify({
            'msg': '删除失败',
            'code': 500
        })


@user_api.route('/add', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        nickname = data.get('nickname')
        sex = data.get('sex')
        age = data.get('age')
        phone = data.get('phone')
        email = data.get('email')
        birthday = data.get('birthday')
        card = data.get('card')
        content = data.get('content')
        remarks = data.get('remarks')

        AddUserDao(username, password, nickname, sex, age, phone, email, birthday, card, content, remarks)
        return jsonify({
            'msg': '添加成功',
            'code': 200
        })
    except Exception as e:
        return jsonify({
            'msg': '添加失败',
            'code': 500
        })


@user_api.route('/edit', methods=['POST'])
def edit_user():
    data = request.get_json()
    try:
        user_id = data.get('id')
        username = data.get('username')
        password = data.get('password')
        nickname = data.get('nickname')
        sex = data.get('sex')
        age = data.get('age')
        phone = data.get('phone')
        email = data.get('email')

        # 更新用户信息
        success = update_user(user_id, username, password, nickname, sex, age, phone, email)

        if success:
            return jsonify({"code": 200, "message": "更新成功"})
        else:
            return jsonify({"code": 500, "message": "更新失败"})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})


@user_api.route('/adminlist', methods=['POST'])
def getadminlist():
    try:
        data = request.get_json()
        username = data.get('username')
        page = int(data.get('page', 1))
        limit = int(data.get('limit', 20))  # 默认每页显示20条

        result = ListAdminDao(username=username, page=page, limit=limit)
        datalist = []
        for user in result['data']:
            body = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'nickname': user[3],
                'sex': user[4],
                'age': user[5],
                'phone': user[6],
                'email': user[7],
                'brithday': user[8],
                'card': user[9],
                'content': user[10],
                'remarks': user[11],
                'role': user[12],
                'token': user[0]
            }
            datalist.append(body)

        return jsonify({
            'msg': '查询成功',
            'data': datalist,
            'total': result['total'],
            'page': page,
            'limit': limit,
            'pages': (result['total'] + limit - 1) // limit,
            'code': 200
        })
    except Exception as e:
        return jsonify({
            'msg': f'查询失败：{str(e)}',
            'code': 500
        })


@user_api.route('/addadmin', methods=['POST'])
def add_admin():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        nickname = data.get('nickname')
        sex = data.get('sex')
        age = data.get('age')
        phone = data.get('phone')
        email = data.get('email')
        birthday = data.get('birthday')
        card = data.get('card')
        content = data.get('content')
        remarks = data.get('remarks')

        AddAdminDao(username, password, nickname, sex, age, phone, email, birthday, card, content, remarks)
        return jsonify({
            'msg': '添加成功',
            'code': 200
        })
    except Exception as e:
        return jsonify({
            'msg': '添加失败',
            'code': 500
        })


@user_api.route('/get/<int:id>', methods=['GET'])
def get_user(id):
    try:
        user = GetUserByIdDao(id)
        if user:
            data = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'nickname': user[3],
                'sex': user[4],
                'age': user[5],
                'phone': user[6],
                'email': user[7],
                'brithday': user[8],
                'card': user[9],
                'content': user[10],
                'remarks': user[11],
                'role': user[12]
            }
            return jsonify({
                'code': 200,
                'msg': '获取成功',
                'data': data
            })
        else:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取失败: {str(e)}'
        })