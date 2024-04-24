# Compare stock returns
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# Get Samsung Electronics and Microsoft data
# The start date of the query is set to May 4, 2018, following Samsung Electronics' stock split. The end date is omitted, so it defaults to today's date.
sec = pdr.get_data_yahoo('005930.KS', start='2018-05-04')
msft = pdr.get_data_yahoo('MSFT', start='2018-05-04')

# Check Samsung Electronics downloaded data
print(sec.head(10))

# Check Microsoft downloaded data
print(msft.head(10))

# Check DataFrame configuration
print(sec.index)

# Check DataFrame columns
print(sec.columns)

# Let's plot a graph using the closing price data of Samsung Electronics and Microsoft.
import matplotlib.pyplot as plt
plt.plot(sec.index, sec.Close, 'b', label='Samsung Electronics')
plt.plot(msft.index, msft.Close, 'r--', label='Microsoft')
plt.legend(loc='best')
plt.show()

# Check the closing price of Samsung Electronics and Microsoft on the last day of the data.
print(sec['Close'])

# Calculate the daily percent change of return for Samsung Electronics.
sec_dpc = (sec['Close'] - sec['Close'].shift(1)) / sec['Close'].shift(1) * 100
sec_dpc.iloc[0] = 0
plt.hist(sec_dpc, bins=18)
plt.grid(True)
plt.show()

# Calculating Cumulative Product of Daily Percent Changes.
sec_dpc_cp = ((100 + sec_dpc) / 100).cumprod() * 100 - 100
print(sec_dpc_cp)

# Calculate the daily percent change of return for Microsoft.
msft_dpc = (msft['Close'] - msft['Close'].shift(1)) / msft['Close'].shift(1) * 100
msft_dpc.iloc[0] = 0
plt.hist(msft_dpc, bins=18)
plt.grid(True)
plt.show()

# Calculating Cumulative Product of Daily Percent Changes.
msft_dpc_cp = ((100 + msft_dpc) / 100).cumprod() * 100 - 100
print(msft_dpc_cp)
