# Comparison of KOSPI and Dow Jones Indices
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()
from scipy import stats
import matplotlib.pyplot as plt

# Download the U.S. Treasury Bond (TLT) index data from Yahoo Finance.
tlt = pdr.get_data_yahoo('TLT', '2002-07-30')
# Download the KOSPI (^KS11) index data from Yahoo Finance.
kospi = pdr.get_data_yahoo('^KS11', '2002-07-30')

# Create a DataFrame with the closing columns of the U.S. Treasury Bond and KOSPI indices.
df = pd.DataFrame({'X': tlt['Close'], 'Y': kospi['Close']})

# Replace NaN data.
df = df.bfill()
df = df.ffill()

# Create a linear regression model object regr with the U.S. Treasury Bond index X and KOSPI index Y.
regr = stats.linregress(df.X, df.Y)
# Display the regression equation as a label in the legend.
regr_line = f'Y = {regr.slope:.2f} * X + {regr.intercept:.2f}'

plt.figure(figsize=(7, 7))
# Represent the scatter plot with small x green marks.
plt.plot(df.X, df.Y, 'xg')
# Plot the regression line in red.
plt.plot(df.X, regr.slope * df.X + regr.intercept, 'r')
plt.legend(['U.S. Treasury Bond x KOSPI', regr_line])
plt.title(f'U.S. Treasury Bond x KOSPI (R = {regr.rvalue:.2f})')
plt.xlabel('U.S. Treasury Bond')
plt.ylabel('KOSPI')
plt.show()