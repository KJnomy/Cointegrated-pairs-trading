import yfinance as yf
import pandas as pd
import math
import os

s1=input("Enter stock 1: ")
s2=input("Enter stock 2: ")

df1 = yf.download(s1, start="2024-08-14", end="2026-08-14", interval="1d")
df2 = yf.download(s2, start="2024-08-14", end="2026-08-14", interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

df1, df2 = df1.align(df2, join="inner")  #this will protect us from data misalignment

y=df1["Close"]
x=df2["Close"]

train_y=y.iloc[0 : math.floor(len(y)*0.65)]  #taking 65 percent of whole data for training
test_y=y.iloc[math.floor(len(y)*0.65) : len(y)] #rest 35 percent for testing

train_x=x.iloc[0 : math.floor(len(x)*0.65)]
test_x=x.iloc[math.floor(len(x)*0.65) : len(x)]

os.makedirs("data", exist_ok=True)

train_y.to_csv("data/train_y.csv")
train_x.to_csv("data/train_x.csv")
test_y.to_csv("data/test_y.csv")
test_x.to_csv("data/test_x.csv")

print("Saved train_y, train_x, test_y, test_x to data/")
