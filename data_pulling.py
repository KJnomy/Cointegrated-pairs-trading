import yfinance as yf

tick= input("Enter the ticker symbol: ")
#response= yf.download(tick, period="2y",interval="1d")
response= yf.Ticker(tick)
#response.to_csv(f"{tick}.csv")
print(response.info["sector"])

