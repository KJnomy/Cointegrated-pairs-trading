import pandas as pd
import numpy as np
import plotly.graph_objects as go

adf_passed_pairs = pd.read_csv("4_results/final_pairs.csv")
test_data        = pd.read_csv("4_results/prices_test.csv", index_col="Date", parse_dates=True)

top_pairs = [("PSX","VLO"), ("COF","WFC"), ("CMS","EXC"), ("BAC","PH"), ("ALL","TRV"), ("IQV","MTD")]
colors    = ["#1baf7a","#378ADD","#c9982a","#9b59b6","#e34948","#17a589"]

fig = go.Figure()

for (p1, p2), color in zip(top_pairs, colors):
    row = adf_passed_pairs[(adf_passed_pairs["Pair1"]==p1) & (adf_passed_pairs["Pair2"]==p2)]
    if len(row) == 0:
        continue

    a    = row["Alpha"].iloc[0]
    beta = row["Hedge_ratio"].iloc[0]
    y    = test_data[p1].dropna()
    x    = test_data[p2].dropna()
    x, y = x.align(y, join="inner")

    spread    = y - a - beta * x
    roll_mean = spread.rolling(30).mean()
    roll_std  = spread.rolling(30).std()
    zscore    = ((spread - roll_mean) / roll_std).dropna()

    # replay signal — same logic as main backtest
    signal = pd.Series(0.0, index=zscore.index)
    pos = 0
    for dt in zscore.index:
        z = zscore.loc[dt]
        if pos == 0:
            if   z >=  2.0: pos = -1
            elif z <= -2.0: pos =  1
        elif pos == -1:
            if z <= 0.4 or z >= 3.5: pos = 0
        elif pos == 1:
            if z >= -0.4 or z <= -3.5: pos = 0
        signal.loc[dt] = pos

    y_ret   = y.pct_change()
    x_ret   = x.pct_change()
    pnl_ret = signal.shift(1) * (y_ret - beta * x_ret)
    eq      = (1 + pnl_ret.fillna(0)).cumprod()

    final_ret = (eq.iloc[-1] - 1) * 100
    fig.add_trace(go.Scatter(
        x=eq.index, y=eq.values,
        name=f"{p1}/{p2}  ({final_ret:+.1f}%)",
        mode="lines", line=dict(color=color, width=1.8)
    ))

fig.add_hline(y=1.0, line_dash="dash", line_color="gray", line_width=1)
fig.update_layout(
    title=dict(text="Out-of-Sample Equity Curves — Top 6 Pairs", font_size=16),
    xaxis_title="Date",
    yaxis_title="Portfolio Value (normalized to 1.0)",
    template="plotly_white",
    height=440,
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)")
)

fig.write_image("4_results/equity_curves.png", width=900, height=440)
fig.show()
print("Equity curve saved → 4_results/equity_curves.png")