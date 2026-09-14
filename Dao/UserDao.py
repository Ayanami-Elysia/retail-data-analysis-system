import pymysql


# 数据库连接
def get_connection():
    return pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='new_retail')


# 管理员登陆
def loginDao(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 使用参数化查询防止SQL注入
        sql = 'SELECT * FROM `py_user` WHERE username = %s AND password = %s AND role = %s'
        cursor.execute(sql, (username, password, role))
        res = cursor.fetchall()
        return res
    except Exception as e:
        print(f"登录查询失败: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()


# 注册检测
def GetuserDao(username):
    conn = get_connection()
    cursor2 = conn.cursor()
    cursor2.execute('select * from `py_user` where username = %s ', (username))
    res = cursor2.fetchall()
    conn.commit()
    conn.close()
    return res


# 查询列表
def ListDao(username=None, page=1, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    offset = (page - 1) * limit

    try:
        # 构建基础查询
        base_query = "SELECT * FROM py_user WHERE role = 'user'"
        count_query = "SELECT COUNT(*) FROM py_user WHERE role = 'user'"

        params = []

        # 添加搜索条件
        if username and username.strip():
            base_query += " AND username LIKE %s"
            count_query += " AND username LIKE %s"
            params.append(f"%{username.strip()}%")

        # 获取总记录数
        if params:
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        total = cursor.fetchone()[0]

        # 添加排序和分页
        base_query += " ORDER BY id DESC LIMIT %s, %s"
        if params:
            params.extend([offset, limit])
            cursor.execute(base_query, params)
        else:
            cursor.execute(base_query, (offset, limit))

        data = cursor.fetchall()

        return {
            "total": total,
            "data": data,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        print(f"查询用户列表失败: {str(e)}")
        return {
            "total": 0,
            "data": [],
            "page": page,
            "limit": limit
        }
    finally:
        cursor.close()
        conn.close()


# 删除用户
def DeleteUserDao(id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "delete from py_user where id = %s"
    cursor.execute(sql, (id,))
    conn.commit()
    conn.close()
    return True


# 新增用户
def AddUserDao(username, password, nickname, sex, age, phone, email, birthday, card, content, remarks):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """insert into py_user(username, password, nickname, sex, age, phone, email, birthday, card, content, remarks,role) 
            values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,'user')"""
    cursor.execute(sql, (username, password, nickname, sex, age, phone, email, birthday, card, content, remarks))
    conn.commit()
    conn.close()
    return True


def get_user_by_id(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM py_user WHERE id = %s"
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        print(f"获取用户信息失败: {str(e)}")
        return None


def update_user(user_id, username, password, nickname, sex, age, phone, email):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """UPDATE py_user SET username=%s, nickname=%s, 
                    sex=%s, age=%s, phone=%s, email=%s WHERE id=%s"""
        cursor.execute(sql, (username, nickname, sex, age, phone, email, user_id))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"更新用户信息失败: {str(e)}")
        return False


# 查询管理员列表
def ListAdminDao(username=None, page=1, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    offset = (page - 1) * limit

    try:
        # 构建基础查询
        base_query = "SELECT * FROM py_user WHERE role = 'admin'"
        count_query = "SELECT COUNT(*) FROM py_user WHERE role = 'admin'"

        params = []

        # 添加搜索条件
        if username and username.strip():
            base_query += " AND username LIKE %s"
            count_query += " AND username LIKE %s"
            params.append(f"%{username.strip()}%")

        # 获取总记录数
        if params:
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        total = cursor.fetchone()[0]

        # 添加排序和分页
        base_query += " ORDER BY id DESC LIMIT %s, %s"
        if params:
            params.extend([offset, limit])
            cursor.execute(base_query, params)
        else:
            cursor.execute(base_query, (offset, limit))

        data = cursor.fetchall()

        return {
            "total": total,
            "data": data,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        print(f"查询管理员列表失败: {str(e)}")
        return {
            "total": 0,
            "data": [],
            "page": page,
            "limit": limit
        }
    finally:
        cursor.close()
        conn.close()


def AddAdminDao(username, password, nickname, sex, age, phone, email, birthday, card, content, remarks):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """insert into py_user(username, password, nickname, sex, age, phone, email, birthday, card, content, remarks,role) 
            values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,'admin')"""
    cursor.execute(sql, (username, password, nickname, sex, age, phone, email, birthday, card, content, remarks))
    conn.commit()
    conn.close()
    return True


class UserDao:
    @staticmethod
    def check_username_exists(username):
        conn = get_connection()
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM py_user WHERE username = %s"
        cursor.execute(sql, (username,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0

    @staticmethod
    def create_user(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            sql = """INSERT INTO py_user 
                    (username, password, role) 
                    VALUES (%s, %s, 'user')"""
            cursor.execute(sql, (username, password))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"创建用户失败: {e}")
            conn.rollback()
            cursor.close()
            conn.close()
            return False


def GetUserByIdDao(id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT * FROM py_user WHERE id = %s"
        cursor.execute(sql, (id,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"获取用户失败: {e}")
        return None
    finally:
        cursor.close()
        conn.close()