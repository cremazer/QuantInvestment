import pandas as pd

# Create a data frame from a dictionary
df = pd.DataFrame({'KOSPI': [1915, 1961, 2026, 2467, 2041],
                   'KOSDAQ': [542, 682, 631, 798, 675]},
                  index=[2014, 2015, 2016, 2017, 2018])
print(df)

# Viewing DataFrame data information
print(df.describe())

# Viewing DataFrame structure information
print(df.info())

# Creating a DataFrame Using Series
kospi = pd.Series([1915, 1961, 2026, 2467, 2041], index=[2014, 2015, 2016, 2017, 2018], name='KOSPI')
kosdaq = pd.Series([542, 682, 631, 798, 675], index=[2014, 2015, 2016, 2017, 2018], name='KOSDAQ')
df = pd.DataFrame({kospi.name: kospi, kosdaq.name: kosdaq})
print(df)

# Creating a DataFrame Using a List
columns = ['KOSPI', 'KOSDAQ']
index = [2014, 2015, 2016, 2017, 2018]
rows = []
rows.append([1915, 542])
rows.append([1961, 682])
rows.append([2026, 631])
rows.append([2467, 798])
rows.append([2041, 675])
df = pd.DataFrame(rows, columns=columns, index=index)
print(df)

# Printing DataFrame using indexes
for i in df.index:
    print(i, df['KOSPI'][i], df['KOSDAQ'][i])

# printing data returned as tuples using the itertuples()
for row in df.itertuples():
    print(row[0], row[1], row[2])

# printing data returned as dictionary using the iterrows()
for idx, row in df.iterrows():
    # print(idx, row[0], row[1]) # FutureWarning: Series.__getitem__ treating keys as positions is deprecated. In a future version, integer keys will always be treated as labels (consistent with DataFrame behavior). To access a value by position, use `ser.iloc[pos]`  print(idx, row[0], row[1])
    print(idx, row.iloc[0], row.iloc[1])