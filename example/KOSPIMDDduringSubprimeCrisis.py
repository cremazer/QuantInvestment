# KOSPI MDD during the Subprime Crisis
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# Download the KOSPI index data. The symbol for the KOSPI index is ^KS11.
kospi = pdr.get_data_yahoo('^KS11', '2004-01-04')

# For the calculation period, the corresponding window value is set approximately to 252 trading days, which is one year.
window = 252

# Calculate the peak in the KOSPI closing price column over a period of one year based on trading days.
peak = kospi['Adj Close'].rolling(window, min_periods=1).max()

# Drawdown calculates how much the current KOSPI closing price has fallen compared to the peak.
drawdown = kospi['Adj Close']/peak - 1.0

# For the drawdown, calculate the trough (mac_dd) over a period of one year.
# Since it is a negative value, the trough immediately becomes the Maximum Drawdown (MDD).
max_dd = drawdown.rolling(window, min_periods=1).min()

import matplotlib.pyplot as plt

plt.figure(figsize=(9, 7))
plt.subplot(211) # Draw in the first row of a 2x1 grid.
kospi['Close'].plot(label='KOSPI', title='KOSPI MDD', grid=True, legend=True)
plt.subplot(212) # Draw in the second row of a 2x1 grid.
drawdown.plot(c='blue', label='KOSPI DD', grid=True, legend=True)
max_dd.plot(c='red', label='KOSPI MDD', grid=True, legend=True)
plt.show()
