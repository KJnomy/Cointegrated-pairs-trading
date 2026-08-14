import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
# aapl= pd.read_csv("Ticker data/AAPL.csv",skiprows=[1,2])
# cocacola=pd.read_csv("Ticker data/KO.csv")
# pepsi=pd.read_csv("Ticker data/PEP.csv")

# plt.plot(aapl["Close"],skiprows=[1,2])

df1= yf.download("KO",period="2y",interval="1d")
df2= yf.download("PEP",period="2y",interval="1d")
df1.columns= df1.columns.droplevel(1)
df2.columns= df2.columns.droplevel(1)

plt.plot(df1.index,df1["Close"], label="Cocacola")
plt.plot(df2.index,df2["Close"],label="Pepsi")

plt.xlabel("date")
plt.ylabel("closing price")

plt.legend()
plt.show()