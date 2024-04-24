# Comparison of KOSPI and Dow Jones Indices
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# Download the Dow Jones (^DJI) index data from Yahoo Finance after 2000.
dow = pdr.get_data_yahoo('^DJI', '2000-01-04')
# Download the KOSPI (^KS11) index data from Yahoo Finance after 2000.
kospi = pdr.get_data_yahoo('^KS11', '2000-01-04')

# 2024-04-23 download data length
print(len(dow)) # 6113
print(len(kospi)) # 5994

# Create a DataFrame with the closing columns of the Dow Jones and KOSPI indices.
df = pd.DataFrame({'Dow Jones': dow['Close'], 'KOSPI': kospi['Close']})

# Replace NaN data.
# df = df.fillna(method='bfill') # FutureWarning: DataFrame.fillna with 'method' is deprecated and will raise in a future version. Use obj.ffill() or obj.bfill() instead.
df = df.bfill()
# df = df.fillna(method='ffill')
df = df.ffill()

# Plot a scatter plot with the Dow Jones index's closing column as x and the KOSPI index's closing column as y.
import matplotlib.pyplot as plt
plt.figure(figsize=(7, 7))
plt.scatter(df['Dow Jones'], df['KOSPI'], marker='.')
plt.xlabel('Dow Jones Industrial Average')
plt.ylabel('KOSPI')
plt.show()