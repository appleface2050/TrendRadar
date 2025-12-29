"""
数据库初始化脚本
创建 MacroTrading 数据库和必要的表结构
"""
import pymysql
from db_config import DB_CONFIG, DATABASE_NAME
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_database():
    """创建 MacroTrading 数据库"""
    try:
        # 连接 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )

        cursor = connection.cursor()

        # 检查数据库是否已存在
        cursor.execute(f"SHOW DATABASES LIKE '{DATABASE_NAME}'")
        result = cursor.fetchone()

        if result:
            logger.info(f"数据库 '{DATABASE_NAME}' 已存在")
        else:
            # 创建数据库
            cursor.execute(f"""
                CREATE DATABASE {DATABASE_NAME}
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci
            """)
            logger.info(f"成功创建数据库 '{DATABASE_NAME}'")

        cursor.close()
        connection.close()

        return True

    except Exception as e:
        logger.error(f"创建数据库失败: {str(e)}")
        return False


def create_us_macro_tables():
    """创建美国宏观数据表"""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DATABASE_NAME,
            charset=DB_CONFIG['charset']
        )

        cursor = connection.cursor()

        # 创建美国宏观数据表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS us_macro_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL COMMENT '指标代码（FRED代码）',
            indicator_name VARCHAR(200) COMMENT '指标名称',
            date DATE NOT NULL COMMENT '数据日期',
            value DECIMAL(20, 6) COMMENT '指标值',
            frequency VARCHAR(20) COMMENT '频率（d/w/m/q/ya）',
            unit VARCHAR(50) COMMENT '单位',
            release_date DATE COMMENT '发布日期',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_indicator_date (indicator_code, date),
            INDEX idx_date (date),
            INDEX idx_indicator (indicator_code),
            INDEX idx_release_date (release_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='美国宏观数据表';
        """

        cursor.execute(create_table_sql)
        connection.commit()

        logger.info("成功创建表 us_macro_data")
        cursor.close()
        connection.close()

        return True

    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        return False


def create_cn_macro_tables():
    """创建中国宏观数据表"""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DATABASE_NAME,
            charset=DB_CONFIG['charset']
        )

        cursor = connection.cursor()

        # 创建中国宏观数据表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cn_macro_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL COMMENT '指标代码',
            indicator_name VARCHAR(200) COMMENT '指标名称',
            date DATE NOT NULL COMMENT '数据日期',
            value DECIMAL(20, 6) COMMENT '指标值',
            frequency VARCHAR(20) COMMENT '频率（d/w/m/q/ya）',
            unit VARCHAR(50) COMMENT '单位',
            source VARCHAR(50) COMMENT '数据源（tushare/akshare）',
            release_date DATE COMMENT '发布日期',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_indicator_date (indicator_code, date),
            INDEX idx_date (date),
            INDEX idx_indicator (indicator_code),
            INDEX idx_source (source),
            INDEX idx_release_date (release_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='中国宏观数据表';
        """

        cursor.execute(create_table_sql)
        connection.commit()

        logger.info("成功创建表 cn_macro_data")
        cursor.close()
        connection.close()

        return True

    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        return False


def create_release_calendar_tables():
    """创建发布日历表"""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DATABASE_NAME,
            charset=DB_CONFIG['charset']
        )

        cursor = connection.cursor()

        # 创建发布日历表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS release_calendar (
            id INT AUTO_INCREMENT PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL COMMENT '指标代码',
            indicator_name VARCHAR(200) COMMENT '指标名称',
            country VARCHAR(10) NOT NULL COMMENT '国家（US/CN）',
            release_date DATE NOT NULL COMMENT '发布日期',
            reference_date DATE COMMENT '参考日期（数据所属期）',
            frequency VARCHAR(20) COMMENT '频率',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_release (indicator_code, release_date, reference_date),
            INDEX idx_release_date (release_date),
            INDEX idx_indicator (indicator_code),
            INDEX idx_country (country)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='宏观数据发布日历表';
        """

        cursor.execute(create_table_sql)
        connection.commit()

        logger.info("成功创建表 release_calendar")
        cursor.close()
        connection.close()

        return True

    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始初始化 MacroTrading 数据库")
    logger.info("=" * 60)

    # 创建数据库
    if create_database():
        logger.info("✓ 数据库创建/检查完成")

        # 创建表
        if create_us_macro_tables():
            logger.info("✓ 美国宏观数据表创建完成")

        if create_cn_macro_tables():
            logger.info("✓ 中国宏观数据表创建完成")

        if create_release_calendar_tables():
            logger.info("✓ 发布日历表创建完成")

        logger.info("=" * 60)
        logger.info("数据库初始化完成！")
        logger.info("=" * 60)
    else:
        logger.error("数据库初始化失败")
