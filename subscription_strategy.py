import os
import datetime
import new_stock_subscription
import get_stock_daily_info
import pandas as pd


STRATEGY_1_PICKLE = 'subscription_strategy_1.pkl'
STRATEGY_PICKLE = 'subscription_strategy.pkl'

def strategy1(df_subscription, df_stock):
    # 如果每檔都買, 以撥券日的開盤價賣出, 預期獲益為何
    df = df_subscription[df_subscription['證券代號'].isin(df_stock['證券代號'])]
    df = df[df['中籤率(%)'] > 0]
    df = df[(df['證券代號'].str.endswith('A') == False) & (df['證券代號'].str.endswith('B') == False) & (df['證券代號'].str.endswith('C') == False)]

    #df = df[df['抽籤日期'].str.startswith('2018')]

    df_result = pd.DataFrame({'證券代號': [], '抽籤日期': [], '買入價': [], '賣出價': [], '賺賠':[]})

    print(df)
    for index, row in df.iterrows():
        sell_date = row['撥券日期(上市、上櫃日期)']
        x = stock_info_df[(stock_info_df['日期'] == sell_date) & (stock_info_df['證券代號'] == row['證券代號'])]

        date = datetime.datetime.strptime(sell_date, '%Y%m%d').date()
        if date > datetime.date.today():
            continue

        trials = 0
        while len(x) == 0 and trials < 10:
            date = date + datetime.timedelta(days=1)
            sell_date = date.strftime('%Y%m%d')
            x = stock_info_df[(stock_info_df['日期'] == sell_date) & (stock_info_df['證券代號'] == row['證券代號'])]
            trials += 1

        buy_price = row.loc['承銷價(元)']
        try:
            sell_price = x['開盤價'].iloc[0]
        except:
            # 特例: 撥券後過很久才重開交易
            if row['抽籤日期'] == '20181011' and row['證券代號'] == '4413':
                continue
            print(row)
            print(x)
            exit(-1)

        amount = row['申購股數']
        print(f"[{row['證券代號']}] {row['抽籤日期']} {sell_price*amount/100}-{buy_price*amount/100}-70 => {(sell_price-buy_price)/100*amount-70}")

        new_row = pd.DataFrame([{
            '證券代號': row['證券代號'], 
            '抽籤日期': row['抽籤日期'], 
            '買入價': buy_price*amount/100, 
            '賣出價': sell_price*amount/100, 
            '賺賠': (sell_price-buy_price)/100*amount-70
        }])
        df_result = pd.concat([df_result, new_row], ignore_index=True)

    df_result.to_pickle(STRATEGY_1_PICKLE)


def strategy(df_subscription, df_stock):
    # 如果每檔都買, 以撥券日的開盤價賣出, 預期獲益為何
    df = df_subscription[df_subscription['證券代號'].isin(df_stock['證券代號'])]
    df = df[df['中籤率(%)'] > 0]
    df = df[(df['證券代號'].str.endswith('A') == False) & (df['證券代號'].str.endswith('B') == False) & (df['證券代號'].str.endswith('C') == False)]

    #df = df[df['抽籤日期'].str.startswith('2018')]

    df_result = pd.DataFrame({'證券代號': [], '抽籤日期': [], '買入價': [], '賣出價': [], '賺賠': [], '策略1': [], '策略2': [], '策略3': []})

    print(df)
    for index, row in df.iterrows():
        strategy1 = strategy2 = strategy3 = True

        sell_date = row['撥券日期(上市、上櫃日期)']
        date = datetime.datetime.strptime(sell_date, '%Y%m%d').date()
        if date > datetime.date.today():
            continue

        buy_price = row.loc['承銷價(元)']
        compare_date = row['申購結束日']
        y = stock_info_df[(stock_info_df['日期'] == compare_date) & (stock_info_df['證券代號'] == row['證券代號'])]
        if len(y) == 0:
            strategy2 = strategy3 = False
        else:
            compare_price = y['開盤價'].iloc[0]
            if compare_price < buy_price*1.1:
                strategy2 = False
            if compare_price < buy_price*1.05:
                strategy3 = False

        x = stock_info_df[(stock_info_df['日期'] == sell_date) & (stock_info_df['證券代號'] == row['證券代號'])]

        trials = 0
        while len(x) == 0 and trials < 10:
            date = date + datetime.timedelta(days=1)
            sell_date = date.strftime('%Y%m%d')
            x = stock_info_df[(stock_info_df['日期'] == sell_date) & (stock_info_df['證券代號'] == row['證券代號'])]
            trials += 1

        try:
            sell_price = x['開盤價'].iloc[0]
        except:
            # 特例: 撥券後過很久才重開交易
            if row['抽籤日期'] == '20181011' and row['證券代號'] == '4413':
                continue
            print(row)
            print(x)
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
            '策略3': strategy3
        }])
        df_result = pd.concat([df_result, new_row], ignore_index=True)

    df_result.to_pickle(STRATEGY_PICKLE)


if __name__ == '__main__':
    new_stock_subscription_df = new_stock_subscription.get_new_stock_subscription_info()
    print(new_stock_subscription_df)
    print(new_stock_subscription_df.info())

    stock_info_df = get_stock_daily_info.get_stock_otc_daily_info()
    print(stock_info_df)
    print(stock_info_df.info())

    strategy(new_stock_subscription_df, stock_info_df)
