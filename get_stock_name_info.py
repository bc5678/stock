import requests
import pandas as pd


STOCK_NAME_PICKLE = 'stock_name_info.pkl'


def get_stock_name_info():
    print("===== 開始抓取上市股票名稱資訊 =====")
    df_stock = pd.read_html('https://isin.twse.com.tw/isin/C_public.jsp?strMode=2', encoding='big5-hkscs')[0]
    df_stock.columns = df_stock.iloc[0].to_list()
    df_stock = df_stock.iloc[2:]
    df_stock = df_stock.drop(columns=['國際證券辨識號碼(ISIN Code)', '備註'])
    df_stock = df_stock[(df_stock['CFICode'] == 'ESVUFR') | (df_stock['CFICode'] == 'CEOGEU') | (df_stock['CFICode'] == 'EDSDDR')]

    print("===== 開始抓取上櫃股票名稱資訊 =====")
    df_otc = pd.read_html('https://isin.twse.com.tw/isin/C_public.jsp?strMode=4', encoding='big5-hkscs')[0]
    df_otc.columns = df_otc.iloc[0].to_list()
    df_otc = df_otc.iloc[2:]
    df_otc = df_otc.drop(columns=['國際證券辨識號碼(ISIN Code)', '備註'])
    df_otc = df_otc[(df_otc['CFICode'] == 'ESVUFR') | (df_otc['CFICode'] == 'EPNRAR')]

    df = pd.concat([df_stock, df_otc], ignore_index=True)
    df[['證券代號', '證券名稱']] = df['有價證券代號及名稱'].str.split(expand=True)
    df = df.drop(columns=['有價證券代號及名稱'])
    print(df)
    
    df.to_pickle(STOCK_NAME_PICKLE)
    print("===== 上市上櫃股票名稱資訊update完成 =====")
    return df


if __name__ == '__main__':
    get_stock_name_info()
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)
