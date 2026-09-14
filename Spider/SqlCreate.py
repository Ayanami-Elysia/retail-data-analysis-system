import pymysql

def create_tables():
    """创建新零售大数据分析平台所需的数据库表"""
    # 数据库连接
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='new_retail')
    cursor = conn.cursor()
    
    try:
        # 先删除所有表（按照依赖关系的反序）
        print("正在删除旧表...")
        
        # 先删除视图
        print("删除旧视图...")
        cursor.execute("DROP VIEW IF EXISTS `view_sales_summary`")
        cursor.execute("DROP VIEW IF EXISTS `view_product_sales_ranking`")
        cursor.execute("DROP VIEW IF EXISTS `view_online_offline_comparison`")
        cursor.execute("DROP VIEW IF EXISTS `view_user_purchase_behavior`")
        cursor.execute("DROP VIEW IF EXISTS `view_campaign_performance`")
        
        # 删除表（按照依赖关系的反序）
        print("删除数据表...")
        
        # 1. 销售明细表（依赖于销售订单表和商品表）
        cursor.execute("DROP TABLE IF EXISTS `sales_detail`")
        
        # 2. 销售订单表（依赖于用户表、门店表、地址表、渠道表、活动表）
        cursor.execute("DROP TABLE IF EXISTS `sales_order`")
        
        # 3. 用户行为表（依赖于用户表和商品表）
        cursor.execute("DROP TABLE IF EXISTS `user_behavior`")
        
        # 4. 商品库存表（依赖于商品表和门店表）
        cursor.execute("DROP TABLE IF EXISTS `product_inventory`")
        
        # 5. 用户地址表（依赖于用户表）
        cursor.execute("DROP TABLE IF EXISTS `user_address`")
        
        # 6. 商品表（依赖于商品分类表和供应商表）
        cursor.execute("DROP TABLE IF EXISTS `product`")
        
        # 7. 商品分类表
        cursor.execute("DROP TABLE IF EXISTS `product_category`")
        
        # 8. 供应商表
        cursor.execute("DROP TABLE IF EXISTS `supplier`")
        
        # 9. 门店表
        cursor.execute("DROP TABLE IF EXISTS `store`")
        
        # 10. 销售渠道表
        cursor.execute("DROP TABLE IF EXISTS `sales_channel`")
        
        # 11. 营销活动表
        cursor.execute("DROP TABLE IF EXISTS `marketing_campaign`")
        
        # 12. 会员等级表
        cursor.execute("DROP TABLE IF EXISTS `member_level`")
        
        # 13. 用户表（基础表，最后删除）
        cursor.execute("DROP TABLE IF EXISTS `py_user`")
        
        print("所有旧表删除完成")
        
        # 创建用户表
        print("创建用户表...")
        cursor.execute("DROP TABLE IF EXISTS `py_user`")
        cursor.execute("""
        CREATE TABLE `py_user` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '用户名',
          `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '密码',
          `nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '真实姓名',
          `sex` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '性别',
          `age` int(11) NULL DEFAULT NULL COMMENT '年龄',
          `phone` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '电话',
          `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '邮箱',
          `birthday` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '生日',
          `card` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '身份证',
          `content` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
          `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
          `role` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT '角色',
          PRIMARY KEY (`id`) USING BTREE
        ) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci ROW_FORMAT = DYNAMIC
        """)
        
        # 创建会员等级表
        print("创建会员等级表...")
        cursor.execute("""
        CREATE TABLE `member_level` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `level_name` varchar(50) NOT NULL COMMENT '等级名称',
          `min_points` int(11) NOT NULL COMMENT '最小积分',
          `max_points` int(11) NOT NULL COMMENT '最大积分',
          `discount` decimal(3,2) NOT NULL COMMENT '折扣率',
          `description` varchar(255) DEFAULT NULL COMMENT '等级描述',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员等级表';
        """)
        
        # 创建供应商表
        print("创建供应商表...")
        cursor.execute("""
        CREATE TABLE `supplier` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `supplier_name` varchar(100) NOT NULL COMMENT '供应商名称',
          `contact_person` varchar(50) DEFAULT NULL COMMENT '联系人',
          `contact_phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
          `address` varchar(255) DEFAULT NULL COMMENT '地址',
          `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
          `status` tinyint(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商表';
        """)
        
        # 创建门店表
        print("创建门店表...")
        cursor.execute("""
        CREATE TABLE `store` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `store_name` varchar(100) NOT NULL COMMENT '门店名称',
          `store_code` varchar(50) NOT NULL COMMENT '门店编码',
          `address` varchar(255) DEFAULT NULL COMMENT '地址',
          `manager` varchar(50) DEFAULT NULL COMMENT '店长',
          `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
          `business_hours` varchar(100) DEFAULT NULL COMMENT '营业时间',
          `status` tinyint(1) DEFAULT 1 COMMENT '状态：0-关闭，1-营业',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `idx_store_code` (`store_code`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店表';
        """)
        
        # 创建销售渠道表
        print("创建销售渠道表...")
        cursor.execute("""
        CREATE TABLE `sales_channel` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `channel_name` varchar(50) NOT NULL COMMENT '渠道名称',
          `channel_type` varchar(20) NOT NULL COMMENT '渠道类型：online-线上，offline-线下',
          `channel_code` varchar(20) NOT NULL COMMENT '渠道编码',
          `description` varchar(255) DEFAULT NULL COMMENT '渠道描述',
          `commission_rate` decimal(5,2) DEFAULT 0.00 COMMENT '佣金比例(%)',
          `status` tinyint(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `idx_channel_code` (`channel_code`),
          KEY `idx_channel_type` (`channel_type`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售渠道表';
        """)
        
        # 创建营销活动表
        print("创建营销活动表...")
        cursor.execute("""
        CREATE TABLE `marketing_campaign` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `campaign_name` varchar(100) NOT NULL COMMENT '活动名称',
          `campaign_type` varchar(50) NOT NULL COMMENT '活动类型：discount-折扣，coupon-优惠券，gift-赠品，flash_sale-限时特卖',
          `start_time` datetime NOT NULL COMMENT '开始时间',
          `end_time` datetime NOT NULL COMMENT '结束时间',
          `discount_rate` decimal(5,2) DEFAULT NULL COMMENT '折扣率',
          `discount_amount` decimal(10,2) DEFAULT NULL COMMENT '优惠金额',
          `min_order_amount` decimal(10,2) DEFAULT NULL COMMENT '最低订单金额',
          `channel_scope` varchar(255) DEFAULT 'all' COMMENT '渠道范围：all-全部渠道，online-仅线上，offline-仅线下，或具体渠道ID列表',
          `product_scope` varchar(255) DEFAULT 'all' COMMENT '商品范围：all-全部商品，category-按分类，product-按商品，或具体商品ID列表',
          `user_scope` varchar(255) DEFAULT 'all' COMMENT '用户范围：all-全部用户，new-新用户，vip-会员用户，或具体用户群体ID',
          `usage_limit` int(11) DEFAULT NULL COMMENT '使用次数限制',
          `budget` decimal(10,2) DEFAULT NULL COMMENT '活动预算',
          `status` tinyint(1) DEFAULT 1 COMMENT '状态：0-未开始，1-进行中，2-已结束，3-已取消',
          `description` text DEFAULT NULL COMMENT '活动描述',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          KEY `idx_start_time` (`start_time`),
          KEY `idx_end_time` (`end_time`),
          KEY `idx_status` (`status`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='营销活动表';
        """)
        
        # 创建商品分类表
        print("创建商品分类表...")
        cursor.execute("""
        CREATE TABLE `product_category` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `category_name` varchar(100) NOT NULL COMMENT '分类名称',
          `parent_id` int(11) DEFAULT 0 COMMENT '父分类ID，0表示一级分类',
          `level` tinyint(1) DEFAULT 1 COMMENT '分类层级',
          `sort_order` int(11) DEFAULT 0 COMMENT '排序',
          `status` tinyint(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          KEY `idx_parent_id` (`parent_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';
        """)
        
        # 创建商品表
        print("创建商品表...")
        cursor.execute("""
        CREATE TABLE `product` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `product_name` varchar(200) NOT NULL COMMENT '商品名称',
          `product_code` varchar(50) NOT NULL COMMENT '商品编码',
          `category_id` int(11) NOT NULL COMMENT '分类ID',
          `supplier_id` int(11) DEFAULT NULL COMMENT '供应商ID',
          `brand` varchar(100) DEFAULT NULL COMMENT '品牌',
          `model` varchar(100) DEFAULT NULL COMMENT '型号',
          `unit` varchar(20) DEFAULT NULL COMMENT '单位',
          `price` decimal(10,2) NOT NULL COMMENT '售价',
          `cost_price` decimal(10,2) DEFAULT NULL COMMENT '成本价',
          `market_price` decimal(10,2) DEFAULT NULL COMMENT '市场价',
          `stock` int(11) DEFAULT 0 COMMENT '库存',
          `warning_stock` int(11) DEFAULT 10 COMMENT '库存预警值',
          `sales` int(11) DEFAULT 0 COMMENT '销量',
          `weight` decimal(10,2) DEFAULT NULL COMMENT '重量(kg)',
          `volume` decimal(10,2) DEFAULT NULL COMMENT '体积(m³)',
          `is_new` tinyint(1) DEFAULT 0 COMMENT '是否新品：0-否，1-是',
          `is_hot` tinyint(1) DEFAULT 0 COMMENT '是否热销：0-否，1-是',
          `is_recommend` tinyint(1) DEFAULT 0 COMMENT '是否推荐：0-否，1-是',
          `status` tinyint(1) DEFAULT 1 COMMENT '状态：0-下架，1-上架',
          `description` text DEFAULT NULL COMMENT '商品描述',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `idx_product_code` (`product_code`),
          KEY `idx_category_id` (`category_id`),
          KEY `idx_supplier_id` (`supplier_id`),
          CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `product_category` (`id`) ON DELETE CASCADE,
          CONSTRAINT `fk_product_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `supplier` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';
        """)
        
        # 创建商品库存表
        print("创建商品库存表...")
        cursor.execute("""
        CREATE TABLE `product_inventory` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `product_id` int(11) NOT NULL COMMENT '商品ID',
          `store_id` int(11) NOT NULL COMMENT '门店ID',
          `quantity` int(11) NOT NULL DEFAULT 0 COMMENT '库存数量',
          `locked_quantity` int(11) NOT NULL DEFAULT 0 COMMENT '锁定库存数量',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `idx_product_store` (`product_id`, `store_id`),
          KEY `idx_store_id` (`store_id`),
          CONSTRAINT `fk_inventory_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE CASCADE,
          CONSTRAINT `fk_inventory_store` FOREIGN KEY (`store_id`) REFERENCES `store` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品库存表';
        """)
        
        # 创建用户地址表
        print("创建用户地址表...")
        cursor.execute("""
        CREATE TABLE `user_address` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `user_id` int(11) NOT NULL COMMENT '用户ID',
          `receiver` varchar(50) NOT NULL COMMENT '收货人',
          `phone` varchar(20) NOT NULL COMMENT '联系电话',
          `province` varchar(50) DEFAULT NULL COMMENT '省份',
          `city` varchar(50) DEFAULT NULL COMMENT '城市',
          `district` varchar(50) DEFAULT NULL COMMENT '区/县',
          `detail_address` varchar(255) NOT NULL COMMENT '详细地址',
          `is_default` tinyint(1) DEFAULT 0 COMMENT '是否默认地址：0-否，1-是',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          KEY `idx_user_id` (`user_id`),
          CONSTRAINT `fk_address_user` FOREIGN KEY (`user_id`) REFERENCES `py_user` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户地址表';
        """)
        
        # 创建用户行为表
        print("创建用户行为表...")
        cursor.execute("""
        CREATE TABLE `user_behavior` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `user_id` int(11) NOT NULL COMMENT '用户ID',
          `product_id` int(11) DEFAULT NULL COMMENT '商品ID',
          `behavior_type` varchar(20) NOT NULL COMMENT '行为类型：view-浏览，search-搜索，cart-加入购物车，purchase-购买',
          `search_keyword` varchar(100) DEFAULT NULL COMMENT '搜索关键词',
          `session_id` varchar(100) DEFAULT NULL COMMENT '会话ID',
          `ip_address` varchar(50) DEFAULT NULL COMMENT 'IP地址',
          `user_agent` varchar(255) DEFAULT NULL COMMENT '用户代理',
          `referrer` varchar(255) DEFAULT NULL COMMENT '来源页面',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          PRIMARY KEY (`id`),
          KEY `idx_user_id` (`user_id`),
          KEY `idx_product_id` (`product_id`),
          KEY `idx_behavior_type` (`behavior_type`),
          KEY `idx_create_time` (`create_time`),
          CONSTRAINT `fk_behavior_user` FOREIGN KEY (`user_id`) REFERENCES `py_user` (`id`) ON DELETE CASCADE,
          CONSTRAINT `fk_behavior_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户行为表';
        """)
        
        # 创建销售订单表
        print("创建销售订单表...")
        cursor.execute("""
        CREATE TABLE `sales_order` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `order_no` varchar(50) NOT NULL COMMENT '订单编号',
          `user_id` int(11) NOT NULL COMMENT '用户ID',
          `store_id` int(11) DEFAULT NULL COMMENT '门店ID',
          `order_source` varchar(20) NOT NULL DEFAULT 'online' COMMENT '订单来源：online-线上，offline-线下',
          `channel_id` int(11) DEFAULT NULL COMMENT '渠道ID',
          `campaign_id` int(11) DEFAULT NULL COMMENT '营销活动ID',
          `order_status` tinyint(1) DEFAULT 0 COMMENT '订单状态：0-待付款，1-待发货，2-待收货，3-已完成，4-已取消，5-已退款',
          `payment_method` varchar(20) DEFAULT NULL COMMENT '支付方式：cash-现金，alipay-支付宝，wechat-微信，card-银行卡',
          `payment_status` tinyint(1) DEFAULT 0 COMMENT '支付状态：0-未支付，1-已支付，2-已退款',
          `payment_time` datetime DEFAULT NULL COMMENT '支付时间',
          `delivery_method` varchar(20) DEFAULT NULL COMMENT '配送方式：express-快递，self-自提',
          `delivery_status` tinyint(1) DEFAULT 0 COMMENT '配送状态：0-未发货，1-已发货，2-已收货',
          `delivery_time` datetime DEFAULT NULL COMMENT '发货时间',
          `complete_time` datetime DEFAULT NULL COMMENT '完成时间',
          `address_id` int(11) DEFAULT NULL COMMENT '地址ID',
          `total_amount` decimal(10,2) NOT NULL COMMENT '订单总金额',
          `discount_amount` decimal(10,2) DEFAULT 0.00 COMMENT '优惠金额',
          `shipping_amount` decimal(10,2) DEFAULT 0.00 COMMENT '运费',
          `payment_amount` decimal(10,2) NOT NULL COMMENT '实付金额',
          `remark` varchar(255) DEFAULT NULL COMMENT '订单备注',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `idx_order_no` (`order_no`),
          KEY `idx_user_id` (`user_id`),
          KEY `idx_store_id` (`store_id`),
          KEY `idx_address_id` (`address_id`),
          KEY `idx_create_time` (`create_time`),
          KEY `idx_order_source` (`order_source`),
          KEY `idx_channel_id` (`channel_id`),
          KEY `idx_campaign_id` (`campaign_id`),
          CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `py_user` (`id`) ON DELETE CASCADE,
          CONSTRAINT `fk_order_store` FOREIGN KEY (`store_id`) REFERENCES `store` (`id`) ON DELETE SET NULL,
          CONSTRAINT `fk_order_address` FOREIGN KEY (`address_id`) REFERENCES `user_address` (`id`) ON DELETE SET NULL,
          CONSTRAINT `fk_order_channel` FOREIGN KEY (`channel_id`) REFERENCES `sales_channel` (`id`) ON DELETE SET NULL,
          CONSTRAINT `fk_order_campaign` FOREIGN KEY (`campaign_id`) REFERENCES `marketing_campaign` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售订单表';
        """)
        
        # 创建销售明细表
        print("创建销售明细表...")
        cursor.execute("""
        CREATE TABLE `sales_detail` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `order_id` int(11) NOT NULL COMMENT '订单ID',
          `product_id` int(11) NOT NULL COMMENT '商品ID',
          `product_name` varchar(200) NOT NULL COMMENT '商品名称',
          `product_code` varchar(50) NOT NULL COMMENT '商品编码',
          `quantity` int(11) NOT NULL COMMENT '购买数量',
          `unit_price` decimal(10,2) NOT NULL COMMENT '单价',
          `total_price` decimal(10,2) NOT NULL COMMENT '总价',
          `discount_price` decimal(10,2) DEFAULT 0.00 COMMENT '优惠价格',
          `actual_price` decimal(10,2) NOT NULL COMMENT '实际价格',
          `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          PRIMARY KEY (`id`),
          KEY `idx_order_id` (`order_id`),
          KEY `idx_product_id` (`product_id`),
          CONSTRAINT `fk_detail_order` FOREIGN KEY (`order_id`) REFERENCES `sales_order` (`id`) ON DELETE CASCADE,
          CONSTRAINT `fk_detail_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售明细表';
        """)
        
        # 提交事务
        conn.commit()
        print("所有表创建成功！")
        
    except Exception as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"创建表时发生错误: {e}")
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()

def create_analysis_views():
    """创建数据分析视图"""
    # 数据库连接
    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='new_retail')
    cursor = conn.cursor()
    
    try:
        print("开始创建数据分析视图...")
        
        # 1. 销售概览视图 - 按日期、渠道类型统计销售数据
        print("创建销售概览视图...")
        cursor.execute("""
        CREATE OR REPLACE VIEW `view_sales_summary` AS
        SELECT 
            DATE(so.create_time) AS sale_date,
            sc.channel_type,
            sc.channel_name,
            COUNT(so.id) AS order_count,
            SUM(so.total_amount) AS total_sales,
            SUM(so.discount_amount) AS total_discount,
            SUM(so.payment_amount) AS actual_sales,
            ROUND(SUM(so.payment_amount)/COUNT(so.id), 2) AS avg_order_value
        FROM 
            sales_order so
        LEFT JOIN 
            sales_channel sc ON so.channel_id = sc.id
        WHERE 
            so.order_status = 3 -- 已完成的订单
        GROUP BY 
            DATE(so.create_time), sc.channel_type, sc.channel_name
        ORDER BY 
            sale_date DESC, total_sales DESC
        """)
        
        # 2. 商品销售排行视图
        print("创建商品销售排行视图...")
        cursor.execute("""
        CREATE OR REPLACE VIEW `view_product_sales_ranking` AS
        SELECT 
            p.id AS product_id,
            p.product_name,
            p.product_code,
            pc.category_name,
            SUM(sd.quantity) AS total_quantity,
            SUM(sd.total_price) AS total_sales,
            COUNT(DISTINCT so.id) AS order_count,
            ROUND(SUM(sd.total_price)/SUM(sd.quantity), 2) AS avg_price
        FROM 
            sales_detail sd
        JOIN 
            sales_order so ON sd.order_id = so.id
        JOIN 
            product p ON sd.product_id = p.id
        JOIN 
            product_category pc ON p.category_id = pc.id
        WHERE 
            so.order_status = 3 -- 已完成的订单
        GROUP BY 
            p.id, p.product_name, p.product_code, pc.category_name
        ORDER BY 
            total_sales DESC
        """)
        
        # 3. 线上线下销售对比视图
        print("创建线上线下销售对比视图...")
        cursor.execute("""
        CREATE OR REPLACE VIEW `view_online_offline_comparison` AS
        SELECT 
            DATE_FORMAT(so.create_time, '%Y-%m') AS sale_month,
            so.order_source,
            COUNT(so.id) AS order_count,
            SUM(so.payment_amount) AS sales_amount,
            COUNT(DISTINCT so.user_id) AS customer_count,
            ROUND(SUM(so.payment_amount)/COUNT(so.id), 2) AS avg_order_value
        FROM 
            sales_order so
        WHERE 
            so.order_status = 3 -- 已完成的订单
        GROUP BY 
            DATE_FORMAT(so.create_time, '%Y-%m'), so.order_source
        ORDER BY 
            sale_month DESC, so.order_source
        """)
        
        # 4. 用户购买行为分析视图
        print("创建用户购买行为分析视图...")
        cursor.execute("""
        CREATE OR REPLACE VIEW `view_user_purchase_behavior` AS
        SELECT 
            u.id AS user_id,
            u.username,
            u.nickname,
            COUNT(so.id) AS order_count,
            SUM(so.payment_amount) AS total_spent,
            MAX(so.create_time) AS last_purchase_date,
            DATEDIFF(CURRENT_DATE, MAX(so.create_time)) AS days_since_last_purchase,
            COUNT(DISTINCT DATE(so.create_time)) AS purchase_days,
            ROUND(SUM(so.payment_amount)/COUNT(so.id), 2) AS avg_order_value,
            GROUP_CONCAT(DISTINCT sc.channel_name ORDER BY sc.channel_name SEPARATOR ', ') AS used_channels
        FROM 
            py_user u
        JOIN 
            sales_order so ON u.id = so.user_id
        LEFT JOIN 
            sales_channel sc ON so.channel_id = sc.id
        WHERE 
            so.order_status = 3 -- 已完成的订单
        GROUP BY 
            u.id, u.username, u.nickname
        ORDER BY 
            total_spent DESC
        """)
        
        # 5. 营销活动效果分析视图
        print("创建营销活动效果分析视图...")
        cursor.execute("""
        CREATE OR REPLACE VIEW `view_campaign_performance` AS
        SELECT 
            mc.id AS campaign_id,
            mc.campaign_name,
            mc.campaign_type,
            COUNT(so.id) AS order_count,
            SUM(so.total_amount) AS gross_sales,
            SUM(so.discount_amount) AS total_discount,
            SUM(so.payment_amount) AS net_sales,
            ROUND((SUM(so.discount_amount)/SUM(so.total_amount))*100, 2) AS discount_rate_percent,
            COUNT(DISTINCT so.user_id) AS customer_count,
            ROUND(SUM(so.payment_amount)/COUNT(so.id), 2) AS avg_order_value
        FROM 
            marketing_campaign mc
        LEFT JOIN 
            sales_order so ON mc.id = so.campaign_id AND so.order_status = 3 -- 已完成的订单
        GROUP BY 
            mc.id, mc.campaign_name, mc.campaign_type
        ORDER BY 
            net_sales DESC
        """)
        
        # 提交事务
        conn.commit()
        print("所有数据分析视图创建成功！")
        
    except Exception as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"创建视图时发生错误: {e}")
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_tables()
    # 注释掉自动创建视图的调用，由用户根据需要手动调用
     #create_analysis_views()
