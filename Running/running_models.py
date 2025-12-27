import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from confs.mysql import mysql_conf, mysql_running_conf
from sqlalchemy import create_engine, text
import pandas as pd

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Enum,
    DECIMAL,
    DateTime,
    Boolean,
    UniqueConstraint,
    Index
)
from sqlalchemy.ext.declarative import declarative_base

# 基础类
Base = declarative_base()

# 创建引擎
engine_running = create_engine(
    # "mysql+pymysql://root:root@localhost:3306/quant?charset=utf8mb4",
    f"mysql+pymysql://{mysql_running_conf['username']}:{mysql_running_conf['password']}@{mysql_running_conf['host']}:{mysql_running_conf['port']}/{mysql_running_conf['database']}?charset=utf8mb4",
    # "mysql+pymysql://tom@127.0.0.1:3306/db1?charset=utf8mb4", # 无密码时
    # 超过链接池大小外最多创建的链接
    max_overflow=0,
    # 链接池大小
    pool_size=5,
    # 链接池中没有可用链接则最多等待的秒数，超过该秒数后报错
    pool_timeout=10,
    # 多久之后对链接池中的链接进行一次回收
    pool_recycle=1,
    # 查看原生语句（未格式化）
    echo=False
)

# 绑定引擎
Session = sessionmaker(bind=engine_running)
# 创建数据库链接池，直接使用session即可为当前线程拿出一个链接对象conn
# 内部会采用threading.local进行隔离
session = scoped_session(Session)

import logging


# logging.basicConfig()
# logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

# logging.disable(logging.WARNING)


def create_table(model_name):
    tables = [model_name.__table__]

    Base.metadata.drop_all(engine_running, tables=tables)
    Base.metadata.create_all(engine_running, tables=tables)

    sql = text(
        "ALTER TABLE   `%s`   CHANGE `uptime` `uptime` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;" % model_name.__table__)
    print(sql)
    session.execute(sql)


class DailyRQRecord(Base):
    __tablename__ = "running_rq_record"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    date = Column(String(32), index=True, nullable=False, unique=True, comment="日期")
    rq = Column(String(32), index=True, nullable=False, comment="rq", default=0)
    status = Column(String(32), index=True, nullable=False, comment="status", default=0)
    physical_power = Column(String(32), index=True, nullable=False, comment="physical_power", default=0)
    fatigue = Column(String(32), index=True, nullable=False, comment="fatigue", default=0)
    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    @classmethod
    def get_recent_rq(cls, start):
        a = session.query(cls).filter(cls.date < start).order_by(cls.date.desc()).first()
        return a.rq


class DailyShoeRecord(Base):
    __tablename__ = "running_shoe_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    date = Column(String(32), index=True, nullable=False, unique=False, comment="使用日期")
    shoe = Column(String(32), index=True, nullable=False, unique=False, comment="名称")
    distance = Column(String(32), index=True, nullable=False, comment="里程", default=0)
    used_time = Column(String(32), default="", index=True, nullable=False, unique=False, comment="使用时长")
    average_heart_rate = Column(String(32), index=True, nullable=False, comment="平均心率", default=0)
    cadence = Column(String(32), default=0, nullable=False, index=True, comment="步频")
    type = Column(String(32), default="", index=True, nullable=False, unique=False, comment="跑步类型")
    rq = Column(String(32), default=0, nullable=False, index=False, comment="rq数值")
    rq_inc = Column(String(32), default=0, nullable=False, index=False, comment="rq增量")
    EMTIR = Column(String(32), default="", nullable=False, index=False, comment="EMTIR")
    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    __table_args__ = (
        Index('idx_date_shoe', "date", 'shoe', unique=False),
    )

    def __str__(self):
        return f"object : <{self.date} {self.shoe}>"

    @classmethod
    def get_last_used_date(cls, shoe):
        a = session.query(cls).filter(cls.shoe == shoe).order_by(cls.date.desc()).first()
        if a:
            return a.date
        else:
            return None


class ShoeInfo(Base):
    __tablename__ = "running_shoe_info"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    shoe = Column(String(32), index=True, nullable=False, unique=True, comment="名称")
    brand = Column(String(32), index=True, nullable=False, unique=False, comment="品牌")
    price = Column(Float, default=0, index=True, nullable=False, comment="价格")
    color = Column(String(32), index=True, nullable=False, unique=False, comment="颜色")
    start_date = Column(String(32), default="", index=True, nullable=False, unique=False, comment="购买日期")
    end_date = Column(String(32), default="", index=True, nullable=False, unique=False, comment="退役日期")
    shortage = Column(String(1023), default="", index=False, nullable=False, comment="缺点")
    sold_price = Column(Float, default=0, index=True, nullable=False, comment="卖出价格")
    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    # __table_args__ = (
    #     Index('idx_ts_code_date', "ts_code", 'date', unique=False),
    #     Index('idx_ts_code_date_unique', "ts_code", 'date', unique=True),
    # )

    def __str__(self):
        return f"running_shoe_info <{self.name}>"

    @classmethod
    def get_all_shoe(cls):
        return [i.shoe for i in session.query(cls).all()]

class DailyShoeStatsCurrentMonth(Base):
    """当月鞋子使用情况，起初用于计算performance of the month用"""
    __tablename__ = "running_daily_shoe_stats_current_month"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    date = Column(String(32), index=True, nullable=False, unique=False, comment="交易日期")
    shoe = Column(String(32), default="", index=True, nullable=False, comment="鞋子")
    used_times = Column(Integer, default=0, nullable=False, comment="总使用次数")
    distance = Column(Float, nullable=False, comment="总里程", default=0)
    avg_distance = Column(Float, nullable=False, comment="平均每次里程", default=0)
    weight_avg_run_time = Column(String(32), default="", index=False, nullable=False, unique=False,
                                 comment="加权平均每次使用时长")
    weight_avg_heart_rate = Column(Float, nullable=False, comment="加权平均心率", default=0)
    weight_avg_cadence = Column(Float, nullable=False, comment="加权平均步频", default=0)
    weight_avg_stride_length = Column(Float, nullable=False, comment="加权平均步幅", default=0)
    weight_avg_pace = Column(String(32), default="", nullable=False, comment="加权配速")
    top1_pace = Column(String(32), default="", nullable=False, comment="top1 配速")
    top3_pace = Column(String(32), default="", nullable=False, comment="top3 加权评价配速")

    top1_performance = Column(String(32), default="", nullable=False, comment="top1 performance")
    top3_performance = Column(String(32), default="", nullable=False, comment="top3 加权平均performance")
    performance = Column(String(32), default="", nullable=False, comment="加权平均performance")

    rq1 = Column(String(32), default="", nullable=False, comment="rq1分数")
    rq3 = Column(String(32), default="", nullable=False, comment="rq3分数")
    rq = Column(String(32), default="", nullable=False, comment="rq分数")
    rq_inc1 = Column(String(32), default="", nullable=False, comment="rq_inc1")
    rq_inc3 = Column(String(32), default="", nullable=False, comment="rq_inc3")
    rq_inc = Column(String(32), default="", nullable=False, comment="rq_inc")

    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    __table_args__ = (
        Index('idx_date_shoe', "date", 'shoe', unique=True),
    )

    def __str__(self):
        return f"object : <{self.date} {self.shoe}>"


class DailyShoeStats(Base):
    __tablename__ = "running_daily_shoe_stats"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    date = Column(String(32), index=True, nullable=False, unique=False, comment="交易日期")
    shoe = Column(String(32), default="", index=True, nullable=False, comment="鞋子")
    total_used_times = Column(Integer, default=0, nullable=False, comment="总使用次数")
    total_distance = Column(Float, nullable=False, comment="总里程", default=0)
    avg_distance = Column(Float, nullable=False, comment="平均每次里程", default=0)
    weight_avg_run_time = Column(String(32), default="", index=False, nullable=False, unique=False,
                                 comment="加权平均每次使用时长")
    weight_avg_heart_rate = Column(Float, nullable=False, comment="加权平均心率", default=0)
    weight_avg_cadence = Column(Float, nullable=False, comment="加权平均步频", default=0)
    weight_avg_stride_length = Column(Float, nullable=False, comment="加权平均步幅", default=0)
    weight_avg_pace = Column(String(32), default="", nullable=False, comment="加权配速")
    top1_pace = Column(String(32), default="", nullable=False, comment="top1 配速")
    top1_performance = Column(String(32), default="", nullable=False, comment="top1 performance")
    top3_pace = Column(String(32), default="", nullable=False, comment="top3 加权评价配速")
    top3_performance = Column(String(32), default="", nullable=False, comment="top3 加权平均performance")
    rq1 = Column(String(32), default="", nullable=False, comment="rq1分数")
    rq3 = Column(String(32), default="", nullable=False, comment="rq3分数")
    rq = Column(String(32), default="", nullable=False, comment="rq分数")
    rq_inc1 = Column(String(32), default="", nullable=False, comment="rq_inc1")
    rq_inc3 = Column(String(32), default="", nullable=False, comment="rq_inc3")
    rq_inc = Column(String(32), default="", nullable=False, comment="rq_inc")
    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    __table_args__ = (
        Index('idx_date_shoe', "date", 'shoe', unique=True),
    )

    def __str__(self):
        return f"object : <{self.date} {self.shoe}>"

class DailyShoeScore(Base):
    __tablename__ = "running_daily_shoe_score"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    date = Column(String(32), index=True, nullable=False, unique=False, comment="交易日期")
    shoe = Column(String(32), default="", index=True, nullable=False, comment="鞋子")
    order = Column(Integer, nullable=False, comment="", default=99999)
    E = Column(Float, nullable=False, comment="", default=0)
    M = Column(Float, nullable=False, comment="", default=0)
    T = Column(Float, nullable=False, comment="", default=0)
    I = Column(Float, nullable=False, comment="", default=0)
    R = Column(Float, nullable=False, comment="", default=0)
    distance_score = Column(Float, nullable=False, comment="", default=0)
    special_score = Column(Float, nullable=False, comment="", default=0)
    count_shoe_of_the_month = Column(Float, nullable=False, comment="", default=0)
    count_performance_of_the_month = Column(Float, nullable=False, comment="", default=0)
    score = Column(Float, nullable=False, comment="", default=0)
    E_avg_pace = Column(String(32), default="", index=False, nullable=False, comment="")
    E_avg_performance = Column(Float, nullable=False, comment="", default=0)
    E_rq = Column(Float, nullable=False, comment="", default=0)
    E_rq_inc = Column(Float, nullable=False, comment="", default=0)

    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    __table_args__ = (
        Index('idx_date_shoe_unique', "date", 'shoe', unique=True),
        Index('idx_date_shoe', "date", 'shoe', unique=False),
    )

    @classmethod
    def add_record(cls, date, shoe, data_dict):
        if session.query(cls).filter(cls.date == date,
                                     cls.shoe == shoe
                                     ).count() != 0:
            a = session.query(cls).filter(cls.date == date,
                                     cls.shoe == shoe).first()
        else:
            a = cls()
            a.date = date
            a.shoe = shoe
        a.order = data_dict["order"]
        if data_dict["E_distance"] == 0:
            a.E = 0
        else:
            a.E = data_dict["E"]
        if data_dict["M_distance"] == 0:
            a.M = 0
        else:
            a.M = data_dict["M"]
        if data_dict["T_distance"] == 0:
            a.T = 0
        else:
            a.T = data_dict["T"]
        if data_dict["I_distance"] == 0:
            a.I = 0
        else:
            a.I = data_dict["I"]
        if data_dict["R_distance"] == 0:
            a.R = 0
        else:
            a.R = data_dict["R"]
        a.distance_score = data_dict["distance_score"]
        a.special_score = data_dict["special_score"]
        a.count_shoe_of_the_month = data_dict["count_shoe_of_the_month"]
        a.count_performance_of_the_month = data_dict["count_performance_of_the_month"]
        a.score = data_dict["score"]
        a.E_avg_pace = data_dict["E_avg_pace"]
        a.E_avg_performance = data_dict["E_avg_performance"]
        a.E_rq = data_dict["E_rq"]
        a.E_rq_inc = data_dict["E_rq_inc"]
        a.uptime = datetime.datetime.now()

        try:
            session.add(a)
            session.commit()
        except Exception as e:
            session.rollback()
            print(e)

class DailyShoeStatsEMTIR(Base):
    __tablename__ = "running_daily_shoe_stats_EMTIR"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    date = Column(String(32), index=True, nullable=False, unique=False, comment="交易日期")
    shoe = Column(String(32), default="", index=True, nullable=False, comment="鞋子")
    EMTIR = Column(String(32), default="E", index=True, nullable=False, comment="EMTIR")
    total_used_times = Column(Integer, default=0, nullable=False, comment="总使用次数")
    total_distance = Column(Float, nullable=False, comment="总里程", default=0)
    avg_distance = Column(Float, nullable=False, comment="平均每次里程", default=0)
    weight_avg_run_time = Column(String(32), default="", index=False, nullable=False, unique=False,
                                 comment="加权平均每次使用时长")
    weight_avg_heart_rate = Column(Float, nullable=False, comment="加权平均心率", default=0)
    weight_avg_cadence = Column(Float, nullable=False, comment="加权平均步频", default=0)
    weight_avg_stride_length = Column(Float, nullable=False, comment="加权平均步幅", default=0)
    weight_avg_pace = Column(String(32), default="", nullable=False, comment="加权配速")
    top1_pace = Column(String(32), default="", nullable=False, comment="top1 配速")
    top1_performance = Column(String(32), default="", nullable=False, comment="top1 performance")
    avg_pace = Column(String(32), default="", nullable=False, comment="加权评价配速")
    avg_performance = Column(String(32), default="", nullable=False, comment="加权平均performance")
    rq1 = Column(String(32), default="", nullable=False, comment="rq1分数")
    rq3 = Column(String(32), default="", nullable=False, comment="rq3分数")
    rq = Column(String(32), default="", nullable=False, comment="rq分数")
    rq_inc1 = Column(String(32), default="", nullable=False, comment="rq_inc1")
    rq_inc3 = Column(String(32), default="", nullable=False, comment="rq_inc3")
    rq_inc = Column(String(32), default="", nullable=False, comment="rq_inc")
    uptime = Column(
        DateTime, onupdate=datetime.datetime.now, comment="最后更新时间")

    __table_args__ = (
        Index('idx_date_shoe_unique', "date", 'shoe', 'EMTIR', unique=True),
        Index('idx_date_shoe', "date", 'shoe', 'EMTIR', unique=False),
    )

    def __str__(self):
        return f"object : <{self.date} {self.shoe}>"

    @classmethod
    def get_group_total_distance(cls, today):
        df_sql = text(f"""
        SELECT shoe,SUM(total_distance)/500 as distance_score FROM `running_daily_shoe_stats_emtir`
        WHERE DATE = '{today}' GROUP BY shoe
        """)
        df = pd.read_sql(df_sql, engine_running)
        return df

if __name__ == "__main__":
    now = datetime.datetime.now()

    print(datetime.datetime.now() - now)
