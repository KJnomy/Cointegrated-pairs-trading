import statsmodels.tsa.stattools as sm
import yfinance as yf
import pandas as pd

s1=input("Enter your stock 1: ")
s2=input("Enter your stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

prices = pd.concat([df1["Close"], df2["Close"]], axis=1).dropna()

prices.columns = [s1,s2]

test = sm.coint(prices[s1],prices[s2])
print(test)

# Now using ADF test to test the stationarity of spread.

y= df1["Close"]
x=df2["Close"]

x=sm.add_constant(x) # adding a constant for intercept

model=sm.OLS(y,x)
result=model.fit()

a= result.params.iloc[0]
beta= result.params.iloc[1]

spread = df1["Close"] - a - beta*df2["Close"]

adf_test=sm.adfuller(spread)

print("Summary of ADF test :")
print(adf_test)

