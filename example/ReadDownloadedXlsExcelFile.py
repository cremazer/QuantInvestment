import pandas as pd

# Set the downloaded file path
xls_file_path = '/Users/lucky/Documents/quant/상장법인목록.xls'

# Read xls Excel File
krx_list = pd.read_html(xls_file_path)

# Print the first element of the list
print(krx_list[0])