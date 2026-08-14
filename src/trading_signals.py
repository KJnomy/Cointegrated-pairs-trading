import pandas as pd


def generate_positions(spread, y, x, beta):
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
        price_s1=y.loc[date]
        price_s2=x.loc[date]

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

    return Daily_data, Trades
