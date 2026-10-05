import yfinance as yf
import pandas as pd

data=pd.read_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/constituents.csv")

tickers=data["Symbol"].tolist()  

tickers=[ticker.replace(".","-") for ticker in tickers] # replacing . to - for yfinance api readability

prices=yf.download(tickers,start="2024-09-17", end="2026-09-17",interval="1d",auto_adjust=True)["Close"] # downloading all the stock data at once
                                                                                # to avoid multiple api calls

prices.to_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/prices.csv")
