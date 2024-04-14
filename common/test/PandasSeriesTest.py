import pandas as pd

# Create a series from a list
s = pd.Series([0.0, 3.6, 2.0, 5.8, 4.2, 8.0])
print(s)

# Change index of series
s.index = pd.Index([0.0, 1.2, 1.8, 3.0, 3.6, 4.8])
s.index.name = 'MY_INDEX'
s.name = 'MY_SERIES'
print(s)

# Adding data to a Series
s[5.9] = 5.5
print(s)

s2 = pd.Series([6.7, 4.2], index=[6.8, 8.0])
#s = s.append(s2) # AttributeError: 'Series' object has no attribute 'append'. Did you mean: '_append'?
s = s._append(s2)
print(s)

# Indexing Series Data
print(s.index[-1])  # 8.0
print(s.values[-1])  # 4.2
print(s.loc[8.0])  # 4.2
print(s.iloc[-1])  # 4.2
print(s.values[:]) # return array
print(s.iloc[:]) # return Series

# Deleting Series Data
print(s.drop(8.0))  # drop by index

# Viewing Series Information
print(s.describe())

# Visualizing a Series
import matplotlib.pyplot as plt
plt.title("ELLIOTT_WAVE")
plt.plot(s, 'bs--')
plt.xticks(s.index)
plt.yticks(s.values)
plt.grid(True)
plt.show()