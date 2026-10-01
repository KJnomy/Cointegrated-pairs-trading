import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.tsa.stattools as sma
import statsmodels.stats.multitest as ssm
import matplotlib.pyplot as plt


data=pd.read_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/constituents.csv")

tickers=data["Symbol"].tolist()  

tickers=[ticker.replace(".","-") for ticker in tickers] # replacing . to - for yfinance api readability

prices=yf.download(tickers,start="2022-09-17", end="2026-09-17",interval="1d",auto_adjust=True)["Close"] # downloading all the stock data at once
                                                                                # to avoid multiple api calls

prices.to_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/prices4y.csv")

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

EG_pairs=[]

for i in range(len(pair1)):
    s1=train_data[pair1[i]]  # closing price of pair1
    s2=train_data[pair2[i]]  #closing price of pair2
    s1, s2= s1.align(s2,join="inner")  #aligning them so that no mismatch of dates happen
    test=sma.coint(s1,s2) # Engle Granger test for cointegration
    EG_pairs.append([pair1[i],pair2[i],test[1]])

EG_pairs=pd.DataFrame(EG_pairs,columns=("Pair1","Pair2","P-value")) # dataframe of Egle Granger pairs

reject, bh_pvalues, _, _ = ssm.multipletests(
    EG_pairs["P-value"],
    alpha=0.05,
    method="fdr_bh"
)

EG_pairs["BH_pvalue"] = bh_pvalues
EG_pairs["BH_significant"] = reject

BH_pairs = EG_pairs[
    EG_pairs["BH_significant"]
].copy()

coint_pair1=BH_pairs["Pair1"].tolist()
coint_pair2=BH_pairs["Pair2"].tolist()

hedge_ratio=[]
a=[]

for i in range(len(coint_pair1)):
    y=train_data[coint_pair1[i]]
    x=train_data[coint_pair2[i]]
    x, y= x.align(y,join="inner")
    z=sm.add_constant(x)
    model=sm.OLS(y,z)
    result=model.fit()
    alpha=result.params.iloc[0]
    beta=result.params.iloc[1]
    hedge_ratio.append(beta)
    a.append(alpha)

BH_pairs["Hedge_ratio"]=hedge_ratio
BH_pairs["Alpha"]= a
print(BH_pairs)

BH_pairs=BH_pairs.reset_index(drop=True)


'''  Trading Strategy  '''

trade_results=[]

capital= 1000000  # we are taking capital of 1 million dollars to trade 
                  # and each trade has an investment of 1 million only
Transaction_cost_percent= 0.1   # fixed transaction cost for each trade
equity_curves={}
for i in range(len(BH_pairs)):
    s1=BH_pairs["Pair1"].iloc[i]
    s2=BH_pairs["Pair2"].iloc[i]
    test_y=test_data[s1]
    test_x=test_data[s2]
    test_y, test_x= test_y.align(test_x,join="inner")
   
    a=BH_pairs["Alpha"].iloc[i]
    beta=BH_pairs["Hedge_ratio"].iloc[i]

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
            if z>=2: # enter position when z greater than equal to 2
                position_s1= -1   
                position_s2= beta        # short s1 and long s2
                Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
                Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
            elif z<=-2: # enter position when z less than equal to -2
                position_s1= 1
                position_s2=-beta    # long s1 and short s2
                Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
                Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
            elif  -2<z<2:
                Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])        

        elif position_s1==-1:
            if z >= 3.5:   #exit if spread goes beyond 3.5 then our position got stuck and will generate huge loss 
                position_s1 = 0
                position_s2 = 0
                Trades.append([date, position_s1, position_s2, price_s1, price_s2, z])
                Daily_data.append([date, position_s1, position_s2, price_s1, price_s2, z])
            
            elif z<=0.4:  # exit position if z comes below 0.4
                position_s1=0
                position_s2=0
                Trades.append([date,position_s1,position_s2,price_s1,price_s2,z])
                Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])
            elif 0.4<z: # keep in position if z doesn't hit 0.4
                Daily_data.append([date,position_s1,position_s2,price_s1,price_s2,z])           

        elif position_s1==1:
            if z <= -3.5:   # exit if spread goes beyond -3.5 then our position got stuck and will generate huge loss
                position_s1 = 0
                position_s2 = 0
                Trades.append([date, position_s1, position_s2, price_s1, price_s2, z])
                Daily_data.append([date, position_s1, position_s2, price_s1, price_s2, z])
            elif z>=-0.4:
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

    daily_returns=pd.Series(daily_returns,index=Daily_data["Date"])
    for i in Trades["Date"]:
        if i in daily_returns.index:
            daily_returns[i] -= Transaction_cost_percent/100    # we have to subtract the transaction cost as soon we enter the trade

    Sharpe = daily_returns.mean() * (((252)**(0.5)) / daily_returns.std()) # calculated sharpe ratio
    
    equity_curve = (1 + daily_returns).cumprod()
    equity_curves[(s1,s2)]= equity_curve
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
            
    Total_returns=((sum(pnl)-len(Trades)*(Transaction_cost_percent/100)*capital)/capital)*100 # total returns generated from capital after removing transaction charges
    Win_rate=(sum(i>0 for i in pnl)/len(pnl))*100
    trade_results.append([s1,s2,len(Trades),Sharpe,max_drawdown,Total_returns,Win_rate])

   
trade_results=pd.DataFrame(trade_results,columns=("Stock1","Stock2","No. of trades","Sharpe ratio","Max drawdown","Returns_in_percent","Win_rate"))

adf_pval=BH_pairs["P-value"].to_list()
adf_alpha=BH_pairs["Alpha"].to_list()
adf_beta=BH_pairs["Hedge_ratio"].to_list()
trade_results["P-value"]=adf_pval
trade_results["Alpha"]=adf_alpha
trade_results["Hedge_ratio"]=adf_beta

print(trade_results)

#Industry map for our adf passed pairs needs to be changed if hardcoded time frame changes

def Stock_info(ticker):
    try:
        info=yf.Ticker(ticker).info
        return {"Sector":info.get("sector"),
                "Industry": info.get("industry")
                }
    except Exception:
        return {"Sector": ("none"),
                "Industry": ("none")}


adf_tickers = set(trade_results["Stock1"]) | set(trade_results["Stock2"])

stock_info = {
    ticker: Stock_info(ticker)
    for ticker in adf_tickers
}

industry_classification = []

for s1, s2 in zip(trade_results["Stock1"],trade_results["Stock2"]):
    industry1 = stock_info[s1]["Industry"]
    industry2 = stock_info[s2]["Industry"]
    if industry1 is None or industry2 is None:
        classification = "Unknown"

    elif industry1 == industry2:
        classification = "Same"

    else:
        classification = "Cross"

    industry_classification.append(classification)


trade_results["Industry_type"] = industry_classification
print(trade_results)

from scipy.stats import ttest_ind 

same = trade_results[trade_results["Industry_type"]=="Same"]["Sharpe ratio"]
cross = trade_results[trade_results["Industry_type"]=="Cross"]["Sharpe ratio"]
stat, pval = ttest_ind(same, cross, equal_var=False)
print(f"Same-Industry — mean Sharpe: {same.mean():.2f}, n={len(same)}")
print(f"Cross-Industry — mean Sharpe: {cross.mean():.2f}, n={len(cross)}")
print(f"Welch t-stat: {stat:.2f}, p-value: {pval:.4f}")


strong = trade_results[trade_results["P-value"] < 0.01]
weak = trade_results[(trade_results["P-value"] >= 0.01) & (trade_results["P-value"] <= 0.05)]
print(f"Strong coint (p<0.01) — % positive Sharpe: {(strong['Sharpe ratio']>0).mean()*100:.0f}%")
print(f"Weak coint (p<0.05) — % positive Sharpe: {(weak['Sharpe ratio']>0).mean()*100:.0f}%")

trade_results.to_csv("results_BH/trade_results.csv", index=False)
BH_pairs.to_csv("results_BH/BH_pairs.csv", index=False)
test_data.to_csv("data/test_data_BH_test.csv")
train_data.to_csv("data/train_data_BH_test.csv")

best_pairs=[]

for i in range(len(trade_results)):
    if (trade_results["Sharpe ratio"].iloc[i]>1 and trade_results["P-value"].iloc[i]<0.01 
        and trade_results["Win_rate"].iloc[i]>75 and trade_results["Max drawdown"].iloc[i]>-0.05): # changed max drawdown from 5 to 0.05 as it is percentage
        best_pairs.append([trade_results["Stock1"].iloc[i],trade_results["Stock2"].iloc[i]])

best_pairs=pd.DataFrame(best_pairs,columns=("Stock1","Stock2"))
best_pairs.to_csv("results_BH/Best_pairs.csv")

print(best_pairs)

plt.figure(figsize=(14, 7))

for _, row in best_pairs.iterrows():

    s1 = row["Stock1"]
    s2 = row["Stock2"]

    equity_curve = equity_curves[(s1, s2)]

    plt.plot(
        equity_curve.index,
        equity_curve.values,
        linewidth=1.8,
        label=f"{s1} - {s2}"
    )

plt.title("Equity Curves of Best Pairs")
plt.xlabel("Date")
plt.ylabel("Portfolio Value (Normalized)")
plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "results_BH/Top_pairs_equity_curves.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()