import pandas as pd
import io
import json
import datetime
import requests
import urllib.request
import new_stock_subscription


def get_stock_runtime_info(stock_list):
    stocks_text = '|'.join(f'tse_{stock}.tw|otc_{stock}.tw' for stock in stock_list)
    url = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch='+ stocks_text + '&json=1&delay=0&_=1552123547443'
    data = json.loads(urllib.request.urlopen(url).read())

    columns = ['c','n','z','tv','v','o','h','l','y']
    df = pd.DataFrame(data['msgArray'], columns=columns)
    df.columns = ['股票代號','股票名稱','成交價','成交量','累積成交量','開盤價','最高價','最低價','昨收價']

    try:
#        df['成交價'] = df['成交價'].astype(float)
        df['開盤價'] = (df['開盤價'].astype(float) * 100).astype(int)
#        df['最高價'] = df['最高價'].astype(float)
#        df['最低價'] = df['最低價'].astype(float)
#        df['昨收價'] = df['昨收價'].astype(float)

#        df['成交量'] = df['成交量'].astype(int)
#        df['累積成交量'] = df['累積成交量'].astype(int)
#        df.insert(9, "漲跌百分比", 0.0) 
    except ValueError:
        print(f'{stock} 還沒有開盤價！')

    
    # 新增漲跌百分比
#    for x in range(len(df.index)):
#        if df['成交價'].iloc[x] != '-':
#            df.iloc[x, [2,3,4,5,6,7,8]] = df.iloc[x, [2,3,4,5,6,7,8]].astype(float)
#            df['漲跌百分比'].iloc[x] = (df['成交價'].iloc[x] - df['昨收價'].iloc[x])/df['昨收價'].iloc[x] * 100
    
    # 紀錄更新時間
    #time = datetime.datetime.now()  
    #print("更新時間:" + str(time.hour)+":"+str(time.minute))
    return df
    
    #start_time = datetime.datetime.strptime(str(time.date())+'9:30', '%Y-%m-%d%H:%M')
    #end_time =  datetime.datetime.strptime(str(time.date())+'13:30', '%Y-%m-%d%H:%M')
    
def get_emerging_runtime_info(stock_list):
    url = 'https://www.tpex.org.tw/storage/emgstk/ch/new.csv'
    res = requests.get(url)
    res.encoding = 'big5'

    lines = [l for l in res.text.split('\n') if len(l.split(','))>=10]
    df = pd.read_csv(io.StringIO(','.join(lines)))
    df = df.reset_index(drop=True)
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
    #date = '20231206'

    n_df = new_stock_subscription.get_new_stock_subscription_info()
    print(n_df)

    stock_list = n_df[n_df['申購結束日'] == date]['證券代號'].to_list()

    if len(stock_list) == 0:
        print('今天沒有推薦申購股票')

    for stock in stock_list:
        print(stock)
        stock_type = ''
        df = get_stock_runtime_info([stock])
        if len(df) == 0:
            df = get_emerging_runtime_info([stock])
            if len(df) == 0:
                print(f'資訊不足, 無法推薦')
                continue
            else:
                stock_type = 'emerging'
        else:
            stock_type = 'stock_otc'

        df = df.iloc[0]
        if stock_type == 'stock_otc':
            current_price = df['開盤價']
        else:
            current_price = df['成交']
        buy_price = n_df[(n_df['申購結束日'] == date) & (n_df['證券代號'] == stock)]['承銷價(元)'].iloc[0]
        if current_price >= buy_price*1.1:
            print(f"建議抽股票: [{df['股票代號']}][{df['股票名稱']}] : {current_price} >= {buy_price} * 1.1 = {buy_price * 1.1}")
        else:
            print(f"建議不抽股票: [{df['股票代號']}][{df['股票名稱']}] : {current_price} < {buy_price} * 1.1 = {buy_price * 1.1}")
    input()
