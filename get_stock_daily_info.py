import pandas as pd
import numpy as np
import requests
import io
import os
import datetime


START_DATE = datetime.date(2023, 12, 5)
END_DATE = datetime.date.today()
STOCK_URL = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=[DATE]&type=ALLBUT0999&_=1649743235999'
OTC_URL = 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=csv&d=[DATE]&se=EW&s=0,asc,0'
STOCK_PICKLE = 'stock_daily_info.pkl'


def list_date(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y%m%d'))
        current_date += datetime.timedelta(days=1)
    return date_list


def str_to_numeric(x):
    # 價位相關的欄位, 全部*100 後當成int存儲, 用來避免浮點數運算偏移
    # 若原本為NaN, 則改成0 (因為價位不可能為0, 所以可和正常值區分開來)
    for s in ['開盤價', '最高價', '最低價', '收盤價', '最後揭示買價', '最後揭示賣價']:
        x[s] = pd.to_numeric(x[s], errors='coerce', downcast="float")
        x[s] = (x[s]*100)

    for s in ['成交股數', '成交筆數', '成交金額', '最後揭示買量', '最後揭示賣量']:
        x[s] = pd.to_numeric(x[s], errors='coerce', downcast="unsigned")

    x.fillna(value=0, inplace=True)

    for s in ['開盤價', '最高價', '最低價', '收盤價', '最後揭示買價', '最後揭示賣價']:
        x[s] = np.rint(x[s]).astype(np.uint32)
    
    for s in ['成交股數', '成交筆數', '最後揭示買量', '最後揭示賣量']:
        # 過去的上櫃資料沒有最後揭示買量, 和最後揭示賣量2個欄位
        # 因此一開始轉成DataFrame時會變成NaN, 經過to_numeric成unsigned後會變成int (值為0), 並非numpy.intXX, 無法call astype()
        # 後續也要注意, 如果是有最後買價, 但最後買量為0, 就是這種狀況
        if type(x[s]) == int:
            x[s] = np.uint32(0)
        else:
            x[s] = x[s].astype(np.uint32)

    return x


def get_stock_by_date(date):
    # Format: 西元年月日
    res = requests.get(STOCK_URL.replace('[DATE]', date))

    # 沒交易的日期資料為空
    if len(res.text) == 0:
        return None

    lines = [l for l in res.text.split('\n') if len(l.split(',"'))>=10]
    df = pd.read_csv(io.StringIO(''.join(lines)))
    df = df.iloc[:,:-2]
    df = df.drop(columns=['證券名稱', '漲跌(+/-)', '漲跌價差'])
    df = df.map(lambda s: (str(s).replace('=', '').replace(',', '').replace('"', '').replace(' ', '')))
    df = df.apply(str_to_numeric, axis=1)
    df['日期'] = date
    return df


def get_otc_by_date(date):
    # Format: 民國年/月/日
    date = str(int(date)-19110000)
    if len(date) == 6:
        date = '0' + date
    res = requests.get(OTC_URL.replace('[DATE]', f'{date[0:3]}/{date[3:5]}/{date[5:7]}'))

    lines = [l for l in res.text.split('\n') if len(l.split(','))>=10]

    # 沒交易的日期仍會有內容, 所以改為確認parse完後沒data
    if len(lines) == 0:
        return None

    df = pd.read_csv(io.StringIO(''.join(lines)))
    df = df.iloc[:,:-3]
    df = df.drop(columns=['名稱', '漲跌'])
    df = df.map(lambda s: (str(s).replace(',', '').replace(' ', '')))

    # 上櫃資料的column有些包含空白, 先將其處理掉
    replace_map = {}
    otc_to_stock_mapping = [
        ('代號', '證券代號'), 
        ('成交股數', '成交股數'),
        ('成交筆數', '成交筆數'),
        ('成交金額(元)', '成交金額'),
        ('開盤', '開盤價'),
        ('最高', '最高價'),
        ('最低', '最低價'),
        ('收盤', '收盤價'),
        ('最後買價', '最後揭示買價'),
        ('最後買量(千股)', '最後揭示買量'),
        ('最後賣價', '最後揭示賣價'),
        ('最後賣量(千股)', '最後揭示賣量'),
    ]
    for column in df.columns:
        for otc_column, stock_column in otc_to_stock_mapping:
            if otc_column in column:
                replace_map[column] = stock_column
    if replace_map:
        df.rename(columns=replace_map, inplace=True)
    
    df = df.reindex(columns=[x[1] for x in otc_to_stock_mapping])
    df = df.apply(str_to_numeric, axis=1)
    df['日期'] = str(int(date)+19110000)
    return df


def get_stock_otc_daily_info():
    print("===== 開始抓取歷年上市上櫃股票每日交易資訊 =====")
    if os.path.isfile(STOCK_PICKLE):
        df_stock = pd.read_pickle(STOCK_PICKLE)
        existed_date_list = df_stock['日期'].unique()
    else:
        df_stock = None
        existed_date_list = []
    
    count = 0
    for date in list_date(START_DATE, END_DATE):
        if date in existed_date_list:
            print(f'{date} exist')
            continue 

        df_stock_one_day = get_stock_by_date(date)
        df_otc_one_day = get_otc_by_date(date)
        if df_stock_one_day is None or df_otc_one_day is None:
            print(f'{date} no data')
            continue

        df_stock = pd.concat([df_stock, df_stock_one_day, df_otc_one_day], ignore_index=True)
        print(f'{date} updated')

        count += 1
        if count == 20:
            count = 0
            df_stock.to_pickle(STOCK_PICKLE)
    df_stock.to_pickle(STOCK_PICKLE)
    print("===== 歷年上市上櫃股票每日交易資訊update完成 =====")
    return df_stock


if __name__ == '__main__':
    get_stock_otc_daily_info()
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)
