import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.tsa.stattools as sm
import statsmodels.api as sma


data=pd.read_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/constituents.csv")

tickers=data["Symbol"].tolist()  

tickers=[ticker.replace(".","-") for ticker in tickers] # replacing . to - for yfinance api readability

prices=yf.download(tickers,period="2y",interval="1d",auto_adjust=True)["Close"] # downloading all the stock data at once
                                                                                # to avoid multiple api calls

prices=prices.dropna(axis=1,thresh=len(prices)*0.9) # keeping data whose na values not more than 10 precent 

train_data=prices.iloc[0:int(len(prices)*0.65)]      
test_data=prices.iloc[int(len(prices)*0.65):len(prices)]                                              

returns=train_data.pct_change()  # calculating the returns of each day w.r.t prev day

corr_matrix= returns.corr()


pairs=[]
for i in range(len(corr_matrix.columns)):
    for j in range(i+1,len(corr_matrix.columns)):
        if corr_matrix.iloc[i,j]>=0.7: #SELECTING THOSE PAIRS WHOSE CORR GRETAER THAN 0.7
            pairs.append([corr_matrix.columns[i],corr_matrix.columns[j],corr_matrix.iloc[i,j]])

pairs=pd.DataFrame(pairs,columns=("Pair1","Pair2","Correlation"))

print(pairs)

pair1=pairs["Pair1"].tolist() # list of tickers in pair1
pair2=pairs["Pair2"].tolist() # list of tickers in pair2

coint_pairs=[]

for i in range(len(pair1)):
    s1=train_data[pair1[i]]  # closing price of pair1
    s2=train_data[pair2[i]]  #closing price of pair2
    s1, s2= s1.align(s2,join="inner")  #aligning them so that no mismatch of dates happen
    test=sm.coint(s1,s2) # Engle Granger test for cointegration
    if test[1]<=0.05:    # p-value less than 0.05 to reject null hypothesis
        coint_pairs.append([pair1[i],pair2[i],test[1]])

coint_pairs=pd.DataFrame(coint_pairs,columns=("Pair1","Pair2","P-value")) # dataframe of cointegrated pairs


coint_pair1=coint_pairs["Pair1"].tolist()
coint_pair2=coint_pairs["Pair2"].tolist()

hedge_ratio=[]
adf_passed_pairs=[]

for i in range(len(coint_pair1)):
    y=train_data[coint_pair1[i]]
    x=train_data[coint_pair2[i]]
    x, y= x.align(y,join="inner")
    z=sma.add_constant(x)
    model=sm.OLS(y,z)
    result=model.fit()
    alpha=result.params.iloc[0]
    beta=result.params.iloc[1]
    hedge_ratio.append(beta)
    # now performing adf test 
    spread= y - alpha- beta*x # before i was using prices[coint_pair1[i]] that will be misaliged so i used x and y which are aligned
    adf_test=sm.adfuller(spread)
    if adf_test[1] <= 0.05:
        adf_passed_pairs.append([coint_pair1[i],coint_pair2[i],adf_test[1],alpha,beta])

coint_pairs["Hedge_ratio"]=hedge_ratio

adf_passed_pairs=pd.DataFrame(adf_passed_pairs,columns=("Pair1","Pair2","P-value(adf)","Alpha","Hedge_ratio"))

print(f"Cointegrated pairs after Engle Granger test: \n{coint_pairs}")
print(f"Pairs after adfuller test: \n{adf_passed_pairs}")


'''  Trading Strategy  '''

trade_results=[]

capital= 1000000  # we are taking capital of 1 million dollars to trade 
                  # and each trade has an investment of 1 million only

for i in range(len(adf_passed_pairs)):
    s1=adf_passed_pairs["Pair1"].iloc[i]
    s2=adf_passed_pairs["Pair2"].iloc[i]
    test_y=test_data[s1]
    test_x=test_data[s2]
    test_y, test_x= test_y.align(test_x,join="inner")
   
    a=adf_passed_pairs["Alpha"].iloc[i]
    beta=adf_passed_pairs["Hedge_ratio"].iloc[i]

    spread=test_y-a-beta*test_x

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
        price_s1=test_y.loc[date]   
        price_s2=test_x.loc[date]

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
    active = daily_returns[daily_returns != 0] # active days in which we are in position
    Sharpe = active.mean() * (252**0.5) / active.std() # calcutaed sharpe on active days only
    
    equity_curve = (1 + daily_returns).cumprod()
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    max_drawdown = drawdown.min()

    pnl=[]
    for i in range(len(Trades)-1):
        if Trades["Position_s1"].iloc[i]==-1:
            s1_pnl= Trades["Price_s1"].iloc[i] - Trades["Price_s1"].iloc[i+1]
            s2_pnl=beta*(Trades["Price_s2"].iloc[i+1] - Trades["Price_s2"].iloc[i])
            pnl.append((s1_pnl+s2_pnl)*(capital/(Trades["Price_s1"].iloc[i]+beta*Trades["Price_s2"].iloc[i])))  # here we are calculating for total capital investment
        elif Trades["Position_s1"].iloc[i]==1:
            s1_pnl= Trades["Price_s1"].iloc[i+1] - Trades["Price_s1"].iloc[i]
            s2_pnl=beta*(Trades["Price_s2"].iloc[i] - Trades["Price_s2"].iloc[i+1])
            pnl.append((s1_pnl+s2_pnl)*(capital/(Trades["Price_s1"].iloc[i]+beta*Trades["Price_s2"].iloc[i])))
            
    Total_returns=(sum(pnl)/capital)*100 # total pnl generated from capital
    
    trade_results.append([s1,s2,len(Trades),Sharpe,max_drawdown,Total_returns])

   
trade_results=pd.DataFrame(trade_results,columns=("Stock1","Stock2","No. of trades","Sharpe ratio","Max drawdown","Returns_in_percent"))

print(trade_results)

