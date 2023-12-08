import io
import json
import datetime
import requests
import numpy as np
import pandas as pd
import urllib.request
import get_subscription_info


def get_stock_runtime_info(stock_list):
    # 可一次query到上市或上櫃的公司資料
    stocks_text = '|'.join(f'tse_{stock}.tw|otc_{stock}.tw' for stock in stock_list)
    url = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch='+ stocks_text + '&json=1&delay=0&_=1552123547443'
    data = json.loads(urllib.request.urlopen(url).read())

    columns = ['c','n','z','tv','v','o','h','l','y']
    df = pd.DataFrame(data['msgArray'], columns=columns)
    df.columns = ['股票代號','股票名稱','成交價','成交量','累積成交量','開盤價','最高價','最低價','昨收價']

    try:
        df['開盤價'] = (df['開盤價'].astype(float) * 100).astype(int)
    except ValueError:
        print(f'{stock} 還沒有開盤價！')

    return df
    
    
def get_emerging_runtime_info(stock_list):
    # 這個頁面一次抓到所有當天的興櫃股票, 所以後面還要濾個股出來
    url = 'https://www.tpex.org.tw/storage/emgstk/ch/new.csv'
    res = requests.get(url)
    res.encoding = 'big5'

    lines = [l for l in res.text.split('\n') if len(l.split(','))>=10]
    df = pd.read_csv(io.StringIO(''.join(lines)))
    df = df.map(lambda s: (str(s).replace(',','').replace(' ', '')))
    df = df[df['代號'].isin(stock_list)]
    df.rename(columns={'代號': '股票代號', '名稱': '股票名稱'}, inplace=True)

    try:
        df['成交'] = (df['成交'].astype(float) * 100).astype(int)
    except ValueError:
        print(f'{stock} 還沒有開盤價！')

    return df


if __name__ == '__main__':
    date = datetime.datetime.today().strftime('%Y%m%d')
#    date = '20231206'

    subscription_df = get_subscription_info.get_subscription_info()
    print(subscription_df)

    stock_list = subscription_df[subscription_df['申購結束日'] == date]['證券代號'].to_list()

    if len(stock_list) == 0:
        print('今天沒有推薦申購股票')

    for stock in stock_list:
        print(stock)
        # 直接從上市上櫃, 和興櫃兩個頁面都去抓資料, 看哪個抓得到
        df = pd.concat([get_stock_runtime_info([stock]), get_emerging_runtime_info([stock])], ignore_index=True)
        if len(df) == 0:
            print(f'資訊不足, 無法推薦')
            continue

        df = df.iloc[0]
        # 抓得到資料的一邊, 值不會是numpy.nan, 就可以拿來使用
        current_price = [x for x in [df['開盤價'], df['成交']] if not np.isnan(x)][0]
        buy_price = subscription_df[(subscription_df['申購結束日'] == date) & (subscription_df['證券代號'] == stock)]['承銷價(元)'].iloc[0]
        if current_price >= buy_price*1.1:
            print(f"建議抽股票: [{df['股票代號']}][{df['股票名稱']}] : {current_price} >= {buy_price} * 1.1 = {buy_price * 1.1}")
        else:
            print(f"建議不抽股票: [{df['股票代號']}][{df['股票名稱']}] : {current_price} < {buy_price} * 1.1 = {buy_price * 1.1}")
    input()
