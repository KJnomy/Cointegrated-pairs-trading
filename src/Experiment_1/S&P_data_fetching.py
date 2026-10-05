import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.tsa.stattools as sma


data=pd.read_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/constituents.csv")

tickers=data["Symbol"].tolist()  

tickers=[ticker.replace(".","-") for ticker in tickers] # replacing . to - for yfinance api readability

prices=yf.download(tickers,start="2023-01-01", end="2026-01-01",interval="1d",auto_adjust=True)["Close"] # downloading all the stock data at once
                                                                                # to avoid multiple api calls

prices.to_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/prices.csv")
