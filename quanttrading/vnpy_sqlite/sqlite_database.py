from datetime import datetime, timedelta
from typing import List
import logging

from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    FloatField, IntegerField,
    Model,
    PostgresqlDatabase,
    SqliteDatabase as PeeweeSqliteDatabase,
    ModelSelect,
    ModelDelete,
    chunked,
    fn
)

from constant import Exchange, Interval
from datatypes import BarData, TickData
from utility import get_file_path
from database import (
    BaseDatabase,
    BarOverview,
    DB_TZ,
    TickOverview,
    convert_tz
)

logger = logging.getLogger(__name__)

path: str = str(get_file_path("database.db"))
db: PeeweeSqliteDatabase = PeeweeSqliteDatabase(path)

class BaseModel(Model):
    class Meta:
        database: PeeweeSqliteDatabase = db

class DbDailyProfit(BaseModel):
    """ 
    daily profit data 
    there could be multiple data for one day. the last one is the latest one.
    """
    id: AutoField = AutoField()
    date: datetime = DateTimeField()
    realised_pnl: float = FloatField()
    total_pnl: float = FloatField()


class DbBarData(Model):
    """K线数据表映射对象"""

    id: AutoField = AutoField()

    symbol: str = CharField()
    exchange: str = CharField()
    datetime: datetime = DateTimeField()
    interval: str = CharField()

    volume: float = FloatField()
    turnover: float = FloatField()
    open_interest: float = FloatField()
    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()

    class Meta:
        database: PeeweeSqliteDatabase = db
        indexes: tuple = ((("symbol", "exchange", "interval", "datetime"), True),)


class DbTickData(Model):
    """TICK数据表映射对象"""

    id: AutoField = AutoField()

    symbol: str = CharField()
    exchange: str = CharField()
    datetime: datetime = DateTimeField()

    name: str = CharField()
    volume: float = FloatField()
    turnover: float = FloatField()
    open_interest: float = FloatField()
    last_price: float = FloatField()
    last_volume: float = FloatField()
    limit_up: float = FloatField()
    limit_down: float = FloatField()

    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    pre_close: float = FloatField()

    bid_price_1: float = FloatField()
    bid_price_2: float = FloatField(null=True)
    bid_price_3: float = FloatField(null=True)
    bid_price_4: float = FloatField(null=True)
    bid_price_5: float = FloatField(null=True)

    ask_price_1: float = FloatField()
    ask_price_2: float = FloatField(null=True)
    ask_price_3: float = FloatField(null=True)
    ask_price_4: float = FloatField(null=True)
    ask_price_5: float = FloatField(null=True)

    bid_volume_1: float = FloatField()
    bid_volume_2: float = FloatField(null=True)
    bid_volume_3: float = FloatField(null=True)
    bid_volume_4: float = FloatField(null=True)
    bid_volume_5: float = FloatField(null=True)

    ask_volume_1: float = FloatField()
    ask_volume_2: float = FloatField(null=True)
    ask_volume_3: float = FloatField(null=True)
    ask_volume_4: float = FloatField(null=True)
    ask_volume_5: float = FloatField(null=True)

    localtime: datetime = DateTimeField(null=True)

    class Meta:
        database: PeeweeSqliteDatabase = db
        indexes: tuple = ((("symbol", "exchange", "datetime"), True),)


class DbBarOverview(Model):
    """K线汇总数据表映射对象"""

    id: AutoField = AutoField()

    symbol: str = CharField()
    exchange: str = CharField()
    interval: str = CharField()
    count: int = IntegerField()
    start: datetime = DateTimeField()
    end: datetime = DateTimeField()

    class Meta:
        database: PeeweeSqliteDatabase = db
        indexes: tuple = ((("symbol", "exchange", "interval"), True),)


class DbTickOverview(Model):
    """Tick汇总数据表映射对象"""

    id: AutoField = AutoField()

    symbol: str = CharField()
    exchange: str = CharField()
    count: int = IntegerField()
    start: datetime = DateTimeField()
    end: datetime = DateTimeField()

    class Meta:
        database: PeeweeSqliteDatabase = db
        indexes: tuple = ((("symbol", "exchange"), True),)


class SqliteDatabase(BaseDatabase):
    """SQLite数据库接口"""

    def __init__(self) -> None:
        """"""
        self.db: PeeweeSqliteDatabase = db
        self.db.connect()
        self.db.create_tables([DbBarData, DbTickData, DbBarOverview, DbTickOverview, DbDailyProfit])

    def save_bar_data(self, bars: List[BarData], stream: bool = False) -> bool:
        """保存K线数据"""
        # 读取主键参数
        bar: BarData = bars[0]
        symbol: str = bar.symbol
        exchange: Exchange = bar.exchange
        interval: Interval = bar.interval

        # 将BarData数据转换为字典，并调整时区
        data: list = []

        for bar in bars:
            bar.datetime = convert_tz(bar.datetime)

            d: dict = bar.__dict__
            d["exchange"] = d["exchange"].value
            d["interval"] = d["interval"].value
            d.pop("gateway_name")
            d.pop("vt_symbol")
            data.append(d)

        # 使用upsert操作将数据更新到数据库中
        with self.db.atomic():
            for c in chunked(data, 50):
                DbBarData.insert_many(c).on_conflict_replace().execute()

        # 更新K线汇总数据
        overview: DbBarOverview = DbBarOverview.get_or_none(
            DbBarOverview.symbol == symbol,
            DbBarOverview.exchange == exchange.value,
            DbBarOverview.interval == interval.value,
        )

        if not overview:
            overview = DbBarOverview()
            overview.symbol = symbol
            overview.exchange = exchange.value
            overview.interval = interval.value
            overview.start = bars[0].datetime
            overview.end = bars[-1].datetime
            overview.count = len(bars)
        elif stream:
            overview.end = bars[-1].datetime
            overview.count += len(bars)
        else:
            overview.start = min(bars[0].datetime, overview.start)
            overview.end = max(bars[-1].datetime, overview.end)

            s: ModelSelect = DbBarData.select().where(
                (DbBarData.symbol == symbol)
                & (DbBarData.exchange == exchange.value)
                & (DbBarData.interval == interval.value)
            )
            overview.count = s.count()

        overview.save()

        return True

    def save_tick_data(self, ticks: List[TickData], stream: bool = False) -> bool:
        """保存TICK数据"""
        # 读取主键参数
        tick: TickData = ticks[0]
        symbol: str = tick.symbol
        exchange: Exchange = tick.exchange

        # 将TickData数据转换为字典，并调整时区
        data: list = []
        # print(f"====================={tick=}")

        for tick in ticks:
            tick.datetime = convert_tz(tick.datetime)

            d: dict = tick.__dict__
            d["exchange"] = d["exchange"].value
            d.pop("gateway_name")
            d.pop("vt_symbol")
            d.pop("extra")
            data.append(d)

        # 使用upsert操作将数据更新到数据库中
        with self.db.atomic():
            for c in chunked(data, 10):
                # print(f"{c=} ")
                DbTickData.insert_many(c).on_conflict_replace().execute()

        # 更新Tick汇总数据
        overview: DbTickOverview = DbTickOverview.get_or_none(
            DbTickOverview.symbol == symbol,
            DbTickOverview.exchange == exchange.value,
        )

        if not overview:
            overview: DbTickOverview = DbTickOverview()
            overview.symbol = symbol
            overview.exchange = exchange.value
            overview.start = ticks[0].datetime
            overview.end = ticks[-1].datetime
            overview.count = len(ticks)
        elif stream:
            overview.end = ticks[-1].datetime
            overview.count += len(ticks)
        else:
            overview.start = min(ticks[0].datetime, overview.start)
            overview.end = max(ticks[-1].datetime, overview.end)

            s: ModelSelect = DbTickData.select().where(
                (DbTickData.symbol == symbol)
                & (DbTickData.exchange == exchange.value)
            )
            overview.count = s.count()

        overview.save()

        return True

    def save_daily_pnl(self,
                       date:datetime,
                       totalPnL:float,
                       realisedPnL:float) -> bool:
        daily_pnl:DbDailyProfit = DbDailyProfit()
        daily_pnl.date = date
        daily_pnl.total_pnl = totalPnL
        daily_pnl.realised_pnl = realisedPnL
        daily_pnl.save()

    def load_last_daily_pnl(self) -> DbDailyProfit:
        try:

            daily_pnl:DbDailyProfit = DbDailyProfit.select().order_by(DbDailyProfit.id.desc()).get()
            if daily_pnl:
                if daily_pnl.date.date() == datetime.now().date():
                    return daily_pnl
        except Exception as e:
            logger.info(f"load daily pnl failed. {e.args}")
            
            
    def delete_daily_pnl(self, date:datetime = None, wholeDay:bool = False) -> int:
        """ 
        delete the daily_pnl records. if date provided. delete the record with the same date
        if wholeDay == True. then delete all day records for the date.
        return the number of rows deleted
        """
        if date and wholeDay:
            query = DbDailyProfit.delete().where(DbDailyProfit.date.date() == date.date())

        elif date:
            query = DbDailyProfit.delete().where(DbDailyProfit.date == date)

        else:
            query = DbDailyProfit.delete()
        
        query.execute()


    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> List[BarData]:
        """读取K线数据"""
        s: ModelSelect = (
            DbBarData.select().where(
                (DbBarData.symbol == symbol)
                & (DbBarData.exchange == exchange.value)
                & (DbBarData.interval == interval.value)
                & (DbBarData.datetime >= start)
                & (DbBarData.datetime <= end)
            ).order_by(DbBarData.datetime)
        )

        bars: List[BarData] = []
        for db_bar in s:
            bar: BarData = BarData(
                symbol=db_bar.symbol,
                exchange=Exchange(db_bar.exchange),
                datetime=datetime.fromtimestamp(db_bar.datetime.timestamp(), DB_TZ),
                interval=Interval(db_bar.interval),
                volume=db_bar.volume,
                turnover=db_bar.turnover,
                open_interest=db_bar.open_interest,
                open_price=db_bar.open_price,
                high_price=db_bar.high_price,
                low_price=db_bar.low_price,
                close_price=db_bar.close_price,
                gateway_name="DB"
            )
            bars.append(bar)
        print("sqlite_database: load_bar_data:")
        return bars

    def load_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        """
        get TICK data based on start and end time.
        tick data is one per second. has OHLCV, time, symbol
        """
        s: ModelSelect = (
            DbTickData.select().where(
                (DbTickData.symbol == symbol)
                & (DbTickData.exchange == exchange.value)
                & (DbTickData.datetime >= start)
                & (DbTickData.datetime <= end)
            ).order_by(DbTickData.datetime)
        )

        ticks: List[TickData] = []
        for db_tick in s:
            tick: TickData = TickData(
                symbol=db_tick.symbol,
                exchange=Exchange(db_tick.exchange),
                datetime=datetime.fromtimestamp(db_tick.datetime.timestamp(), DB_TZ),
                name=db_tick.name,
                volume=db_tick.volume,
                turnover=db_tick.turnover,
                open_interest=db_tick.open_interest,
                last_price=db_tick.last_price,
                last_volume=db_tick.last_volume,
                limit_up=db_tick.limit_up,
                limit_down=db_tick.limit_down,
                open_price=db_tick.open_price,
                high_price=db_tick.high_price,
                low_price=db_tick.low_price,
                pre_close=db_tick.pre_close,
                bid_price_1=db_tick.bid_price_1,
                bid_price_2=db_tick.bid_price_2,
                bid_price_3=db_tick.bid_price_3,
                bid_price_4=db_tick.bid_price_4,
                bid_price_5=db_tick.bid_price_5,
                ask_price_1=db_tick.ask_price_1,
                ask_price_2=db_tick.ask_price_2,
                ask_price_3=db_tick.ask_price_3,
                ask_price_4=db_tick.ask_price_4,
                ask_price_5=db_tick.ask_price_5,
                bid_volume_1=db_tick.bid_volume_1,
                bid_volume_2=db_tick.bid_volume_2,
                bid_volume_3=db_tick.bid_volume_3,
                bid_volume_4=db_tick.bid_volume_4,
                bid_volume_5=db_tick.bid_volume_5,
                ask_volume_1=db_tick.ask_volume_1,
                ask_volume_2=db_tick.ask_volume_2,
                ask_volume_3=db_tick.ask_volume_3,
                ask_volume_4=db_tick.ask_volume_4,
                ask_volume_5=db_tick.ask_volume_5,
                localtime=db_tick.localtime,
                gateway_name="DB"
            )
            ticks.append(tick)

        return ticks


    def load_all_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
    ) -> List[TickData]:
        """
        get TICK data based on start and end time.
        tick data is one per second. has OHLCV, time, symbol
        """
        s: ModelSelect = (
            DbTickData.select().where(
                (DbTickData.symbol == symbol)
                & (DbTickData.exchange == exchange.value)
            ).order_by(DbTickData.datetime)
        )

        ticks: List[TickData] = []
        for db_tick in s:
            tick: TickData = TickData(
                symbol=db_tick.symbol,
                exchange=Exchange(db_tick.exchange),
                datetime=datetime.fromtimestamp(db_tick.datetime.timestamp(), DB_TZ),
                name=db_tick.name,
                volume=db_tick.volume,
                turnover=db_tick.turnover,
                open_interest=db_tick.open_interest,
                last_price=db_tick.last_price,
                last_volume=db_tick.last_volume,
                limit_up=db_tick.limit_up,
                limit_down=db_tick.limit_down,
                open_price=db_tick.open_price,
                high_price=db_tick.high_price,
                low_price=db_tick.low_price,
                pre_close=db_tick.pre_close,
                bid_price_1=db_tick.bid_price_1,
                bid_price_2=db_tick.bid_price_2,
                bid_price_3=db_tick.bid_price_3,
                bid_price_4=db_tick.bid_price_4,
                bid_price_5=db_tick.bid_price_5,
                ask_price_1=db_tick.ask_price_1,
                ask_price_2=db_tick.ask_price_2,
                ask_price_3=db_tick.ask_price_3,
                ask_price_4=db_tick.ask_price_4,
                ask_price_5=db_tick.ask_price_5,
                bid_volume_1=db_tick.bid_volume_1,
                bid_volume_2=db_tick.bid_volume_2,
                bid_volume_3=db_tick.bid_volume_3,
                bid_volume_4=db_tick.bid_volume_4,
                bid_volume_5=db_tick.bid_volume_5,
                ask_volume_1=db_tick.ask_volume_1,
                ask_volume_2=db_tick.ask_volume_2,
                ask_volume_3=db_tick.ask_volume_3,
                ask_volume_4=db_tick.ask_volume_4,
                ask_volume_5=db_tick.ask_volume_5,
                localtime=db_tick.localtime,
                gateway_name="DB"
            )
            ticks.append(tick)

        return ticks



    def load_tick_data_byHours(
        self,
        symbol: str,
        exchange: Exchange,
        dateHour:datetime = datetime.now(DB_TZ),
        tick_nums:int = 3600
    ) -> List[TickData]:
        """
        get tick data for the latest available x days.
        tick data is one per second. has OHLCV, time, symbol
        :dateHour : the hour which we would like to get ticks from
        :tick_nums: number of tickdata need to be returned.
        # return only one hour's data --> default 3600 ticks
        """
        # print(f"{dateHour.hour=}")
        # for i in range(1000):
        #     # current_date = datetime.now(DB_TZ) - timedelta(i)
        #     # current_date = current_date.replace(hour=23)

        # return only one hour data --> 3600
        print(f"load_tick_data_byHours... dateHour: {dateHour}")
        if not (tick_nums and 0 < tick_nums <=3600):
            print("load_tick_data_byHours...1")
            tick_nums = 3600
        print(f"load_tick_data_byHours... 2 tick_nums {tick_nums}")
        s: ModelSelect = (
            DbTickData.select().where(
                (DbTickData.symbol == symbol)
                & (DbTickData.exchange == exchange.value)
                & (DbTickData.datetime.hour == dateHour.hour)
            ).order_by(DbTickData.datetime.desc()).limit(tick_nums)
        )
        print(f"load_tick_data_byHours... 3 ")
        ticks: List[TickData] = []
        for db_tick in s:
            tick: TickData = TickData(
                symbol=db_tick.symbol,
                exchange=Exchange(db_tick.exchange),
                datetime=datetime.fromtimestamp(db_tick.datetime.timestamp(), DB_TZ),
                name=db_tick.name,
                volume=db_tick.volume,
                # turnover=db_tick.turnover,
                # open_interest=db_tick.open_interest,
                last_price=db_tick.last_price,
                # last_volume=db_tick.last_volume,
                # limit_up=db_tick.limit_up,
                # limit_down=db_tick.limit_down,
                open_price=db_tick.open_price,
                high_price=db_tick.high_price,
                low_price=db_tick.low_price,
                pre_close=db_tick.pre_close,
                # bid_price_1=db_tick.bid_price_1,
                # bid_price_2=db_tick.bid_price_2,
                # bid_price_3=db_tick.bid_price_3,
                # bid_price_4=db_tick.bid_price_4,
                # bid_price_5=db_tick.bid_price_5,
                # ask_price_1=db_tick.ask_price_1,
                # ask_price_2=db_tick.ask_price_2,
                # ask_price_3=db_tick.ask_price_3,
                # ask_price_4=db_tick.ask_price_4,
                # ask_price_5=db_tick.ask_price_5,
                # bid_volume_1=db_tick.bid_volume_1,
                # bid_volume_2=db_tick.bid_volume_2,
                # bid_volume_3=db_tick.bid_volume_3,
                # bid_volume_4=db_tick.bid_volume_4,
                # bid_volume_5=db_tick.bid_volume_5,
                # ask_volume_1=db_tick.ask_volume_1,
                # ask_volume_2=db_tick.ask_volume_2,
                # ask_volume_3=db_tick.ask_volume_3,
                # ask_volume_4=db_tick.ask_volume_4,
                # ask_volume_5=db_tick.ask_volume_5,
                # localtime=db_tick.localtime,
                gateway_name="DB"
            )
            ticks.append(tick)
            # print(tick.datetime)
        
        print(len(ticks))
        return ticks

    def delete_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval
    ) -> int:
        """删除K线数据"""
        d: ModelDelete = DbBarData.delete().where(
            (DbBarData.symbol == symbol)
            & (DbBarData.exchange == exchange.value)
            & (DbBarData.interval == interval.value)
        )
        count: int = d.execute()

        # 删除K线汇总数据
        d2: ModelDelete = DbBarOverview.delete().where(
            (DbBarOverview.symbol == symbol)
            & (DbBarOverview.exchange == exchange.value)
            & (DbBarOverview.interval == interval.value)
        )
        d2.execute()

        return count

    def delete_tick_data(
        self,
        symbol: str,
        exchange: Exchange
    ) -> int:
        """删除TICK数据"""
        d: ModelDelete = DbTickData.delete().where(
            (DbTickData.symbol == symbol)
            & (DbTickData.exchange == exchange.value)
        )
        count: int = d.execute()

        # 删除Tick汇总数据
        d2: ModelDelete = DbTickOverview.delete().where(
            (DbTickOverview.symbol == symbol)
            & (DbTickOverview.exchange == exchange.value)
        )
        d2.execute()

        return count

    def get_bar_overview(self) -> List[BarOverview]:
        """查询数据库中的K线汇总信息"""
        # 如果已有K线，但缺失汇总信息，则执行初始化
        data_count: int = DbBarData.select().count()
        overview_count: int = DbBarOverview.select().count()
        if data_count and not overview_count:
            self.init_bar_overview()

        s: ModelSelect = DbBarOverview.select()
        overviews: List[BarOverview] = []
        for overview in s:
            overview.exchange = Exchange(overview.exchange)
            overview.interval = Interval(overview.interval)
            overviews.append(overview)
        return overviews

    def get_tick_overview(self) -> List[TickOverview]:
        """查询数据库中的Tick汇总信息"""
        s: ModelSelect = DbTickOverview.select()
        overviews: list = []
        for overview in s:
            overview.exchange = Exchange(overview.exchange)
            overviews.append(overview)
        return overviews

    def init_bar_overview(self) -> None:
        """初始化数据库中的K线汇总信息"""
        s: ModelSelect = (
            DbBarData.select(
                DbBarData.symbol,
                DbBarData.exchange,
                DbBarData.interval,
                fn.COUNT(DbBarData.id).alias("count")
            ).group_by(
                DbBarData.symbol,
                DbBarData.exchange,
                DbBarData.interval
            )
        )

        for data in s:
            overview: DbBarOverview = DbBarOverview()
            overview.symbol = data.symbol
            overview.exchange = data.exchange
            overview.interval = data.interval
            overview.count = data.count

            start_bar: DbBarData = (
                DbBarData.select()
                .where(
                    (DbBarData.symbol == data.symbol)
                    & (DbBarData.exchange == data.exchange)
                    & (DbBarData.interval == data.interval)
                )
                .order_by(DbBarData.datetime.asc())
                .first()
            )
            overview.start = start_bar.datetime

            end_bar: DbBarData = (
                DbBarData.select()
                .where(
                    (DbBarData.symbol == data.symbol)
                    & (DbBarData.exchange == data.exchange)
                    & (DbBarData.interval == data.interval)
                )
                .order_by(DbBarData.datetime.desc())
                .first()
            )
            overview.end = end_bar.datetime

            overview.save()
