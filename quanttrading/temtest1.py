from constant import ChartInterval
import yfinance as yf

print(f"Interval is {ChartInterval}")
print(f"Interval is {ChartInterval.M1}")
print(f"Interval is {ChartInterval.M1.name}")
print(f"Interval is {ChartInterval.M1.value}")

msft = yf.Ticker("MSFT")

# get all stock info
print(f"info is {msft}")

# get historical market data
hist = msft.history(period="1mo",)

print(f"hist is {hist}")