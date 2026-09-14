import os
import random
from datetime import datetime, timedelta
from faker import Faker
import findspark
from pyspark.sql import SparkSession
from pyspark.sql.types import *
import pymysql
from decimal import Decimal

# 创建Faker实例，使用中文
fake = Faker(['zh_CN'])

def create_spark_session():
    """创建SparkSession"""
    # 设置Hadoop环境变量
    os.environ['HADOOP_HOME'] = r"C:\Program Files\Hadoop"
    os.environ['PATH'] = os.environ['PATH'] + r";C:\Program Files\Hadoop\bin"
    
    # 初始化findspark
    findspark.init()
    
    return SparkSession.builder \
        .appName("NewRetailDataCreation") \
        .config("spark.jars", "mysql-connector-java-5.1.49.jar") \
        .config("spark.driver.extraClassPath", "mysql-connector-java-5.1.49.jar") \
        .config("spark.executor.extraClassPath", "mysql-connector-java-5.1.49.jar") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

def connect_db():
    """连接数据库"""
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='123456',
        db='new_retail'
    )

def create_base_data():
    """创建基础数据"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 清理旧数据（按照依赖关系的反序删除）
        print("清理旧数据...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        tables = [
            'sales_detail', 'sales_order', 'user_behavior', 'product_inventory',
            'user_address', 'product', 'product_category', 'supplier',
            'store', 'sales_channel', 'marketing_campaign', 'member_level'
        ]
        
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table}")
            print(f"已清理表 {table}")
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("旧数据清理完成")
        
        # 1. 创建会员等级
        print("创建会员等级数据...")
        member_levels = [
            ('普通会员', 0, 1000, 1.00, '新注册会员的默认等级'),
            ('银卡会员', 1001, 5000, 0.98, '享受98折优惠'),
            ('金卡会员', 5001, 20000, 0.95, '享受95折优惠'),
            ('钻石会员', 20001, 50000, 0.90, '享受9折优惠'),
            ('至尊会员', 50001, 999999, 0.85, '享受85折优惠及专属服务')
        ]
        
        for level in member_levels:
            cursor.execute("""
                INSERT INTO member_level (level_name, min_points, max_points, discount, description)
                VALUES (%s, %s, %s, %s, %s)
            """, level)
        
        # 2. 创建销售渠道
        print("创建销售渠道数据...")
        channels = [
            ('官方网站', 'online', 'WEB001', '公司官方网站销售', 5.00),
            ('移动APP', 'online', 'APP001', '移动应用程序销售', 3.00),
            ('微信小程序', 'online', 'WX001', '微信平台销售', 2.50),
            ('实体门店', 'offline', 'OFF001', '线下门店销售', 0.00),
            ('电话订购', 'offline', 'TEL001', '电话预订配送', 1.00)
        ]
        
        for channel in channels:
            cursor.execute("""
                INSERT INTO sales_channel (channel_name, channel_type, channel_code, 
                                         description, commission_rate)
                VALUES (%s, %s, %s, %s, %s)
            """, channel)
        
        # 3. 创建商品分类
        print("创建商品分类数据...")
        main_categories = [
            ('手机数码', 0, 1),
            ('电脑办公', 0, 1),
            ('家用电器', 0, 1),
            ('服装鞋包', 0, 1),
            ('食品生鲜', 0, 1)
        ]
        
        for category in main_categories:
            cursor.execute("""
                INSERT INTO product_category (category_name, parent_id, level)
                VALUES (%s, %s, %s)
            """, category)
            
        # 4. 创建供应商数据
        print("创建供应商数据...")
        suppliers = [
            ('华为技术有限公司', '张三', '13800138001', '深圳市龙岗区坂田华为基地', 'huawei@example.com'),
            ('小米科技有限公司', '李四', '13800138002', '北京市海淀区西二旗小米科技园', 'xiaomi@example.com'),
            ('苹果贸易（中国）有限公司', '王五', '13800138003', '北京市朝阳区建国门外大街', 'apple@example.com'),
            ('三星（中国）投资有限公司', '赵六', '13800138004', '北京市朝阳区三星大厦', 'samsung@example.com'),
            ('联想（北京）有限公司', '钱七', '13800138005', '北京市海淀区联想研究院', 'lenovo@example.com')
        ]
        
        for supplier in suppliers:
            cursor.execute("""
                INSERT INTO supplier (supplier_name, contact_person, contact_phone, address, email)
                VALUES (%s, %s, %s, %s, %s)
            """, supplier)
            
        # 5. 创建门店数据
        print("创建门店数据...")
        stores = [
            ('北京中关村旗舰店', 'BJ001', '北京市海淀区中关村大街1号', '张店长', '010-88888888', '09:00-22:00'),
            ('上海南京路店', 'SH001', '上海市黄浦区南京东路1号', '李店长', '021-88888888', '09:00-22:00'),
            ('广州天河城店', 'GZ001', '广州市天河区天河路208号', '王店长', '020-88888888', '09:00-22:00'),
            ('深圳华强北店', 'SZ001', '深圳市福田区华强北路1号', '赵店长', '0755-88888888', '09:00-22:00'),
            ('成都春熙路店', 'CD001', '成都市锦江区春熙路1号', '钱店长', '028-88888888', '09:00-22:00')
        ]
        
        for store in stores:
            cursor.execute("""
                INSERT INTO store (store_name, store_code, address, manager, phone, business_hours)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, store)
            
        # 6. 创建营销活动数据
        print("创建营销活动数据...")
        current_time = datetime.now()
        campaigns = [
            ('618大促', 'discount', current_time - timedelta(days=10), current_time + timedelta(days=20), 0.8, 0, 100, 'all', 'all', 'all'),
            ('新人专享', 'coupon', current_time - timedelta(days=30), current_time + timedelta(days=30), None, 50, 0, 'online', 'all', 'new'),
            ('会员日特惠', 'discount', current_time - timedelta(days=5), current_time + timedelta(days=1), 0.9, 0, 200, 'all', 'all', 'vip'),
            ('限时秒杀', 'flash_sale', current_time, current_time + timedelta(days=3), 0.7, 0, 0, 'online', 'category', 'all'),
            ('店庆活动', 'gift', current_time - timedelta(days=15), current_time + timedelta(days=15), None, 0, 500, 'offline', 'all', 'all')
        ]
        
        for campaign in campaigns:
            cursor.execute("""
                INSERT INTO marketing_campaign (campaign_name, campaign_type, start_time, end_time,
                    discount_rate, discount_amount, min_order_amount, channel_scope,
                    product_scope, user_scope)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, campaign)
        
        conn.commit()
        print("基础数据创建完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"创建基础数据时发生错误: {e}")
    finally:
        cursor.close()
        conn.close()

def generate_user_data(spark, count=1000):
    """生成更真实的用户数据"""
    print(f"开始生成{count}个用户数据...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 清理用户表和地址表
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE py_user")
        cursor.execute("TRUNCATE TABLE user_address")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 首先创建管理员账号
        cursor.execute("""
            INSERT INTO py_user (username, password, nickname, sex, age, phone, 
                email, birthday, card, content, remarks, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'admin',  # username
            '123456',  # password
            '系统管理员',  # nickname
            '男',  # sex
            35,  # age
            '13888888888',  # phone
            'admin@example.com',  # email
            '1988-01-01',  # birthday
            '110101198801010001',  # card
            '系统管理员账号',  # content
            '系统默认创建',  # remarks
            'admin'  # role
        ))
        conn.commit()
        admin_id = cursor.lastrowid
        
        # 为管理员生成地址
        admin_addresses = [
            (admin_id, '系统管理员', '13888888888', '北京市', '北京市', '海淀区', 
             '北京市海淀区中关村科技园区1号楼', 1)
        ]
        cursor.executemany("""
            INSERT INTO user_address (user_id, receiver, phone, province, city, 
                district, detail_address, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, admin_addresses)
        conn.commit()
        
        # 生成普通用户数据
        fake = Faker(['zh_CN'])
        batch_size = 100
        
        # 预定义一些真实的手机号前缀
        phone_prefixes = ['133', '135', '136', '137', '138', '139', '150', '151', '152', 
                         '157', '158', '159', '182', '183', '187', '188', '189']
        
        for i in range(0, count-1, batch_size):  # count-1 因为已经创建了一个管理员
            batch_data = []
            for j in range(batch_size):
                if i + j >= count-1:
                    break
                
                gender = random.choice(['男', '女'])
                name = fake.name_male() if gender == '男' else fake.name_female()
                birth_date = fake.date_of_birth(minimum_age=18, maximum_age=70)
                age = datetime.now().year - birth_date.year
                
                # 生成更真实的用户名（使用拼音+数字的组合）
                username = f"{fake.romanized_name().lower().replace(' ', '')}{random.randint(100, 999)}"
                
                # 生成更真实的手机号
                phone = f"{random.choice(phone_prefixes)}{str(random.randint(10000000, 99999999))}"
                
                batch_data.append((
                    username,
                    "123456",  # password
                    name,  # nickname
                    gender,  # sex
                    age,  # age
                    phone,  # phone
                    f"{username}@{random.choice(['gmail.com', 'qq.com', '163.com', '126.com'])}",  # email
                    birth_date.strftime('%Y-%m-%d'),  # birthday
                    fake.ssn(),  # card
                    f"{name}的个人账号",  # content
                    None,  # remarks
                    'user'  # role 统一改为user
                ))
            
            # 插入用户数据并获取ID
            user_ids = []
            for user_data in batch_data:
                cursor.execute("""
                    INSERT INTO py_user (username, password, nickname, sex, age, phone, 
                        email, birthday, card, content, remarks, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, user_data)
                user_ids.append(cursor.lastrowid)
            
            conn.commit()
            print(f"已生成 {min(i + batch_size, count-1)} 个用户数据")
            
            # 为每个用户生成地址
            address_batch = []
            for user_id in user_ids:
                # 每个用户生成1-3个地址
                address_count = random.randint(1, 3)
                for addr_idx in range(address_count):
                    province = fake.province()
                    city = fake.city()
                    district = fake.district()
                    street = fake.street_name()
                    building = fake.building_number()
                    
                    address_batch.append((
                        user_id,
                        fake.name(),  # receiver
                        f"{random.choice(phone_prefixes)}{str(random.randint(10000000, 99999999))}",  # phone
                        province,
                        city,
                        district,
                        f"{province}{city}{district}{street}{building}号",  # detail_address
                        1 if addr_idx == 0 else 0  # 第一个地址默认
                    ))
            
            cursor.executemany("""
                INSERT INTO user_address (user_id, receiver, phone, province, city, 
                    district, detail_address, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, address_batch)
            conn.commit()
            
            print(f"已生成 {len(address_batch)} 个用户地址")
        
        print(f"用户数据生成完成，共生成{count}条记录（包含管理员）")
        
    except Exception as e:
        conn.rollback()
        print(f"生成用户数据时发生错误: {e}")
        raise e  # 重新抛出异常以便查看详细错误信息
    finally:
        cursor.close()
        conn.close()

def generate_user_address(cursor, user_id):
    """为用户生成地址数据"""
    fake = Faker(['zh_CN'])
    address_count = random.randint(1, 3)  # 每个用户1-3个地址
    addresses = []
    
    for i in range(address_count):
        province = fake.province()
        city = fake.city_name()
        district = fake.district()
        detail = fake.street_address()
        is_default = 1 if i == 0 else 0  # 第一个地址设为默认
        
        addresses.append((
            user_id,
            fake.name(),  # receiver
            fake.phone_number(),  # phone
            province,
            city,
            district,
            f"{province}{city}{district}{detail}",  # detail_address
            is_default
        ))
    
    return addresses

def generate_product_data(spark, count=500):
    """生成更真实的商品数据"""
    print(f"开始生成{count}个商品数据...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 清理商品表
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE product")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 获取分类和供应商信息
        cursor.execute("SELECT id FROM product_category")
        category_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM supplier")
        supplier_ids = [row[0] for row in cursor.fetchall()]
        
        # 预定义真实的商品数据
        product_templates = {
            '手机数码': {
                'brands': ['Apple', 'Samsung', 'Huawei', 'Xiaomi', 'OPPO', 'VIVO'],
                'names': ['手机', '平板电脑', '智能手表', '无线耳机', '充电器'],
                'models': ['Pro', 'Max', 'Ultra', 'Lite', 'Plus'],
                'price_range': (999, 9999)
            },
            '电脑办公': {
                'brands': ['Lenovo', 'Dell', 'HP', 'Asus', 'Acer'],
                'names': ['笔记本电脑', '台式电脑', '显示器', '打印机', '路由器'],
                'models': ['商务版', '游戏版', '专业版', '轻薄版', '旗舰版'],
                'price_range': (2999, 19999)
            },
            '家用电器': {
                'brands': ['海尔', '美的', '格力', '松下', '西门子'],
                'names': ['冰箱', '洗衣机', '空调', '电视', '微波炉'],
                'models': ['智能版', '节能版', '家用版', '豪华版', '经典版'],
                'price_range': (1999, 15999)
            }
        }
        
        batch_size = 50
        for i in range(0, count, batch_size):
            batch_data = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                
                category_id = random.choice(category_ids)
                cursor.execute("SELECT category_name FROM product_category WHERE id = %s", (category_id,))
                category_name = cursor.fetchone()[0]
                
                if category_name in product_templates:
                    template = product_templates[category_name]
                    brand = random.choice(template['brands'])
                    name = random.choice(template['names'])
                    model = random.choice(template['models'])
                    min_price, max_price = template['price_range']
                else:
                    # 其他分类的默认设置
                    brand = random.choice(['通用品牌A', '通用品牌B', '通用品牌C'])
                    name = f"商品{i+j+1}"
                    model = f"型号{i+j+1}"
                    min_price, max_price = (99, 999)
                
                price = round(random.uniform(min_price, max_price), 2)
                product_code = f"{category_name[:2]}{str(i+j+1).zfill(6)}"
                
                batch_data.append((
                    f"{brand} {name} {model}",  # product_name
                    product_code,
                    category_id,
                    random.choice(supplier_ids),  # supplier_id
                    brand,
                    model,
                    '台',  # unit
                    price,
                    round(price * 0.7, 2),  # cost_price
                    round(price * 1.2, 2),  # market_price
                    random.randint(100, 1000),  # stock
                    20,  # warning_stock
                    random.randint(0, 500),  # sales
                    random.randint(0, 1),  # is_new
                    random.randint(0, 1),  # is_hot
                    1,  # status
                    f"{brand}{name}{model}，采用最新技术，提供优质体验。"  # description
                ))
            
            cursor.executemany("""
                INSERT INTO product (product_name, product_code, category_id, supplier_id,
                    brand, model, unit, price, cost_price, market_price, stock,
                    warning_stock, sales, is_new, is_hot, status, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch_data)
            
            conn.commit()
            print(f"已生成 {min(i + batch_size, count)} 个商品数据")
        
        print(f"商品数据生成完成，共生成{count}条记录")
        
    except Exception as e:
        conn.rollback()
        print(f"生成商品数据时发生错误: {e}")
    finally:
        cursor.close()
        conn.close()

def generate_inventory_data(spark):
    """生成商品库存数据"""
    print("开始生成商品库存数据...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 获取所有商品和门店
        cursor.execute("SELECT id FROM product")
        product_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM store")
        store_ids = [row[0] for row in cursor.fetchall()]
        
        # 为每个门店的每个商品生成库存数据
        for store_id in store_ids:
            batch_data = []
            for product_id in product_ids:
                quantity = random.randint(50, 500)
                locked = random.randint(0, min(20, quantity))
                
                batch_data.append((
                    product_id,
                    store_id,
                    quantity,
                    locked
                ))
            
            cursor.executemany("""
                INSERT INTO product_inventory (product_id, store_id, quantity, locked_quantity)
                VALUES (%s, %s, %s, %s)
            """, batch_data)
            
            conn.commit()
            print(f"已生成门店 {store_id} 的库存数据")
        
        print("商品库存数据生成完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"生成库存数据时发生错误: {e}")
    finally:
        cursor.close()
        conn.close()

def generate_user_behavior(spark, days=30):
    """生成用户行为数据"""
    print(f"开始生成最近{days}天的用户行为数据...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 获取用户和商品ID
        cursor.execute("SELECT id FROM py_user")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM product")
        product_ids = [row[0] for row in cursor.fetchall()]
        
        # 行为类型及其权重
        behaviors = ['view', 'search', 'cart', 'purchase']
        behavior_weights = [70, 15, 10, 5]  # 70%浏览，15%搜索，10%加购，5%购买
        
        # 生成行为数据
        current_time = datetime.now()
        batch_data = []
        batch_size = 1000
        total_records = 0
        
        for day in range(days):
            # 每天随机生成100-500条行为记录
            daily_records = random.randint(100, 500)
            
            for _ in range(daily_records):
                user_id = random.choice(user_ids)
                behavior = random.choices(behaviors, behavior_weights)[0]
                timestamp = current_time - timedelta(days=day, 
                                                   hours=random.randint(0, 23),
                                                   minutes=random.randint(0, 59),
                                                   seconds=random.randint(0, 59))
                
                record = (
                    user_id,
                    random.choice(product_ids) if behavior != 'search' else None,
                    behavior,
                    '手机' if behavior == 'search' else None,  # search_keyword
                    f"SESSION_{user_id}_{timestamp.strftime('%Y%m%d')}",  # session_id
                    f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",  # ip_address
                    f"Mozilla/5.0 ({random.choice(['Windows', 'Mac', 'Linux'])})",  # user_agent
                    random.choice(['首页', '搜索页', '分类页', '推荐页']),  # referrer
                    timestamp
                )
                
                batch_data.append(record)
                if len(batch_data) >= batch_size:
                    cursor.executemany("""
                        INSERT INTO user_behavior (user_id, product_id, behavior_type,
                            search_keyword, session_id, ip_address, user_agent,
                            referrer, create_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, batch_data)
                    conn.commit()
                    total_records += len(batch_data)
                    print(f"已生成 {total_records} 条用户行为数据")
                    batch_data = []
        
        # 处理剩余的数据
        if batch_data:
            cursor.executemany("""
                INSERT INTO user_behavior (user_id, product_id, behavior_type,
                    search_keyword, session_id, ip_address, user_agent,
                    referrer, create_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch_data)
            conn.commit()
            total_records += len(batch_data)
        
        print(f"用户行为数据生成完成，共生成{total_records}条记录")
        
    except Exception as e:
        conn.rollback()
        print(f"生成用户行为数据时发生错误: {e}")
    finally:
        cursor.close()
        conn.close()

def generate_order_data(spark, count=2000):
    """使用Spark生成订单数据 - 更真实版本"""
    print(f"开始生成{count}个订单数据...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 清理订单相关表
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE sales_detail")
        cursor.execute("TRUNCATE TABLE sales_order")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 获取用户ID列表
        cursor.execute("SELECT id FROM py_user")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # 获取用户地址
        cursor.execute("SELECT user_id, id FROM user_address WHERE is_default = 1")
        user_addresses = dict(cursor.fetchall())
        
        # 获取商品信息 - 确保价格作为Decimal类型
        cursor.execute("SELECT id, product_name, product_code, CAST(price AS DECIMAL(10,2)) FROM product")
        products = cursor.fetchall()
        
        # 获取销售渠道
        cursor.execute("SELECT id, channel_type FROM sales_channel")
        channels = cursor.fetchall()
        online_channels = [c[0] for c in channels if c[1] == 'online']
        offline_channels = [c[0] for c in channels if c[1] == 'offline']
        
        # 获取门店
        cursor.execute("SELECT id FROM store")
        store_ids = [row[0] for row in cursor.fetchall()]
        
        # 获取营销活动
        cursor.execute("SELECT id FROM marketing_campaign")
        campaign_ids = [row[0] for row in cursor.fetchall()]
        
        # 支付方式
        payment_methods = ['alipay', 'wechat', 'card', 'cash']
        payment_weights = [40, 40, 15, 5]  # 40%支付宝，40%微信，15%银行卡，5%现金
        
        # 配送方式
        delivery_methods = ['express', 'self']
        
        # 生成订单数据
        batch_size = 50
        for i in range(0, count, batch_size):
            # 对每个批次的订单
            for j in range(batch_size):
                if i + j >= count:
                    break
                    
                # 生成订单基本信息
                user_id = random.choice(user_ids)
                
                # 随机选择订单来源和渠道
                is_online = random.random() < 0.7  # 70%是线上订单
                order_source = 'online' if is_online else 'offline'
                channel_id = random.choice(online_channels if is_online else offline_channels)
                
                # 随机选择门店（线下订单）
                store_id = random.choice(store_ids) if not is_online else None
                
                # 随机选择地址（线上订单）
                address_id = user_addresses.get(user_id) if is_online else None
                
                # 随机选择营销活动
                campaign_id = random.choice(campaign_ids) if random.random() < 0.3 else None  # 30%的订单有活动
                
                # 生成订单时间（考虑节假日销售波动）
                now = datetime.now()
                # 模拟节假日销售高峰
                holidays = [
                    (now.replace(month=1, day=1), 5),  # 元旦
                    (now.replace(month=2, day=14), 3),  # 情人节
                    (now.replace(month=5, day=1), 4),   # 劳动节
                    (now.replace(month=6, day=18), 5),  # 618
                    (now.replace(month=10, day=1), 5),  # 国庆节
                    (now.replace(month=11, day=11), 10), # 双11
                    (now.replace(month=12, day=12), 8),  # 双12
                    (now.replace(month=12, day=25), 3),  # 圣诞节
                ]
                
                # 计算日期权重
                date_weights = []
                for d in range(365):
                    order_date = now - timedelta(days=d)
                    weight = 1  # 基础权重
                    
                    # 周末权重提高
                    if order_date.weekday() >= 5:  # 5和6是周六日
                        weight *= 1.5
                    
                    # 节假日权重提高
                    for holiday_date, holiday_weight in holidays:
                        days_diff = abs((order_date - holiday_date).days)
                        if days_diff <= 3:  # 节假日前后3天
                            weight *= holiday_weight / (days_diff + 1)
                    
                    date_weights.append((d, weight))
                
                # 根据权重选择日期
                days_ago = random.choices([d for d, w in date_weights], 
                                         weights=[w for d, w in date_weights])[0]
                order_time = now - timedelta(days=days_ago)
                
                # 生成订单编号
                order_no = order_time.strftime('%Y%m%d') + str(i + j + 1).zfill(6)
                
                # 随机选择1-5个商品
                order_products = random.sample(products, random.randint(1, 5))
                total_amount = Decimal('0.00')
                
                # 随机选择支付方式
                payment_method = random.choices(payment_methods, payment_weights)[0]
                
                # 随机选择配送方式（线上订单）
                delivery_method = random.choice(delivery_methods) if is_online else None
                
                # 计算订单状态和时间
                if days_ago < 1:  # 今天的订单
                    possible_statuses = [0, 1]  # 待付款或待发货
                    weights = [20, 80]  # 20%待付款，80%待发货
                elif days_ago < 3:  # 3天内的订单
                    possible_statuses = [1, 2, 3]  # 待发货、待收货或已完成
                    weights = [20, 30, 50]  # 20%待发货，30%待收货，50%已完成
                else:  # 更早的订单
                    possible_statuses = [3, 4]  # 已完成或已取消
                    weights = [90, 10]  # 90%已完成，10%已取消
                
                order_status = random.choices(possible_statuses, weights)[0]
                
                # 计算支付状态
                if order_status == 0:  # 待付款
                    payment_status = 0  # 未支付
                    payment_time = None
                else:  # 其他状态
                    payment_status = 1  # 已支付
                    payment_time = order_time + timedelta(hours=random.randint(0, 2))
                
                # 计算发货和完成时间
                delivery_status = 0  # 默认未发货
                delivery_time = None
                complete_time = None
                
                if order_status >= 1:  # 待发货及以上
                    if order_status >= 2:  # 待收货及以上
                        delivery_status = 1  # 已发货
                        delivery_time = payment_time + timedelta(days=random.randint(1, 2))
                        
                        if order_status >= 3:  # 已完成
                            delivery_status = 2  # 已收货
                            complete_time = delivery_time + timedelta(days=random.randint(1, 3))
                
                # 插入订单主表数据
                cursor.execute("""
                    INSERT INTO sales_order (order_no, user_id, store_id, order_source, 
                        channel_id, campaign_id, order_status, payment_method, payment_status,
                        payment_time, delivery_method, delivery_status, delivery_time,
                        complete_time, address_id, total_amount, discount_amount, 
                        shipping_amount, payment_amount, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_no,
                    user_id,
                    store_id,
                    order_source,
                    channel_id,
                    campaign_id,
                    order_status,
                    payment_method,
                    payment_status,
                    payment_time,
                    delivery_method,
                    delivery_status,
                    delivery_time,
                    complete_time,
                    address_id,
                    0,  # 临时总金额，稍后更新
                    0,  # discount_amount
                    0 if not is_online or delivery_method == 'self' else random.choice([10, 15, 20]),  # shipping_amount
                    0,  # 临时支付金额，稍后更新
                    order_time
                ))
                
                # 获取插入的订单ID
                order_id = cursor.lastrowid
                
                # 生成订单明细
                detail_batch = []
                for product in order_products:
                    product_id, product_name, product_code, price = product
                    quantity = random.randint(1, 5)
                    # 确保使用Decimal进行计算
                    price = Decimal(str(price))
                    total_price = price * Decimal(str(quantity))
                    
                    # 计算折扣（如果有活动）
                    discount_price = Decimal('0.00')
                    if campaign_id:
                        # 使用Decimal进行折扣计算
                        discount_rate = Decimal(str(random.uniform(0.05, 0.2)))
                        discount_price = (total_price * discount_rate).quantize(Decimal('0.01'))
                    
                    actual_price = total_price - discount_price
                    total_amount += actual_price
                    
                    detail_batch.append((
                        order_id,
                        product_id,
                        product_name,
                        product_code,
                        quantity,
                        price,  # unit_price
                        total_price,  # total_price
                        discount_price,
                        actual_price
                    ))
                
                # 批量插入订单明细数据
                cursor.executemany("""
                    INSERT INTO sales_detail (order_id, product_id, product_name, 
                        product_code, quantity, unit_price, total_price, 
                        discount_price, actual_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, detail_batch)
                
                # 计算订单总折扣
                discount_amount = sum(Decimal(str(item[7])) for item in detail_batch)
                
                # 计算运费
                shipping_amount = Decimal('0.00') if not is_online or delivery_method == 'self' else \
                    Decimal(str(random.choice([10, 15, 20])))
                
                # 计算实付金额
                payment_amount = total_amount + shipping_amount
                
                # 更新订单主表的金额
                cursor.execute("""
                    UPDATE sales_order 
                    SET total_amount = %s, discount_amount = %s, shipping_amount = %s, payment_amount = %s 
                    WHERE id = %s
                """, (total_amount + discount_amount, discount_amount, shipping_amount, payment_amount, order_id))
                
            conn.commit()
            print(f"已生成 {min(i + batch_size, count)} 个订单数据")
        
        print(f"订单数据生成完成，共生成{count}个订单")
        
    except Exception as e:
        conn.rollback()
        print(f"生成订单数据时发生错误: {e}")
        raise e  # 重新抛出异常以便查看详细错误信息
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    try:
        # 创建SparkSession
        spark = create_spark_session()
        spark.sparkContext.setLogLevel("ERROR")
        print("SparkSession创建成功！")
        
        # 创建基础数据（包含会员等级、销售渠道、商品分类、供应商、门店、营销活动）
        create_base_data()
        
        # 生成用户数据
        generate_user_data(spark, count=1000)
        
        # 生成商品数据
        generate_product_data(spark, count=500)
        
        # 生成库存数据
        generate_inventory_data(spark)
        
        # 生成用户行为数据
        generate_user_behavior(spark, days=30)
        
        # 生成订单数据
        generate_order_data(spark, count=2000)
        
        print("所有数据生成完成！")
        
    except Exception as e:
        print(f"数据生成过程中发生错误: {e}")
    finally:
        if 'spark' in locals():
            spark.stop()
            print("SparkSession已关闭")

if __name__ == "__main__":
    main()
