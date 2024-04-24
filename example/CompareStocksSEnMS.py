# Comparing the Returns of Samsung Electronics and Microsoft Stocks
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# Get Samsung Electronics and Microsoft data
# The start date of the query is set to May 4, 2018, following Samsung Electronics' stock split. The end date is omitted, so it defaults to today's date.
sec = pdr.get_data_yahoo('005930.KS', start='2018-05-04')
sec_dpc = (sec['Close'] - sec['Close'].shift(1)) / sec['Close'].shift(1) * 100
sec_dpc.iloc[0] = 0
sec_dpc_cp = ((100 + sec_dpc) / 100).cumprod() * 100 - 100

msft = pdr.get_data_yahoo('MSFT', start='2018-05-04')
msft_dpc = (msft['Close'] - msft['Close'].shift(1)) / msft['Close'].shift(1) * 100
msft_dpc.iloc[0] = 0
msft_dpc_cp = ((100 + msft_dpc) / 100).cumprod() * 100 - 100

# Let's plot a graph using the closing price data of Samsung Electronics and Microsoft.
import matplotlib.pyplot as plt
plt.plot(sec.index, sec_dpc_cp, 'b', label='Samsung Electronics')
plt.plot(msft.index, msft_dpc_cp, 'r--', label='Microsoft')
plt.ylabel('Change %')
plt.grid(True)
plt.legend(loc='best')
plt.show()