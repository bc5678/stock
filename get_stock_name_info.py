import pandas as pd
import requests


STOCK_NAME_PICKLE = 'stock_name_info.pkl'


def get_stock_name_info():
    print("===== 開始抓取上市上櫃股票名稱資訊 =====")
    df1 = pd.read_html('https://isin.twse.com.tw/isin/C_public.jsp?strMode=2', encoding='big5-hkscs')[0]
    df1.columns = df1.iloc[0].to_list()
    df1 = df1.iloc[2:]
    df1 = df1.drop(columns=['國際證券辨識號碼(ISIN Code)', '備註'])
    df1 = df1[(df1['CFICode'] == 'ESVUFR') | (df1['CFICode'] == 'CEOGEU') | (df1['CFICode'] == 'EDSDDR')]

    df2 = pd.read_html('https://isin.twse.com.tw/isin/C_public.jsp?strMode=4', encoding='big5-hkscs')[0]
    df2.columns = df2.iloc[0].to_list()
    df2 = df2.iloc[2:]
    df2 = df2.drop(columns=['國際證券辨識號碼(ISIN Code)', '備註'])
    df2 = df2[(df2['CFICode'] == 'ESVUFR') | (df2['CFICode'] == 'EPNRAR')]

    df = pd.concat([df1, df2])
    df[['證券代號', '證券名稱']] = df['有價證券代號及名稱'].str.split(expand=True)
    df.insert(0, '證券名稱', df.pop('證券名稱'))
    df.insert(0, '證券代號', df.pop('證券代號'))
    df = df.drop(columns=['有價證券代號及名稱'])
    df.reset_index(drop=True, inplace=True)
    print(df)
    
    df.to_pickle(STOCK_NAME_PICKLE)
    print("===== 上市上櫃股票名稱資訊update完成 =====")
    return df


if __name__ == '__main__':
    get_stock_name_info()
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)
