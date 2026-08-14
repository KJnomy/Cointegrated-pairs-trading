import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm

s1=input("Enter your stock 1: ")
s2=input("Enter your stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

y= df1["Close"]
x= df2["Close"]

x=sm.add_constant(x)

model=sm.OLS(y,x)

result=model.fit()

print(result.summary())