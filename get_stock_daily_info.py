import pandas as pd
import numpy as np
import requests
import io
import os
import datetime


START_DATE = datetime.date(2023, 11, 26)
END_DATE = datetime.date.today()
#END_DATE = datetime.date(2010, 12, 31)
STOCK_DAILY_INFO_URL = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=[DATE]&type=ALLBUT0999&_=1649743235999'
STOCK_DAILY_INFO_PICKLE = 'stock_daily_info.pkl'
OTC_DAILY_INFO_URL = 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=csv&d=[DATE]&se=EW&s=0,asc,0'


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


def stock_to_numeric(x):
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


def get_stock_daily_info(date):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/111.25 (KHTML, like Gecko) Chrome/99.0.2345.81 Safari/123.36'}

    # Format: 西元年月日
    res = requests.get(STOCK_DAILY_INFO_URL.replace('[DATE]', date), headers=headers)

    # 沒交易的日期資料為空
    if len(res.text) == 0:
        return None

    lines = [l for l in res.text.split('\n') if len(l.split(',"'))>=10]
    df = pd.read_csv(io.StringIO(','.join(lines))).iloc[:, :-1]
    df = df.map(lambda s: (str(s).replace('=','').replace(',','').replace('"',''))).iloc[:,:-1]
    df = df.drop(columns=['證券名稱', '漲跌(+/-)', '漲跌價差'])
    df = df.apply(stock_to_numeric, axis=1)
    df['日期'] = date
    return df


def get_otc_daily_info(date):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/111.25 (KHTML, like Gecko) Chrome/99.0.2345.81 Safari/123.36'}

    # Format: 民國年/月/日
    date = str(int(date)-19110000)
    if len(date) == 7:
        res = requests.get(OTC_DAILY_INFO_URL.replace('[DATE]', f'{date[0:3]}/{date[3:5]}/{date[5:7]}'), headers=headers)
    elif len(date) == 6:
        res = requests.get(OTC_DAILY_INFO_URL.replace('[DATE]', f'{date[0:2]}/{date[2:4]}/{date[4:6]}'), headers=headers)

    lines = [l for l in res.text.split('\n') if len(l.split(','))>=10]

    # 沒交易的日期仍會有內容, 所以改為確認parse完後沒data
    if len(lines) == 0:
        return None

    df = pd.read_csv(io.StringIO(','.join(lines)))
    df = df.map(lambda s: (str(s).replace(',',''))).iloc[:,:-3]
    df = df.drop(columns=['名稱', '漲跌'])

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
    df = df.apply(stock_to_numeric, axis=1)
    df['日期'] = str(int(date)+19110000)

    return df


def get_stock_otc_daily_info():
    print("===== 開始抓取歷年上市上櫃股票每日交易資訊 =====")
    if os.path.isfile(STOCK_DAILY_INFO_PICKLE):
        df_stock_info = pd.read_pickle(STOCK_DAILY_INFO_PICKLE)
        existed_date_list = df_stock_info['日期'].unique()
    else:
        df_stock_info = None
        existed_date_list = []
    
    count = 0
    for date in list_date(START_DATE, END_DATE):
        if date in existed_date_list:
            print(f'{date} exist')
            continue 
        df_stock = get_stock_daily_info(date)
        df_otc = get_otc_daily_info(date)
        if df_stock is None or df_otc is None:
            print(f'{date} no data')
            continue
        #print(df_stock)
        #print(df_stock.info())

        df_stock_info = pd.concat([df_stock_info, df_stock])
        df_stock_info = pd.concat([df_stock_info, df_otc])
        print(df_stock_info)
        print(df_stock_info.info())
        #input()
        count += 1
        if count == 20:
            count = 0
            df_stock_info.to_pickle(STOCK_DAILY_INFO_PICKLE)
    df_stock_info = df_stock_info.reset_index(drop=True)
    df_stock_info.to_pickle(STOCK_DAILY_INFO_PICKLE)
    print("===== 歷年上市上櫃股票每日交易資訊update完成 =====")
    return df_stock_info


if __name__ == '__main__':
    get_stock_otc_daily_info()
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('max_colwidth', 400)
