import yfinance as yf
import pandas as pd
import statsmodels.tsa.stattools as sm

s1=input("Enter stock 1: ")
s2=input("Enter stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

y=df1["Close"]
x=df2["Close"]

x=sm.add_constant(x)

model=sm.OLS(y,x)
result=model.fit()

a=result.params.iloc[0]
beta=result.params.iloc[1]

spread=df1["Close"]-a-beta*df2["Close"]

roll_spread_mean=spread.rolling(window=30).mean()
roll_spread_std=spread.rolling(window=30).std()

roll_zscore=(spread-roll_spread_mean)/roll_spread_std

roll_zscore=roll_zscore.dropna()

Trades=[]
Daily_data=[]
position_s1=0
position_s2=0

for i in range(1,len(roll_zscore)):
    date=roll_zscore.index[i]
    z=roll_zscore.iloc[i-1]
    price_s1=df1["Close"].loc[date]   #i+29 bcz i am running loop over roll_zscore so 30 day gap
    price_s2=df2["Close"].loc[date]

    if position_s1==0:
        if z>=2:
            position_s1= -1   
            position_s2= beta        # short s1 and long s2
            Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
        elif z<=-2:
            position_s1= 1
            position_s2=-beta    # long s1 and short s2
            Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
        elif  -2<z<2:
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])        

    elif position_s1==-1:
        if z<=0.4:
            position_s1=0
            position_s2=0
            Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
        elif 0.4<z:
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])


    elif position_s1==1:
        if z>=-0.4:
            position_s1=0
            position_s2=0
            Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
        elif z<-0.4:
            Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])

Trades=pd.DataFrame(Trades,columns=["Date","Position_s1","Position_s2","Price_s1","Price_s2","Z-score"])
Daily_data=pd.DataFrame(Daily_data,columns=["Date","Position_s1","Position_s2","Price_s1","Price_s2","Z-score"])

print(Trades)
print(Daily_data)

pos_s1=Daily_data["Position_s1"]
pos_s2=Daily_data["Position_s2"]
s1_price=Daily_data["Price_s1"]
s2_price=Daily_data["Price_s2"]

daily_returns=[0]  # first day return will be 0
ret=0
for i in range(1,len(Daily_data["Date"])):
    
    if pos_s1.iloc[i-1]==1 and pos_s1.iloc[i]==1:
        ret= (s1_price.iloc[i]-s1_price.iloc[i-1]) - beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==-1 and pos_s1.iloc[i]==-1:
        ret= -(s1_price.iloc[i]-s1_price.iloc[i-1]) + beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==1 and pos_s1.iloc[i]==0:
        ret= (s1_price.iloc[i]-s1_price.iloc[i-1]) - beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==-1 and pos_s1.iloc[i]==0:
        ret= -(s1_price.iloc[i]-s1_price.iloc[i-1]) + beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==0 :
        daily_returns.append(0)

daily_returns=pd.Series(daily_returns)

Sharpe= (daily_returns.mean())*((252)**0.5)/(daily_returns.std())

print(f"Annualized Sharpe ratio is: {Sharpe}")