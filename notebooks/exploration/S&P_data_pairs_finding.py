import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.tsa.stattools as sm


data=pd.read_csv("C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data/constituents.csv")

tickers=data["Symbol"].tolist()  

tickers=[ticker.replace(".","-") for ticker in tickers] # replacing . to - for yfinance api readability

prices=yf.download(tickers,period="2y",interval="1d",auto_adjust=True)["Close"] # downloading all the stock data at once
                                                                                # to avoid multiple api calls

prices=prices.dropna(axis=1,thresh=len(prices)*0.4) # we are removing those stocks whose data has more than 
                                                    # 60 percent na values

returns=prices.pct_change()  # calculating the returns of each day w.r.t prev day

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
    s1=prices[pair1[i]]  # closing price of pair1
    s2=prices[pair2[i]]  #closing price of pair2
    s1, s2= s1.align(s2,join="inner")  #aligning them so that no mismatch of dates happen
    test=sm.coint(s1,s2) # Engle Granger test for cointegration
    if test[1]<=0.05:    # p-value less than 0.05 to reject null hypothesis
        coint_pairs.append([pair1[i],pair2[i],test[1]])

coint_pairs=pd.DataFrame(coint_pairs,columns=("Pair1","Pair2","P-value")) # dataframe of cointegrated pairs

print(coint_pairs)
#%%
coint_pair1=coint_pairs["Pair1"].tolist()
coint_pair2=coint_pairs["Pair2"].tolist()

hedge_ratio=[]
adf_passed_pairs=[]

for i in range(len(coint_pair1)):
    x=prices[coint_pair1[i]]
    y=prices[coint_pair2[i]]
    x, y= x.align(y,join="inner")
    x=sm.add_constant(x)
    model=sm.OLS(y,x)
    result=model.fit()
    alpha=result.params.iloc[0]
    beta=result.params.iloc[1]
    hedge_ratio.append(beta)
    # now performing adf test 
    spread= prices[coint_pair2[i]] - alpha- beta*prices[coint_pair1[i]]
    adf_test=sm.adfuller(spread)
    if adf_test[1] <= 0.05:
        adf_passed_pairs.append([coint_pair1[i],coint_pair2[i],adf_test[1]])

coint_pairs["Hedge_ratio"]=hedge_ratio

adf_passed_pairs=pd.DataFrame(adf_passed_pairs,columns=("Pair1","Pair2","P-value(adf)"))

print(f"Cointegrated pairs after Engle Granger test: \n{coint_pairs}")
print(f"Pairs after adfuller test: \n{adf_passed_pairs}")

