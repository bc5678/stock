import datetime
import requests
import pandas as pd

START_DATE = datetime.date(2010, 1, 1)
END_DATE = datetime.date.today()
STOCK_DIVIDEND_URL = 'https://www.twse.com.tw/exchangeReport/TWT49U?response=html&strDate=[START_DATE]&endDate=[END_DATE]'
OTC_DIVIDEND_URL = 'https://www.tpex.org.tw/web/stock/exright/dailyquo/exDailyQ_result.php?l=zh-tw&d=[START_DATE]&ed=[END_DATE]'
DIVIDEND_PICKLE = 'dividend_info.pkl'


def ROC_date_convert(x):
    x = x.replace('年', '/').replace('月', '/').replace('日', '/')
    x = x.split('/')
    return str(int(x[0])+1911) + x[1] + x[2]


def get_stock_dividend(start_date, end_date):
    df = pd.read_html(STOCK_DIVIDEND_URL.replace('[START_DATE]', start_date).replace('[END_DATE]', end_date))[0]
    df = df.drop(columns=['權值+息值', '漲停價格', '跌停價格', '開盤競價基準', '減除股利參考價', '詳細資料', '最近一次申報資料 季別/日期', '最近一次申報每股 (單位)淨值', '最近一次申報每股 (單位)盈餘'])
    df.rename(columns={'資料日期': '日期'}, inplace=True)
    df['日期'] = df['日期'].apply(ROC_date_convert)
    df['權/息'] = df['權/息'].apply(lambda x: '除'+x)
    df = df.map(lambda x: str(x).replace(',','').replace(' ', ''))

    return df


def get_otc_dividend(start_date, end_date):
    # parse YYYYMMDD to YYY/MM/DD
    start_date = f'{int(start_date[:4])-1911}/{start_date[4:6]}/{start_date[6:]}'
    end_date = f'{int(end_date[:4])-1911}/{end_date[4:6]}/{end_date[6:]}'
    
    res = requests.get(OTC_DIVIDEND_URL.replace('[START_DATE]', start_date).replace('[END_DATE]', end_date))

    columns = ['日期', '股票代號', '股票名稱', '除權息前收盤價', '除權息參考價', '權值', '息值', '權值+息值', '權/息', '漲停價', '跌停價',
               '開始交易基準價', '減除股利參考價', '現金股利', '每仟股無償配股', '員工紅利轉增資', '現金增資股數', '現金增資認購價', '公開承銷股數', 
               '員工認購股數', '原股東認購股數', '按持股比例仟股認購']
    df = pd.DataFrame(res.json()['aaData'], columns=columns)
    df = df.drop(columns=['權值', '息值', '權值+息值', '漲停價', '跌停價', '開始交易基準價', '減除股利參考價', '現金股利', '每仟股無償配股', '員工紅利轉增資', 
                          '現金增資股數', '現金增資認購價', '公開承銷股數', '員工認購股數', '原股東認購股數', '按持股比例仟股認購'])
    df['日期'] = df['日期'].apply(ROC_date_convert)
    df = df.map(lambda x: str(x).replace(',','').replace(' ', ''))

    return df


def get_dividend(start_date, end_date):
    start_date = start_date.strftime('%Y%m%d')
    end_date = end_date.strftime('%Y%m%d')
    print('===== 開始抓取歷年除權息資訊 =====')
    df = pd.concat([get_stock_dividend(start_date, end_date), get_otc_dividend(start_date, end_date)], ignore_index=True)
    print('===== 歷年除權息資訊update完成 =====')
    df.to_pickle(DIVIDEND_PICKLE)

    return df
    

if __name__ == '__main__':
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)
    print(get_dividend(START_DATE, END_DATE))
