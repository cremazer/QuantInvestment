import pandas as pd

xlsx_file_path = '/Users/lucky/Documents/quant/상장법인목록.xlsx'

krx_list = pd.read_excel(xlsx_file_path)

print(krx_list)