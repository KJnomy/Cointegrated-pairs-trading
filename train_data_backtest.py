import yfinance as yf
import pandas as pd
import statsmodels.tsa.stattools as sm
import math
import matplotlib.pyplot as plt
s1=input("Enter stock 1: ")
s2=input("Enter stock 2: ")

df1=yf.download(s1,period="2y",interval="1d")
df2=yf.download(s2,period="2y",interval="1d")

df1.columns=df1.columns.droplevel(1)
df2.columns=df2.columns.droplevel(1)

df1, df2 = df1.align(df2, join="inner")  #this will protect us from data misalignment

y=df1["Close"]
x=df2["Close"]

train_y=y.iloc[0 : math.floor(len(y)*0.65)]  #taking 65 percent of whole data for training
test_y=y.iloc[math.floor(len(y)*0.65) : len(y)] #rest 35 percent for testing

train_x=x.iloc[0 : math.floor(len(x)*0.65)]
test_x=x.iloc[math.floor(len(x)*0.65) : len(x)]

trainx=train_x
train_x=sm.add_constant(train_x)

model=sm.OLS(train_y,train_x)
result=model.fit()

a=result.params.iloc[0]
beta=result.params.iloc[1]

spread=train_y-a-beta*trainx
plt.plot(spread.index,spread)
plt.show()

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
    price_s1=train_y.loc[date]   
    price_s2=trainx.loc[date]

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
ret=0    #initial return is zero
# we defined return for our pairs as ret = ret_num/ret_den, ret_num = current pnl, ret_den= current value of our investment 
for i in range(1,len(Daily_data["Date"])):
    
    if pos_s1.iloc[i-1]==1 and pos_s1.iloc[i]==1:
        ret_num= (s1_price.iloc[i]-s1_price.iloc[i-1]) - beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        ret_den= abs(pos_s1.iloc[i-1])*s1_price.iloc[i-1] + abs(pos_s2.iloc[i-1])*s2_price.iloc[i-1]
        ret=ret_num/ret_den
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==-1 and pos_s1.iloc[i]==-1:
        ret_num= -(s1_price.iloc[i]-s1_price.iloc[i-1]) + beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        ret_den= abs(pos_s1.iloc[i-1])*s1_price.iloc[i-1] + abs(pos_s2.iloc[i-1])*s2_price.iloc[i-1]
        ret=ret_num/ret_den
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==1 and pos_s1.iloc[i]==0:
        ret_num= (s1_price.iloc[i]-s1_price.iloc[i-1]) - beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        ret_den= abs(pos_s1.iloc[i-1])*s1_price.iloc[i-1] + abs(pos_s2.iloc[i-1])*s2_price.iloc[i-1]
        ret=ret_num/ret_den
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==-1 and pos_s1.iloc[i]==0:
        ret_num= -(s1_price.iloc[i]-s1_price.iloc[i-1]) + beta*(s2_price.iloc[i]-s2_price.iloc[i-1])
        ret_den= abs(pos_s1.iloc[i-1])*s1_price.iloc[i-1] + abs(pos_s2.iloc[i-1])*s2_price.iloc[i-1]
        ret=ret_num/ret_den
        daily_returns.append(ret)
    elif pos_s1.iloc[i-1]==0 :
        daily_returns.append(0)

daily_returns=pd.Series(daily_returns)

Sharpe= (daily_returns.mean())*((252)**0.5)/(daily_returns.std())

print(f"Annualized Sharpe ratio is: {Sharpe}")

print(len(Trades))