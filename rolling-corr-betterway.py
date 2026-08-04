import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

s1=input("Enter your stock 1: ")
s2=input("Enter your stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

rolling_corr=(df1["Close"]).rolling(window=30).corr(df2["Close"])

plt.plot(rolling_corr.index,rolling_corr,label="Rolling Correlation")
plt.xlabel("Date")
plt.ylabel("Corr-coef")
plt.show()