import io
import os
import datetime
import requests
import pandas as pd

START_YEAR = 2010
END_YEAR = datetime.date.today().year
NEW_STOCK_SUBSCRIPTION_URL = 'https://www.twse.com.tw/rwd/zh/announcement/publicForm?date=[YEAR]0101&response=csv'
NEW_STOCK_SUBSCRIPTION_PICKLE = 'new_stock_subscription.pkl'


def ROC_date_convert(data):
    for c in ['抽籤日期', '申購開始日', '申購結束日', '撥券日期(上市、上櫃日期)']:
        x = data[c].split('/')
        data[c] = str(int(x[0])+1911) + x[1] + x[2]
    return data


def get_new_stock_subscription(year):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/111.25 (KHTML, like Gecko) Chrome/99.0.2345.81 Safari/123.36'}

    # Format: 西元年月日
    res = requests.get(NEW_STOCK_SUBSCRIPTION_URL.replace('[YEAR]', str(year)), headers=headers)

    lines = [l for l in res.text.replace('Co."," Ltd.', 'Co., Ltd.').split('\n') if len(l.split(',"'))>=10]
    df = pd.read_csv(io.StringIO(','.join(lines))).iloc[:, :]
    replace_map = {}
    for column in df.columns:
        if column != column.strip():
            replace_map[column] = column.strip()
    if replace_map:
        df.rename(columns=replace_map, inplace=True)
    df = df.drop(columns=['序號', '證券名稱', '主辦券商', '總承銷金額(元)', '總合格件', '承銷股數', '實際承銷股數', '實際承銷價(元)', '申購股數', '取消公開抽籤'])
    df = df.map(lambda s: str(s).replace(',','')).iloc[:,:-1]
    df = df.apply(ROC_date_convert, axis=1)
    return df


if __name__ == '__main__':
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('max_colwidth', 400)
    if os.path.isfile(NEW_STOCK_SUBSCRIPTION_PICKLE):
        df_all = pd.read_pickle(NEW_STOCK_SUBSCRIPTION_PICKLE)
        existed_date_list = df_all['抽籤日期'].unique()
    else:
        df_all = None
        existed_date_list = []
   
    count = 0
    for year in range(START_YEAR, END_YEAR+1):
        print(year)
        for existed_date in existed_date_list:
            if str(year) in existed_date:
                print(f'{year} exist')
                break
        else:
            df = get_new_stock_subscription(year)
            print(df)
            df_all = pd.concat([df_all, df])
    df_all.to_pickle(NEW_STOCK_SUBSCRIPTION_PICKLE)
    print(df_all)
