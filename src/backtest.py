import pandas as pd
from ols import fit_hedge_ratio
from trading_signals import generate_positions


def compute_daily_returns(Daily_data, beta):
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

    return pd.Series(daily_returns)


def compute_sharpe(daily_returns):
    return (daily_returns.mean())*((252)**0.5)/(daily_returns.std())


def compute_max_drawdown(daily_returns):
    equity_curve = (1 + daily_returns).cumprod()
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    max_drawdown = drawdown.min()
    return max_drawdown


def run_backtest(y, x, a, beta, label):
    spread = y - a - beta*x
    Daily_data, Trades = generate_positions(spread, y, x, beta)
    daily_returns = compute_daily_returns(Daily_data, beta)

    print(f"Trades ({label})")
    print(Trades)
    print(f"Daily_data ({label})")
    print(Daily_data)

    Sharpe = compute_sharpe(daily_returns)
    max_drawdown = compute_max_drawdown(daily_returns)

    print(f"{label} Annualized Sharpe ratio is: {Sharpe}")
    print(f"{label} No. of trades: {len(Trades)}")
    print(f"{label} Max Drawdown: {max_drawdown:.2%}")

    return Sharpe, max_drawdown, Trades, daily_returns


if __name__ == "__main__":
    train_y = pd.read_csv("data/train_y.csv", index_col=0, parse_dates=True).squeeze()
    train_x = pd.read_csv("data/train_x.csv", index_col=0, parse_dates=True).squeeze()
    test_y = pd.read_csv("data/test_y.csv", index_col=0, parse_dates=True).squeeze()
    test_x = pd.read_csv("data/test_x.csv", index_col=0, parse_dates=True).squeeze()

    a, beta = fit_hedge_ratio(train_y, train_x)

    run_backtest(train_y, train_x, a, beta, label="In-sample (train)")
    run_backtest(test_y, test_x, a, beta, label="Out-of-sample (test)")
