#here i have to make a rolling correlation for 30 day
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt

df1= yf.download("KO",period="2y",interval="1d")
df2= yf.download("PEP",period="2y",interval="1d")
df1.columns= df1.columns.droplevel(1)
df2.columns= df2.columns.droplevel(1)

rc=[] #array for rolling corr
time=[]  # array for time record
for n in range(1,len(df1)-29):
    a= pd.Series(df1["Close"][n:n+29])
    b= pd.Series(df2["Close"][n:n+29])
    corrcoef=a.corr(b)
    time.append(df1.index[n])
    rc.append(corrcoef)
    

plt.plot(time,rc,label="Rolling Correlation")
plt.xlabel("Time")
plt.ylabel("Corr-coef")

plt.show()