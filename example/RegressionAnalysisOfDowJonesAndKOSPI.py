# Comparison of KOSPI and Dow Jones Indices
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()
from scipy import stats
import matplotlib.pyplot as plt

# Download the Dow Jones (^DJI) index data from Yahoo Finance after 2000.
dow = pdr.get_data_yahoo('^DJI', '2000-01-04')
# Download the KOSPI (^KS11) index data from Yahoo Finance after 2000.
kospi = pdr.get_data_yahoo('^KS11', '2000-01-04')

# Create a DataFrame with the closing columns of the Dow Jones and KOSPI indices.
df = pd.DataFrame({'X': dow['Close'], 'Y': kospi['Close']})

# Replace NaN data.
df = df.bfill()
df = df.ffill()

# Create a linear regression model object regr with the Dow Jones index X and KOSPI index Y.
regr = stats.linregress(df.X, df.Y)
# Display the regression equation as a label in the legend.
regr_line = f'Y = {regr.slope:.2f} * X + {regr.intercept:.2f}'

plt.figure(figsize=(7, 7))
# Represent the scatter plot with small circles.
plt.plot(df.X, df.Y, '.')
# Plot the regression line in red.
plt.plot(df.X, regr.slope * df.X + regr.intercept, 'r')
plt.legend(['DOW Jones x KOSPI', regr_line])
plt.title(f'Dow Jones x KOSPI (R = {regr.rvalue:.2f})')
plt.xlabel('Dow Jones Industrial Average')
plt.ylabel('KOSPI')
plt.show()