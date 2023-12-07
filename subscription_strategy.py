import os
import datetime
import new_stock_subscription
import get_stock_daily_info
import get_emerging_stock_daily_info
import pandas as pd


STRATEGY_PICKLE = 'subscription_strategy.pkl'


# 策略1: 全買
# 策略2: 最後購買日開盤價 >= 申購價*1.1 才買, 無資料(如初上市上櫃)不買 
# 策略3: 最後購買日開盤價 >= 申購價*1.05 才買, 無資料(如初上市上櫃)不買 
# 策略4: 最後購買日收盤價 >= 申購價*1.1 才買, 無資料(如初上市上櫃)不買 
# 策略5: 最後購買日收盤價 >= 申購價*1.05 才買, 無資料(如初上市上櫃)不買 
# 策略6: 最後購買日開盤價 >= 申購價*1.1 才買, 無資料(如初上市上櫃)買 
# 策略7: 最後購買日開盤價 >= 申購價*1.05 才買, 無資料(如初上市上櫃)買 
# 策略8: 最後購買日收盤價 >= 申購價*1.1 才買, 無資料(如初上市上櫃)買 
# 策略9: 最後購買日收盤價 >= 申購價*1.05 才買, 無資料(如初上市上櫃)買 
def strategy(df, df_stock, df_emerging):
    # 如果每檔都買, 以撥券日的開盤價賣出, 預期獲益為何
    df = df[df['中籤率(%)'] > 0]
    df = df[(df['證券代號'].str.endswith('A') == False) & (df['證券代號'].str.endswith('B') == False) & (df['證券代號'].str.endswith('C') == False)]

    df_result = pd.DataFrame({'證券代號': [], '抽籤日期': [], '買入價': [], '賣出價': [], '賺賠': [], '策略1': [], '策略2': [], '策略3': [], '策略4': [], '策略5': [], '策略6': [], '策略7': [], 
                                '策略8': [], 
                                '策略9': [], 
                                '撥券日_開盤價': [],
                                '撥券日_收盤價': [],
                                '撥券日_最高價': [],
                                '撥券日_最低價': [],
                })

    print(df)
    for index, row in df.iterrows():
        strategy1 = strategy2 = strategy3 = strategy4 = strategy5 = strategy6 = strategy7 = strategy8 = strategy9 = True
        stock_type = ''

        sell_date = row['撥券日期(上市、上櫃日期)']
        if datetime.datetime.strptime(sell_date, '%Y%m%d').date() > datetime.date.today():
            continue

        buy_price = row.loc['承銷價(元)']
        buy_date = row['申購結束日']
        buy_date_info = df_stock[(df_stock['日期'] == buy_date) & (df_stock['證券代號'] == row['證券代號'])]
        if len(buy_date_info) > 0:
            stock_type = 'stock_otc'
        else:
            buy_date_info = df_emerging[(df_emerging['日期'] == buy_date) & (df_emerging['證券代號'] == row['證券代號'])]
            if len(buy_date_info) > 0:
                stock_type = 'emerging'
            

        print(row['證券代號'], row['申購結束日'])
        if len(buy_date_info) == 0:
            strategy2 = strategy3 = strategy4 = strategy5 = False
        else:
            if stock_type == 'stock_otc':
                compare_price = buy_date_info['開盤價'].iloc[0]
            else:
                compare_price = buy_date_info['最後'].iloc[0]
                
            if compare_price < buy_price*1.1:
                strategy2 = False
                strategy6 = False
            if compare_price < buy_price*1.05:
                strategy3 = False
                strategy7 = False

            if stock_type == 'stock_otc':
                compare_price = buy_date_info['收盤價'].iloc[0]
            else:
                compare_price = buy_date_info['最後'].iloc[0]

            if compare_price < buy_price*1.1:
                strategy4 = False
                strategy8 = False
            if compare_price < buy_price*1.05:
                strategy5 = False
                strategy9 = False

        sell_date = row['撥券日期(上市、上櫃日期)']
        sell_date_info = df_stock[(df_stock['日期'] == sell_date) & (df_stock['證券代號'] == row['證券代號'])]
        trials = 0
        date = datetime.datetime.strptime(sell_date, '%Y%m%d')
        while len(sell_date_info) == 0 and trials < 10:
            date = date + datetime.timedelta(days=1)
            sell_date = date.strftime('%Y%m%d')
            sell_date_info = df_stock[(df_stock['日期'] == sell_date) & (df_stock['證券代號'] == row['證券代號'])]
            trials += 1

        if len(sell_date_info) == 0:
            sell_date = row['撥券日期(上市、上櫃日期)']
            sell_date_info = df_emerging[(df_emerging['日期'] == sell_date) & (df_emerging['證券代號'] == row['證券代號'])]
            trials = 0
            date = datetime.datetime.strptime(sell_date, '%Y%m%d')
            while len(sell_date_info) == 0 and trials < 10:
                date = date + datetime.timedelta(days=1)
                sell_date = date.strftime('%Y%m%d')
                sell_date_info = df_emerging[(df_emerging['日期'] == sell_date) & (df_emerging['證券代號'] == row['證券代號'])]
                trials += 1
        
        try:
            sell_price = sell_date_info['開盤價'].iloc[0]
        except:
            # 特例: 撥券後過很久才重開交易
            if row['抽籤日期'] == '20181011' and row['證券代號'] == '4413':
                continue
            print(row)
            print(sell_date_info)
            continue
            exit(-1)


        amount = row['申購股數']
        print(f"[{row['證券代號']}] {row['抽籤日期']} {sell_price*amount/100}-{buy_price*amount/100}-70 => {(sell_price-buy_price)/100*amount-70}")

        new_row = pd.DataFrame([{
            '證券代號': row['證券代號'], 
            '抽籤日期': row['抽籤日期'], 
            '買入價': buy_price*amount/100, 
            '賣出價': sell_price*amount/100, 
            '賺賠': (sell_price-buy_price)/100*amount-70,
            '策略1': strategy1,
            '策略2': strategy2,
            '策略3': strategy3,
            '策略4': strategy4,
            '策略5': strategy5,
            '策略6': strategy6,
            '策略7': strategy7,
            '策略8': strategy8,
            '策略9': strategy9,
            '撥券日_開盤價': sell_date_info['開盤價'].iloc[0], 
            '撥券日_收盤價': sell_date_info['收盤價'].iloc[0],
            '撥券日_最高價': sell_date_info['最高價'].iloc[0],
            '撥券日_最低價': sell_date_info['最低價'].iloc[0], 
        }])
        df_result = pd.concat([df_result, new_row], ignore_index=True)

    df_result.to_pickle(STRATEGY_PICKLE)
    return df_result


def score(df):
    score_df = pd.DataFrame({'策略1': [], '策略2': [], '策略3': [], '策略4': [], '策略5': [], '策略6': [], '策略7': [], '策略8': [],
                '策略9': []
               })
    new_row = pd.DataFrame({
        '策略1': df['策略1'].sum()/df['策略1'].sum(),
        '策略2': df['策略2'].sum()/df['策略1'].sum(),
        '策略3': df['策略3'].sum()/df['策略1'].sum(),
        '策略4': df['策略4'].sum()/df['策略1'].sum(),
        '策略5': df['策略5'].sum()/df['策略1'].sum(),
        '策略6': df['策略6'].sum()/df['策略1'].sum(),
        '策略7': df['策略7'].sum()/df['策略1'].sum(),
        '策略8': df['策略8'].sum()/df['策略1'].sum(),
        '策略9': df['策略9'].sum()/df['策略1'].sum()
    }, index=['購買檔數/全部檔數'])
    score_df = pd.concat([score_df, new_row])

    new_row = pd.DataFrame({
        '策略1': df[df['賺賠'] < 0]['策略1'].sum() / df['策略1'].sum(),
        '策略2': df[df['賺賠'] < 0]['策略2'].sum() / df['策略2'].sum(),
        '策略3': df[df['賺賠'] < 0]['策略3'].sum() / df['策略3'].sum(),
        '策略4': df[df['賺賠'] < 0]['策略4'].sum() / df['策略4'].sum(),
        '策略5': df[df['賺賠'] < 0]['策略5'].sum() / df['策略5'].sum(),
        '策略6': df[df['賺賠'] < 0]['策略6'].sum() / df['策略6'].sum(),
        '策略7': df[df['賺賠'] < 0]['策略7'].sum() / df['策略7'].sum(),
        '策略8': df[df['賺賠'] < 0]['策略8'].sum() / df['策略8'].sum(),
        '策略9': df[df['賺賠'] < 0]['策略9'].sum() / df['策略9'].sum()
    }, index=['賠錢檔數/購買檔數'])
    score_df = pd.concat([score_df, new_row])
    print(score_df)


def prune_df(s_df, e_df, n_df):
    print(len(s_df))
    print(len(e_df))
    print(len(n_df))

    s_df = s_df[s_df['證券代號'].isin(n_df['證券代號'].unique())]
    print(len(s_df))

    e_df = e_df[e_df['證券代號'].isin(n_df['證券代號'].unique())]
    print(len(e_df))

    n_df = n_df[n_df['證券代號'].isin(s_df['證券代號'].unique()) | n_df['證券代號'].isin(e_df['證券代號'].unique())]
    print(len(n_df))

    for stock in n_df['證券代號'].unique():
        n_date_list = n_df[n_df['證券代號'] == stock]['抽籤日期'].unique()
        extend_date_list = []
        for date in n_date_list:
            input_datetime = datetime.datetime.strptime(date, "%Y%m%d")
            extend_date_list.extend([((input_datetime - datetime.timedelta(days=i))).strftime("%Y%m%d") for i in range(15, 0, -1)])
            extend_date_list.append(date)
            extend_date_list.extend([(input_datetime + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(1, 16)])
        s_df = s_df.drop(s_df[(s_df['證券代號'] == stock) & ~s_df['日期'].isin(extend_date_list)].index)
        e_df = e_df.drop(e_df[(e_df['證券代號'] == stock) & ~e_df['日期'].isin(extend_date_list)].index)
        print(len(s_df))
        print(len(e_df))

    return s_df, e_df, n_df


if __name__ == '__main__':
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)

    # 更新申購資訊
    '''new_stock_subscription_df = new_stock_subscription.get_new_stock_subscription_info()
    print(new_stock_subscription_df)
    print(new_stock_subscription_df.info())

    # 更新上市上櫃歷史股價資訊
    stock_info_df = get_stock_daily_info.get_stock_otc_daily_info()
    print(stock_info_df)
    print(stock_info_df.info())

    # 更新興櫃歷史股價資訊
    emerging_info_df = get_emerging_stock_daily_info.get_emerging_stock_daily_info()
    print(emerging_info_df)
    print(emerging_info_df.info())

    # 將申購資訊, 上市上櫃興櫃歷史資訊, 去除大量不需要的部分以加快處理速度
    stock_info_df, emerging_info_df, new_stock_subscription_df = prune_df(stock_info_df, emerging_info_df, new_stock_subscription_df)
    stock_info_df.to_pickle('stock_daily_info_subset1.pkl')
    emerging_info_df.to_pickle('emerging_stock_daily_info_subset1.pkl')
    new_stock_subscription_df.to_pickle('new_stock_subscription_subset1.pkl')'''

    stock_info_df = pd.read_pickle('stock_daily_info_subset1.pkl')
    emerging_info_df = pd.read_pickle('emerging_stock_daily_info_subset1.pkl')
    new_stock_subscription_df = pd.read_pickle('new_stock_subscription_subset1.pkl')
    df = strategy(new_stock_subscription_df, stock_info_df, emerging_info_df)
    
    print(df)
    print(df[(df['策略3'] == True) & (df['賺賠'] < 0)])
    score(df)
    
     
    #print(len(df[df['撥券日_開盤價'] < df['撥券日_收盤價']]))
    #print(len(df[df['撥券日_開盤價'] >= df['撥券日_收盤價']]))

    #print(len(df[df['撥券日_收盤價'] < df['撥券前日_收盤價']]))
    #print(len(df[df['撥券日_收盤價'] >= df['撥券前日_收盤價']]))
