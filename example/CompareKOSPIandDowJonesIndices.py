# Comparison of KOSPI and Dow Jones Indices
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# Download the Dow Jones (^DJI) index data from Yahoo Finance after 2000.
dow = pdr.get_data_yahoo('^DJI', '2000-01-04')
# Download the KOSPI (^KS11) index data from Yahoo Finance after 2000.
kospi = pdr.get_data_yahoo('^KS11', '2000-01-04')


import matplotlib.pyplot as plt

plt.figure(figsize=(9, 5))
# Plot the Dow Jones index with a red dashed line.
plt.plot(dow.index, dow.Close, 'r--', label='Dow Jones Industrial')
# Plot the KOSPI index with a blue solid line.
plt.plot(kospi.index, kospi.Close, 'b', label='KOSPI')
plt.grid(True)
plt.legend(loc='best')
plt.show()

# Indexation Comparison
# Divide today's Dow Jones index by the Dow Jones index on January 4, 2000, and multiply by 100.
dow_jones_indices = (dow.Close / dow.Close.loc['2000-01-04']) * 100
# Divide today's KOSPI index by the KOSPI index on January 4, 2000, and multiply by 100.
kospi_index = (kospi.Close / kospi.Close.loc['2000-01-04']) * 100

plt.figure(figsize=(9, 5))
plt.plot(dow_jones_indices.index, dow_jones_indices, 'r--', label='Dow Jones Industrial Average')
plt.plot(kospi_index.index, kospi_index, 'b', label='KOSPI')
plt.grid(True)
plt.legend(loc='best')
plt.show()