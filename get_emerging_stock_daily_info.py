import pandas as pd
import numpy as np
import requests
import io
import os
import datetime


START_DATE = datetime.date(2023, 12, 5)
END_DATE = datetime.date.today()
#END_DATE = datetime.date(2013, 8, 31)
STOCK_DAILY_INFO_URL = 'https://www.tpex.org.tw/web/emergingstock/historical/daily/EMDaily_dl.php?l=zh-tw&f=EMdes010.[DATE]-C.csv'
STOCK_DAILY_INFO_PICKLE = 'emerging_stock_daily_info.pkl'


def list_date(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y%m%d'))
        current_date += datetime.timedelta(days=1)
    return date_list


def stock_to_numeric(x):
    # 價位相關的欄位, 全部*100 後當成int存儲, 用來避免浮點數運算偏移
    # 若原本為NaN, 則改成0 (因為價位不可能為0, 所以可和正常值區分開來)
    for s in ['最後', '成交量', '成交金額', '筆數']:
        x[s] = pd.to_numeric(x[s], errors='coerce', downcast="float")

    x.fillna(value=0, inplace=True)

    for s in ['最後']:
        x[s] = (x[s]*100)

    for s in ['最後', '成交量', '成交金額', '筆數']:
        x[s] = np.rint(x[s]).astype(np.uint32)

    return x


def get_stock_daily_info(date):
    # Format: 西元年月日
    res = requests.get(STOCK_DAILY_INFO_URL.replace('[DATE]', date))

    # 沒交易的日期資料為空
    if len(res.text) == 0:
        return None

    lines = [l for l in res.text.split('\n') if len(l.split(','))>=10]
    df = pd.read_csv(io.StringIO(','.join(lines))).iloc[:-1, 1:]
    df.columns = df.iloc[0].to_list()
    df = df.reset_index(drop=True).iloc[1:, :]
    df = df.map(lambda s: (str(s).replace(',','').replace(' ', '')))
    print(df.columns)
    try:
        df = df.drop(columns=['證券名稱', '最後最佳報買價', '最後最佳報賣價', '日均價', '前日均價', '漲跌', '漲跌幅', '最高', '最低', '發行股數', '上市櫃進度日期', '上市櫃進度'])
    except KeyError:
        pass
    try:
        df = df.drop(columns=['名稱', '最高買', '最低賣', '日均價', '前日均價', '漲跌', '漲跌幅', '最高', '最低', '股本', '上市櫃日期', '進度'])
    except KeyError:
        pass
    try:
        df = df.drop(columns=['名稱', '最高買', '最低賣', '日均價', '前日均價', '漲跌', '漲跌幅', '最高', '最低', '發行股數', '上市櫃日期', '進度'])
    except KeyError:
        pass

    df = df.apply(stock_to_numeric, axis=1)
    df['日期'] = date
    return df


def get_emerging_stock_daily_info():
    print("===== 開始抓取歷年興櫃股票每日交易資訊 =====")
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
        if df_stock is None:
            print(f'{date} no data')
            continue

        df_stock_info = pd.concat([df_stock_info, df_stock], ignore_index=True)
        print(df_stock_info)
        print(df_stock_info.info())
        #input()
        count += 1
        if count == 10:
            count = 0
            df_stock_info.to_pickle(STOCK_DAILY_INFO_PICKLE)
    df_stock_info = df_stock_info.reset_index(drop=True)
    df_stock_info.to_pickle(STOCK_DAILY_INFO_PICKLE)
    print("===== 歷年上市上櫃股票每日交易資訊update完成 =====")
    return df_stock_info


if __name__ == '__main__':
    get_emerging_stock_daily_info()
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)
