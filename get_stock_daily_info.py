import pandas as pd
import requests
import io
import os
import datetime


START_DATE = datetime.date(2023, 11, 1)
#END_DATE = datetime.date(2023, 11, 7)
END_DATE = datetime.date.today()
STOCK_DAILY_INFO_URL = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=[DATE]&type=ALLBUT0999&_=1649743235999'
STOCK_DAILY_INFO_PICKLE = 'stock_daily_info.pkl'


def list_date(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y%m%d'))
        current_date += datetime.timedelta(days=1)
    return date_list

#date_str = '20211203'
#date_object = datetime.strptime(date_str, '%Y%m%d').date()
#print(date_object)


def to_numeric(x):
    for s in ['成交股數', '成交筆數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌價差', '最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量']:
        x[s] = pd.to_numeric(x[s], errors='coerce')
    return x


def get_stock_daily_info(date):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/111.25 (KHTML, like Gecko) Chrome/99.0.2345.81 Safari/123.36'}
    res = requests.get(STOCK_DAILY_INFO_URL.replace('[DATE]', date), headers=headers)
    if len(res.text) == 0:
        return None

    lines = [l for l in res.text.split('\n') if len(l.split(',"'))>=10]
    df = pd.read_csv(io.StringIO(','.join(lines))).iloc[:, :-1]
    df = df.map(lambda s: (str(s).replace('=','').replace(',','').replace('"',''))).iloc[:,:-1]
    df = df.apply(to_numeric, axis=1)
    df['date'] = date
    return df


if __name__ == '__main__':
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('max_colwidth', 400)
    if os.path.isfile(STOCK_DAILY_INFO_PICKLE):
        df_all = pd.read_pickle(STOCK_DAILY_INFO_PICKLE)
    else:
        df_all = None
    

    existed_date_list = df_all['date'].unique()
    for date in list_date(START_DATE, END_DATE):
        if date in existed_date_list:
            continue 
        df = get_stock_daily_info(date)
        if df is None:
            continue

        df_all = pd.concat([df_all, df])
        print(df_all)
    df_all.to_pickle(STOCK_DAILY_INFO_PICKLE)
    #print(df_all)
