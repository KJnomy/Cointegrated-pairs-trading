import yfinance as yf
import pandas as pd
import numpy as np

data=pd.read_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/constituents.csv")

tickers=data["Symbol"].tolist()  

tickers=[ticker.replace(".","-") for ticker in tickers] # replacing . to - for yfinance api readability

prices=yf.download(tickers,period="2y",interval="1d",auto_adjust=True)["Close"] # downloading all the stock data at once
                                                                                # to avoid multiple api calls

prices=prices.dropna(axis=1,thresh=len(prices)*0.4) # we are removing those stocks whose data has more than 
                                                    # 60 percent na values

returns=prices.pct_change()  # calculating the returns of each day w.r.t prev day

corr_matrix= returns.corr()

pairs=[]
for i in range(len(corr_matrix.columns)):
    for j in range(i+1,len(corr_matrix.columns)):
        if corr_matrix.iloc[i,j]>=0.7:
            pairs.append([corr_matrix.columns[i],corr_matrix.columns[j],corr_matrix.iloc[i,j]])

pairs=pd.DataFrame(pairs,columns=("Pair1","Pair2","Correlation"))

print(pairs)