import os
import datetime
import numpy as np
import pandas as pd
import get_subscription_info
import get_stock_daily_info
import get_emerging_daily_info


STRATEGY_PICKLE = 'subscription_strategy.pkl'


# 策略1: 全買
# 策略2: 最後購買日開盤價 >= 申購價*1.1 才買, 無資料不買 
# 策略3: 最後購買日開盤價 >= 申購價*1.05 才買, 無資料不買 
# 策略4: 最後購買日收盤價 >= 申購價*1.1 才買, 無資料不買 
# 策略5: 最後購買日收盤價 >= 申購價*1.05 才買, 無資料不買 
# 策略6: 最後購買日開盤價 >= 申購價*1.1 才買, 無資料買 
# 策略7: 最後購買日開盤價 >= 申購價*1.05 才買, 無資料買 
# 策略8: 最後購買日收盤價 >= 申購價*1.1 才買, 無資料買 
# 策略9: 最後購買日收盤價 >= 申購價*1.05 才買, 無資料買 
def strategy(df_stock, df_emerging, df_subscription):
    # 如果每檔都買, 以撥券日的開盤價賣出, 預期獲益為何
    df_result = pd.DataFrame({'證券代號': [], '抽籤日期': [], '買入價': [], '賣出價': [], '賺賠': [], 
                                '策略1': [], '策略2': [], '策略3': [], '策略4': [], '策略5': [], '策略6': [], '策略7': [], '策略8': [], '策略9': [], 
                                '撥券日_開盤價': [], '撥券日_收盤價': [], '撥券日_最高價': [], '撥券日_最低價': [],
                })

    print(df_subscription)
    for index, row in df_subscription.iterrows():
        strategy1 = strategy2 = strategy3 = strategy4 = strategy5 = strategy6 = strategy7 = strategy8 = strategy9 = True

        sell_date = row['撥券日期(上市、上櫃日期)']
        if datetime.datetime.strptime(sell_date, '%Y%m%d').date() > datetime.date.today():
            continue

        buy_price = row.loc['承銷價(元)']
        buy_date = row['申購結束日']
        buy_date_info1 = df_stock[(df_stock['日期'] == buy_date) & (df_stock['證券代號'] == row['證券代號'])]
        buy_date_info2 = df_emerging[(df_emerging['日期'] == buy_date) & (df_emerging['證券代號'] == row['證券代號'])]
        buy_date_info = pd.concat([buy_date_info1, buy_date_info2])           

        print(row['證券代號'], row['申購結束日'])
        if len(buy_date_info) == 0:
            strategy2 = strategy3 = strategy4 = strategy5 = False
        else:
            compare_price = [buy_date_info[x].iloc[0] for x in ['開盤價', '最後'] if not np.isnan(buy_date_info[x].iloc[0])][0]
                
            if compare_price < buy_price*1.1:
                strategy2 = False
                strategy6 = False
            if compare_price < buy_price*1.05:
                strategy3 = False
                strategy7 = False

            compare_price = [buy_date_info[x].iloc[0] for x in ['收盤價', '最後'] if not np.isnan(buy_date_info[x].iloc[0])][0]

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
            '策略1': strategy1, '策略2': strategy2, '策略3': strategy3, '策略4': strategy4, '策略5': strategy5, '策略6': strategy6, '策略7': strategy7, '策略8': strategy8, '策略9': strategy9,
            '撥券日_開盤價': sell_date_info['開盤價'].iloc[0], '撥券日_收盤價': sell_date_info['收盤價'].iloc[0], 
            '撥券日_最高價': sell_date_info['最高價'].iloc[0], '撥券日_最低價': sell_date_info['最低價'].iloc[0], 
        }])
        df_result = pd.concat([df_result, new_row], ignore_index=True)

    df_result.to_pickle(STRATEGY_PICKLE)
    return df_result


def score(df):
    scordf_emerging = pd.DataFrame({'策略1': [], '策略2': [], '策略3': [], '策略4': [], '策略5': [], '策略6': [], '策略7': [], '策略8': [],
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
    scordf_emerging = pd.concat([scordf_emerging, new_row], ignore_index=True)

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
    scordf_emerging = pd.concat([scordf_emerging, new_row], ignore_index=True)
    print(scordf_emerging)


def prune_df(df_stock, df_emerging, df_subscription):
    print(len(df_stock), len(df_emerging), len(df_subscription))

    df_stock = df_stock[df_stock['證券代號'].isin(df_subscription['證券代號'].unique())]
    df_emerging = df_emerging[df_emerging['證券代號'].isin(df_subscription['證券代號'].unique())]
    df_subscription = df_subscription[df_subscription['證券代號'].isin(df_stock['證券代號'].unique()) | df_subscription['證券代號'].isin(df_emerging['證券代號'].unique())]
    print(len(df_stock), len(df_emerging), len(df_subscription))

    for stock in df_subscription['證券代號'].unique():
        subscribe_date_list = df_subscription[df_subscription['證券代號'] == stock]['抽籤日期']
        extend_date_list = []
        for date in subscribe_date_list:
            input_datetime = datetime.datetime.strptime(date, "%Y%m%d")
            extend_date_list.extend([((input_datetime - datetime.timedelta(days=i))).strftime("%Y%m%d") for i in range(15, 0, -1)])
            extend_date_list.append(date)
            extend_date_list.extend([(input_datetime + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(1, 16)])
        df_stock = df_stock.drop(df_stock[(df_stock['證券代號'] == stock) & ~df_stock['日期'].isin(extend_date_list)].index)
        df_emerging = df_emerging.drop(df_emerging[(df_emerging['證券代號'] == stock) & ~df_emerging['日期'].isin(extend_date_list)].index)
        print(len(df_stock), len(df_emerging))

    return df_stock, df_emerging, df_subscription


if __name__ == '__main__':
#    pd.set_option('display.max_columns', None)
#    pd.set_option('display.max_rows', None)
#    pd.set_option('display.width', 1000)

    # 更新申購資訊
    '''df_subscription = get_subscription_info.get_subscription_info()
    print(df_subscription)
    print(df_subscription.info())

    # 更新上市上櫃歷史股價資訊
    df_stock = get_stock_daily_info.get_stock_otc_daily_info()
    print(df_stock)
    print(df_stock.info())

    # 更新興櫃歷史股價資訊
    df_emerging = get_emerging_daily_info.get_emerging_daily_info()
    print(df_emerging)
    print(df_emerging.info())

    # 將申購資訊, 上市上櫃興櫃歷史資訊, 去除大量不需要的部分以加快處理速度
    df_stock, df_emerging, df_subscription = prune_df(df_stock, df_emerging, df_subscription)
    df_stock.to_pickle('stock_daily_info_subset1.pkl')
    df_emerging.to_pickle('emerging_daily_info_subset1.pkl')
    df_subscription.to_pickle('subscription_info_subset1.pkl')'''

    df_stock = pd.read_pickle('stock_daily_info_subset1.pkl')
    df_emerging = pd.read_pickle('emerging_daily_info_subset1.pkl')
    df_subscription = pd.read_pickle('subscription_info_subset1.pkl')
    df = strategy(df_stock, df_emerging, df_subscription)
    
    print(df)
    score(df)
    
     
    #print(len(df[df['撥券日_開盤價'] < df['撥券日_收盤價']]))
    #print(len(df[df['撥券日_開盤價'] >= df['撥券日_收盤價']]))

    #print(len(df[df['撥券日_收盤價'] < df['撥券前日_收盤價']]))
    #print(len(df[df['撥券日_收盤價'] >= df['撥券前日_收盤價']]))
