import statsmodels.tsa.stattools as sm
import yfinance as yf
import pandas as pd

s1=input("Enter your stock 1: ")
s2=input("Enter your stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)


y= df1["Close"]
x=df2["Close"]

x=sm.add_constant(x) # adding a constant for intercept

model=sm.OLS(y,x)
result=model.fit()

a= result.params.iloc[0]
beta= result.params.iloc[1]

spread = df1["Close"] - a - beta*df2["Close"]

# Calculating the rolling  Z-score to find the signals to long or short

roll_spread_mean= spread.rolling(window=30).mean()
roll_spread_sd=spread.rolling(window=30).std()

roll_zscore=(spread - roll_spread_mean)/(roll_spread_sd)
roll_zscore=roll_zscore.dropna()
print(roll_zscore)

'''
 Now let's generate signals and trade
 The rule I am taking here is I will short when the roll_zscore is above 2 and will long if 
 it is below -2 and exit near 0

'''

'''
Here i have taken an array "Trades" which stores the position at that time so  
-1 represents short , 0 represents exit , 1 represents long , "p" represents its
still in position, "np" represents not in position
'''

Trades=[]

position=0 # initial position is zero its not exit

for i in range(0,len(roll_zscore)):

    z= roll_zscore.iloc[i]
    date = roll_zscore.index[i]

    if position==0:
        if z>= 2:
             position=-1
             Trades.append([date,"Entry Short",z])

        elif z<= -2:
             position=1
             Trades.append([date,"Entry Long",z])

    elif position == 1:

         if z>=-0.4:
              position=0
              Trades.append([date,"Exit long",z])

    elif position==-1:
         if z<= 0.4:
              position=0
              Trades.append([date,"Exit short",z])
         
Trades=pd.DataFrame(Trades,columns=["Date","Action","Z-score"])

print(Trades)


