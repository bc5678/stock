import datetime
import pandas as pd

# 列出從2010年1月1日以來, 星期六/星期日有交易的日子
df = pd.read_pickle('stock_daily_info.pkl')
date_list = df['日期'].unique()
for date in date_list:
    d = datetime.datetime.strptime(date, '%Y%m%d')
    if (d.weekday() == 5 or d.weekday() == 6):
        print(date, d.weekday())
