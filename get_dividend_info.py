import io
import os
import datetime
import requests
import numpy as np
import pandas as pd
#https://www.twse.com.tw/rwd/zh/exRight/TWT48U?response=csv

START_YEAR = 2010
END_YEAR = datetime.date.today().year
SUBSCRIPTION_URL = 'https://www.twse.com.tw/rwd/zh/announcement/publicForm?date=[YEAR]0101&response=csv'
SUBSCRIPTION_PICKLE = 'subscription_info.pkl'

def get_twse_dividend_history(start_date: str, end_date: str):
    url = f"https://www.twse.com.tw/exchangeReport/TWT49U?response=html&strDate={start_date}&endDate={end_date}"
    dividend_history = pd.read_html(url)

    return dividend_history[0]



def get_subscription_by_year(year):
    # Format: 西元年月日
    res = requests.get(SUBSCRIPTION_URL.replace('[YEAR]', str(year)))

    lines = [l for l in res.text.replace('Co."," Ltd.', 'Co., Ltd.').split('\n') if len(l.split(',"'))>=10]
    df = pd.read_csv(io.StringIO(','.join(lines))).iloc[:, :]
    replace_map = {}
    for column in df.columns:
        if column != column.strip():
            replace_map[column] = column.strip()
    if replace_map:
        df.rename(columns=replace_map, inplace=True)
    df = df[df['發行市場'] != '中央登錄公債']
    df = df.drop(columns=['序號', '證券名稱', '主辦券商', '總承銷金額(元)', '總合格件', '承銷股數', '實際承銷股數', '實際承銷價(元)', '取消公開抽籤'])
    df = df.map(lambda s: str(s).replace(',','')).iloc[:,:-1]
    df = df.apply(ROC_date_convert, axis=1)
    df = df.apply(price_to_int, axis=1)
    return df


def get_subscription_info():
    print("===== 開始抓取歷年公開申購資訊 =====")
    if os.path.isfile(SUBSCRIPTION_PICKLE):
        df_all = pd.read_pickle(SUBSCRIPTION_PICKLE)
        existed_date_list = df_all['抽籤日期'].unique()
    else:
        df_all = None
        existed_date_list = []
   
    count = 0
    for year in range(START_YEAR, END_YEAR+1):
        print(year)
        for existed_date in existed_date_list:
            if (str(year) in existed_date) and (year != datetime.date.today().year):
                print(f'{year} exist')
                break
        else:
            df = get_subscription_by_year(year)
            print(df)
            df_all = pd.concat([df_all, df], ignore_index=True)
    df_all = df_all.drop_duplicates().reset_index(drop=True)
    df_all.to_pickle(SUBSCRIPTION_PICKLE)
    print("===== 歷年公開申購資訊update完成 =====")
    return df_all


if __name__ == '__main__':
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)
    get_subscription_info()
    
