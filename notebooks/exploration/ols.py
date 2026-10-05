import statsmodels.tsa.stattools as sm
import statsmodels.api as sma


def fit_hedge_ratio(train_y, train_x):
    train_x = sma.add_constant(train_x)

    model = sm.OLS(train_y, train_x)
    result = model.fit()

    a = result.params.iloc[0]
    beta = result.params.iloc[1]

    return a, beta
