# region imports
from AlgorithmImports import *
# endregion


class MultiSourceCustomDataAlgorithm(QCAlgorithm):
    """
    Demonstrates loading custom data from three sources:
    1. GitHub (REMOTE_FILE)
    2. Dropbox (REMOTE_FILE)
    3. QuantConnect Object Store (OBJECT_STORE)

    Also creates example CSV files in the Object Store for reference.
    """

    def initialize(self) -> None:
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)

        # Seed initial prices for smoother indicator warm-up
        self.settings.seed_initial_prices = True

        # Create example CSV files in the Object Store
        self._create_example_csv_files()

        # Subscribe to custom data sources
        self._github_data = self.add_data(GitHubCustomData, "GH")
        self._dropbox_data = self.add_data(DropboxCustomData, "DB")
        self._object_store_data = self.add_data(ObjectStoreCustomData, "OS")

        # Schedule rebalancing at midnight (daily data)
        self.schedule.on(
            self.date_rules.every_day(),
            self.time_rules.at(0, 0),
            self._rebalance
        )

    def _create_example_csv_files(self) -> None:
        """Create example CSV files in the Object Store."""
        github_csv_content = """Date,Ticker,Value,Signal
2020-01-02,AAPL,150.0,1
2020-01-02,MSFT,160.0,1
2020-01-02,GOOGL,1350.0,-1
2020-01-03,AAPL,155.0,1
2020-01-03,MSFT,158.0,-1
2020-01-03,GOOGL,1360.1,1"""

        dropbox_csv_content = """Date,Ticker,Value,Signal
2020-01-02,SPY,320.0,1
2020-01-02,QQQ,220.0,-1
2020-01-02,IWM,160.0,1
2020-01-03,SPY,325.0,-1
2020-01-03,QQQ,225.0,1
2020-01-03,IWM,158.0,-1"""

        object_store_csv_content = """Date,Ticker,Value,Signal
2020-01-02,TSLA,430.0,1
2020-01-02,AMZN,1900.0,-1
2020-01-02,NFLX,340.0,1
2020-01-03,TSLA,440.0,-1
2020-01-03,AMZN,1920.0,1
2020-01-03,NFLX,335.0,-1"""

        if not self.object_store.contains_key("github_example.csv"):
            self.object_store.save("github_example.csv", github_csv_content)
            self.log("Created github_example.csv in Object Store")

        if not self.object_store.contains_key("dropbox_example.csv"):
            self.object_store.save("dropbox_example.csv", dropbox_csv_content)
            self.log("Created dropbox_example.csv in Object Store")

        if not self.object_store.contains_key("object_store_example.csv"):
            self.object_store.save("object_store_example.csv", object_store_csv_content)
            self.log("Created object_store_example.csv in Object Store")

    def _get_or_add_symbol(self, ticker: str) -> Symbol:
        """Get or add a security by ticker string and return its Symbol."""
        symbol = Symbol.create(ticker, SecurityType.EQUITY, Market.USA)
        if not self.securities.contains_key(symbol):
            self.add_equity(ticker)
        return symbol

    def _rebalance(self) -> None:
        """Process any available custom data and trade based on signals."""
        # This method is called daily at midnight.
        # In a real strategy, you would process the latest slice data here.
        pass

    def on_data(self, slice: Slice) -> None:
        for symbol, data in slice.get(GitHubCustomData).items():
            if not data:
                continue
            self._process_custom_data(data, "GitHub")

        for symbol, data in slice.get(DropboxCustomData).items():
            if not data:
                continue
            self._process_custom_data(data, "Dropbox")

        for symbol, data in slice.get(ObjectStoreCustomData).items():
            if not data:
                continue
            self._process_custom_data(data, "ObjectStore")

    def _process_custom_data(self, data, source: str) -> None:
        symbol = self._get_or_add_symbol(data.ticker)
        if symbol is None:
            return
        if data.signal == 1 and not self.portfolio[symbol].is_long:
            self.set_holdings(symbol, 0.33)
            self.log(f"[{source}] Buy {data.ticker} at {self.time}")
        elif data.signal == -1 and not self.portfolio[symbol].is_short:
            self.set_holdings(symbol, -0.33)
            self.log(f"[{source}] Short {data.ticker} at {self.time}")


class GitHubCustomData(PythonData):
    """
    Custom data source from a GitHub raw CSV file.
    """

    def get_source(self, config: SubscriptionDataConfig, date: datetime, is_live_mode: bool) -> SubscriptionDataSource:
        # Use the example CSV we placed in the Object Store for backtesting
        # In live mode, you would point to a real GitHub raw URL
        if is_live_mode:
            return SubscriptionDataSource(
                "https://raw.githubusercontent.com/QuantConnect/Documentation/master/Resources/datasets/custom-data/bitstampusd.csv",
                SubscriptionTransportMedium.REMOTE_FILE
            )
        return SubscriptionDataSource(
            "github_example.csv",
            SubscriptionTransportMedium.OBJECT_STORE
        )

    def reader(self, config: SubscriptionDataConfig, line: str, date: datetime, is_live_mode: bool) -> BaseData:
        if not line.strip() or not line[0].isdigit():
            return None

        data = [x.strip() for x in line.split(',')]
        if len(data) < 4:
            return None

        try:
            trade = GitHubCustomData()
            trade.symbol = config.symbol
            trade.time = datetime.strptime(data[0], "%Y-%m-%d")
            trade.end_time = trade.time + timedelta(1)
            trade.ticker = data[1]
            trade.value = float(data[2])
            trade.signal = int(data[3])
            return trade
        except Exception:
            return None


class DropboxCustomData(PythonData):
    """
    Custom data source from a Dropbox shared link.
    """

    def get_source(self, config: SubscriptionDataConfig, date: datetime, is_live_mode: bool) -> SubscriptionDataSource:
        # Use the example CSV we placed in the Object Store for backtesting
        # In live mode, you would point to a real Dropbox shared link
        if is_live_mode:
            return SubscriptionDataSource(
                "https://www.dropbox.com/s/abc123/example.csv?dl=1",
                SubscriptionTransportMedium.REMOTE_FILE
            )
        return SubscriptionDataSource(
            "dropbox_example.csv",
            SubscriptionTransportMedium.OBJECT_STORE
        )

    def reader(self, config: SubscriptionDataConfig, line: str, date: datetime, is_live_mode: bool) -> BaseData:
        if not line.strip() or not line[0].isdigit():
            return None

        data = [x.strip() for x in line.split(',')]
        if len(data) < 4:
            return None

        try:
            trade = DropboxCustomData()
            trade.symbol = config.symbol
            trade.time = datetime.strptime(data[0], "%Y-%m-%d")
            trade.end_time = trade.time + timedelta(1)
            trade.ticker = data[1]
            trade.value = float(data[2])
            trade.signal = int(data[3])
            return trade
        except Exception:
            return None


class ObjectStoreCustomData(PythonData):
    """
    Custom data source from the QuantConnect Object Store.
    """

    def get_source(self, config: SubscriptionDataConfig, date: datetime, is_live_mode: bool) -> SubscriptionDataSource:
        return SubscriptionDataSource(
            "object_store_example.csv",
            SubscriptionTransportMedium.OBJECT_STORE
        )

    def reader(self, config: SubscriptionDataConfig, line: str, date: datetime, is_live_mode: bool) -> BaseData:
        if not line.strip() or not line[0].isdigit():
            return None

        data = [x.strip() for x in line.split(',')]
        if len(data) < 4:
            return None

        try:
            trade = ObjectStoreCustomData()
            trade.symbol = config.symbol
            trade.time = datetime.strptime(data[0], "%Y-%m-%d")
            trade.end_time = trade.time + timedelta(1)
            trade.ticker = data[1]
            trade.value = float(data[2])
            trade.signal = int(data[3])
            return trade
        except Exception:
            return None
