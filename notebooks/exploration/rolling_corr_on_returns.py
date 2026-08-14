import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

s1=input("Enter your stock 1: ")
s2=input("Enter your stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)


returns= pd.concat([df1["Close"].pct_change(),
                   df2["Close"].pct_change()],
                   axis=1).dropna()
returns.columns=["return_s1","return_s2"]


rolling_corr= returns["return_s1"].rolling(window=30).corr(returns["return_s2"])

avg_corr= rolling_corr.dropna().mean()

plt.plot(rolling_corr.index,rolling_corr)
plt.xlabel("Date")
plt.ylabel("Corr-coef")
plt.title(f"average corr= {avg_corr}")
plt.show()

