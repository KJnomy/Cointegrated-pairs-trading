import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

df1=yf.download("KO",period="2y",interval="1d")
df2=yf.download("PEP",period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

rolling_corr=(df1["Close"]).rolling(window=30).corr(df2["Close"])

plt.plot(rolling_corr.index,rolling_corr,label="Rolling Correlation")
plt.xlabel("Date")
plt.ylabel("Corr-coef")
plt.show()