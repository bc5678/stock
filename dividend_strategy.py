import os
import datetime
import pandas as pd
import get_stock_daily_info


PICKLE = 'dividend_strategy.pkl'


def prune_df(df_stock, df_dividend):
    print(len(df_stock), len(df_dividend))

    df_stock = df_stock[df_stock['證券代號'].isin(df_dividend['股票代號'].unique())]
    df_dividend = df_dividend[df_dividend['股票代號'].isin(df_stock['證券代號'].unique())]
    print(len(df_stock), len(df_dividend))

    for stock in df_dividend['股票代號'].unique():
        dividend_date_list = df_dividend[df_dividend['股票代號'] == stock]['日期']
        extend_date_list = []
        for date in dividend_date_list:
            input_datetime = datetime.datetime.strptime(date, "%Y%m%d")
            extend_date_list.extend([((input_datetime - datetime.timedelta(days=i))).strftime("%Y%m%d") for i in range(30, 0, -1)])
            extend_date_list.append(date)
            extend_date_list.extend([(input_datetime + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(1, 31)])
        df_stock = df_stock.drop(df_stock[(df_stock['證券代號'] == stock) & ~df_stock['日期'].isin(extend_date_list)].index)
        print(len(df_stock))

    return df_stock, df_dividend
    

def add_days(date, days):
    new_date = datetime.datetime.strptime(date, '%Y%m%d') + datetime.timedelta(days=days)
    return new_date.strftime('%Y%m%d')


def before_dividend_result(df_stock, dividend_date_info):
    dividend_date = dividend_date_info['日期']
    df_sell_day = pd.DataFrame()
    days = -1
    while len(df_sell_day) == 0 or df_sell_day['成交股數'].iloc[0] == 0:
        sell_date = add_days(dividend_date, days)
        if days <= -30:
            break
        df_sell_day = df_stock[(df_stock['證券代號'] == dividend_date_info['股票代號']) & (df_stock['日期'] == sell_date)]
        days -= 1
    if len(df_sell_day) == 0:
        return pd.DataFrame()

    df_sell_day = df_sell_day.iloc[0]
           
    df_buy_day = [pd.DataFrame()]*4 
    for i, days in enumerate([-7, -14, -21, -28]):
        while len(df_buy_day[i]) == 0 or df_buy_day[i]['成交股數'].iloc[0] == 0:
            buy_date = add_days(sell_date, days)
            # 往前找不到每日交易資料, 有可能是新上市不久
            if days <= -60:
                df_buy_day[i] = df_stock[(df_stock['證券代號'] == dividend_date_info['股票代號']) & (df_stock['日期'] == sell_date)]
                break
            df_buy_day[i] = df_stock[(df_stock['證券代號'] == dividend_date_info['股票代號']) & (df_stock['日期'] == buy_date)]
            days -= 1
        if len(df_buy_day[i]) == 0:
            return pd.DataFrame()
        df_buy_day[i] = df_buy_day[i].iloc[0]
    
    new_row = pd.DataFrame([{
        '證券代號': dividend_date_info['股票代號'],
        '除權息日': dividend_date_info['日期'],
        '除權息前賣出日期': sell_date,
        '除權息前賣出價': df_sell_day['開盤價'],
        '除權息前1W買入日期': df_buy_day[0]['日期'], '買入價1W前': df_buy_day[0]['開盤價'], '賺賠1W前': (0.0+df_sell_day['開盤價']-df_buy_day[0]['開盤價'])*10,
        '除權息前2W買入日期': df_buy_day[1]['日期'], '買入價2W前': df_buy_day[1]['開盤價'], '賺賠2W前': (0.0+df_sell_day['開盤價']-df_buy_day[1]['開盤價'])*10,
        '除權息前3W買入日期': df_buy_day[2]['日期'], '買入價3W前': df_buy_day[2]['開盤價'], '賺賠3W前': (0.0+df_sell_day['開盤價']-df_buy_day[2]['開盤價'])*10,
        '除權息前4W買入日期': df_buy_day[3]['日期'], '買入價4W前': df_buy_day[3]['開盤價'], '賺賠4W前': (0.0+df_sell_day['開盤價']-df_buy_day[3]['開盤價'])*10,
    }])
    return new_row


def after_dividend_result(df_stock, dividend_date_info):
    dividend_date = dividend_date_info['日期']
    df_buy_day = pd.DataFrame()
    days = 0
    while len(df_buy_day) == 0 or df_buy_day['成交股數'].iloc[0] == 0:
        buy_date = add_days(dividend_date, days)
        if (datetime.datetime.strptime(buy_date, '%Y%m%d') > datetime.datetime.today()) or (days >= 30):
            break
        df_buy_day = df_stock[(df_stock['證券代號'] == dividend_date_info['股票代號']) & (df_stock['日期'] == buy_date)]
        days += 1
    if len(df_buy_day) == 0:
        return pd.DataFrame()

    df_buy_day = df_buy_day.iloc[0]
    
    df_sell_day = [pd.DataFrame()]*4 
    for i, days in enumerate([7, 14, 21, 28]):
        while len(df_sell_day[i]) == 0 or df_sell_day[i]['成交股數'].iloc[0] == 0:
            sell_date = add_days(buy_date, days)
            # 後續找不到每日交易資料, 也有可能是已經下市了
            if (datetime.datetime.strptime(sell_date, '%Y%m%d') > datetime.datetime.today()) or (days >= 60):
                df_sell_day[i] = df_stock[(df_stock['證券代號'] == dividend_date_info['股票代號']) & (df_stock['日期'] == buy_date)]
                break
            df_sell_day[i] = df_stock[(df_stock['證券代號'] == dividend_date_info['股票代號']) & (df_stock['日期'] == sell_date)]
            days += 1
        if len(df_sell_day[i]) == 0:
            return pd.DataFrame()
        df_sell_day[i] = df_sell_day[i].iloc[0]
    
    new_row = pd.DataFrame([{
        '證券代號': dividend_date_info['股票代號'],
#        '除權息日': dividend_date_info['日期'],
        '除權息後買入日期': buy_date,
        '除權息後買入價': df_buy_day['開盤價'],
        '除權息後1W賣出日期': df_sell_day[0]['日期'], '賣出價1W後': df_sell_day[0]['開盤價'], '賺賠1W後': (0.0+df_sell_day[0]['開盤價']-df_buy_day['開盤價'])*10,
        '除權息後2W賣出日期': df_sell_day[1]['日期'], '賣出價2W後': df_sell_day[1]['開盤價'], '賺賠2W後': (0.0+df_sell_day[1]['開盤價']-df_buy_day['開盤價'])*10,
        '除權息後3W賣出日期': df_sell_day[2]['日期'], '賣出價3W後': df_sell_day[2]['開盤價'], '賺賠3W後': (0.0+df_sell_day[2]['開盤價']-df_buy_day['開盤價'])*10,
        '除權息後4W賣出日期': df_sell_day[3]['日期'], '賣出價4W後': df_sell_day[3]['開盤價'], '賺賠4W後': (0.0+df_sell_day[3]['開盤價']-df_buy_day['開盤價'])*10,
    }])
    return new_row


def strategy(df_stock, df_dividend):
    if os.path.isfile(PICKLE):
        df_result = pd.read_pickle(PICKLE)
    else:
        df_result = pd.DataFrame({'證券代號': [], '除權息日': [], 
                                  '除權息前4W買入日期': [], '買入價4W前': [], '賺賠4W前': [], 
                                  '除權息前3W買入日期': [], '買入價3W前': [], '賺賠3W前': [], 
                                  '除權息前2W買入日期': [], '買入價2W前': [], '賺賠2W前': [], 
                                  '除權息前1W買入日期': [], '買入價1W前': [], '賺賠1W前': [], 
                                  '除權息前賣出日期': [], '除權息前賣出價': [],
                                  '除權息後買入日期': [], '除權息後買入價': [],
                                  '除權息後1W賣出日期': [], '賣出價1W後': [], '賺賠1W後': [], 
                                  '除權息後2W賣出日期': [], '賣出價2W後': [], '賺賠2W後': [], 
                                  '除權息後3W賣出日期': [], '賣出價3W後': [], '賺賠3W後': [], 
                                  '除權息後4W賣出日期': [], '賣出價4W後': [], '賺賠4W後': []})
    
    count = 0
    for index, row in df_dividend.iterrows():
        if index < 9210:
            continue
        print('Index:', index, row)

#        buy_date = row['日期']
#        df_buy_day = pd.DataFrame()
#        days = 0
#        while len(df_buy_day) == 0 or df_buy_day['成交股數'].iloc[0] == 0:
#            buy_date = add_days(buy_date, days)
#            if datetime.datetime.strptime(buy_date, '%Y%m%d') > datetime.datetime.today():
#                break
#            df_buy_day = df_stock[(df_stock['證券代號'] == row['股票代號']) & (df_stock['日期'] == buy_date)]
#            days += 1
#        if len(df_buy_day) == 0:
#            continue
#        df_buy_day = df_buy_day.iloc[0]
#        
#        df_sale_day = [pd.DataFrame()]*4
#        for i, days in enumerate([7, 14, 21, 28]):
#            while len(df_sale_day[i]) == 0 or df_sale_day[i]['成交股數'].iloc[0] == 0:
#                sale_date = add_days(buy_date, days)
#                # 後續找不到每日交易資料, 也有可能是已經下市了
#                if (datetime.datetime.strptime(sale_date, '%Y%m%d') > datetime.datetime.today()) or (days >= 60):
#                    df_sale_day[i] = df_stock[(df_stock['證券代號'] == row['股票代號']) & (df_stock['日期'] == buy_date)]
#                    break
#                df_sale_day[i] = df_stock[(df_stock['證券代號'] == row['股票代號']) & (df_stock['日期'] == sale_date)]
#                days += 1
#            df_sale_day[i] = df_sale_day[i].iloc[0]
#        
#        new_row = pd.DataFrame([{
#            '證券代號': row['股票代號'],
#            '除權息日': row['日期'],
#            '除權息後買入日期': buy_date,
#            '除權息後買入價': df_buy_day['開盤價'],
#            '除權息後1W賣出日期': df_sale_day[0]['日期'], '賣出價1W後': df_sale_day[0]['開盤價'], '賺賠1W後': (0.0+df_sale_day[0]['開盤價']-df_buy_day['開盤價'])*10,
#            '除權息後2W賣出日期': df_sale_day[1]['日期'], '賣出價2W後': df_sale_day[1]['開盤價'], '賺賠2W後': (0.0+df_sale_day[1]['開盤價']-df_buy_day['開盤價'])*10,
#            '除權息後3W賣出日期': df_sale_day[2]['日期'], '賣出價3W後': df_sale_day[2]['開盤價'], '賺賠3W後': (0.0+df_sale_day[2]['開盤價']-df_buy_day['開盤價'])*10,
#            '除權息後4W賣出日期': df_sale_day[3]['日期'], '賣出價4W後': df_sale_day[3]['開盤價'], '賺賠4W後': (0.0+df_sale_day[3]['開盤價']-df_buy_day['開盤價'])*10,
#        }])
#        new_row = pd.concat([before_dividend_result(df_stock, row), after_dividend_result(df_stock, row)])
#        new_row = pd.concat([a_df, b_df])
        before_df = before_dividend_result(df_stock, row)
        after_df = after_dividend_result(df_stock, row)
        if (len(before_df) == 0) or (len(after_df) == 0):
            continue
        new_row = before_df.merge(after_df)
        df_result = pd.concat([df_result, new_row], ignore_index=True)
        count += 1
        if count == 10:
            count = 0
            df_result.drop_duplicates(inplace=True)
            df_result.to_pickle(PICKLE)
            
    df_result.drop_duplicates(inplace=True)
    df_result.to_pickle(PICKLE)
    return df_result


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 1000)

    # 更新除權息資訊
    #df_dividend = get_dividend_info.get_dividend()
    '''df_dividend = pd.read_pickle('dividend_info.pkl')
    print(df_dividend)
    print(df_dividend.info())

    # 更新上市上櫃歷史股價資訊
    df_stock = get_stock_daily_info.get_stock_otc_daily_info()
    print(df_stock)             
    print(df_stock.info())      
        
    # 將申購資訊, 上市上櫃興櫃歷史資訊, 去除大量不需要的部分以加快處理速度
    df_stock, df_dividend = prune_df(df_stock, df_dividend)
    df_stock.to_pickle('stock_daily_info_subset2.pkl')'''
        
    df_stock = pd.read_pickle('stock_daily_info_subset2.pkl')
    df_dividend = pd.read_pickle('dividend_info.pkl')
    df = strategy(df_stock, df_dividend)
    print(df)

#    df_dividend = pd.read_pickle('dividend_info_subset2.pkl')
#    df = pd.read_pickle('dividend_strategy.pkl')
#    df_stock = pd.read_pickle('stock_daily_info_subset2.pkl')

#    for stock in df['證券代號'].unique():
#        df2 = df[df['證券代號'] == stock]
#        print(df2)
#        s = df2['賺賠4'] > 1000
#        if len(s) >= 5 and s[-5:].all():
#            print(df2)
#        df3 = df2[df2['賺賠1'] > 1000]
        

#    for index, row in df_dividend.iterrows():
#        check_date = row['日期']
#        df_check_day = pd.DataFrame()
#        days = 0
#        while len(df_check_day) == 0:
#            days -= 1
#            if days < -10:
#                break
#            check_date = add_days(check_date, days)
#            df_check_day = df_stock[(df_stock['證券代號'] == row['股票代號']) & (df_stock['日期'] == check_date)]
#        if len(df_check_day) == 0:
#            continue
#        df_check_day = df_check_day.iloc[0]
#        if df_check_day['成交金額'] >= 1000000000:
#            result_df = df[(df['購買日期'] == row['日期']) & (df['證券代號'] == row['股票代號'])]
#            if len(result_df) > 0:
#                print(result_df['賺賠1'])
            
#        print(df_check_day)
#        exit(-1)
    
#    print(len(df[df['賺賠1'] > 0]), len(df[df['賺賠1'] < 0]))
#    print(df[df['賺賠1'] > 0]['賺賠1'].mean, df[df['賺賠1'] < 0]['賺賠1'].mean)
#    print(df[df['賺賠1'] > 0], df[df['賺賠1'] < 0])
#    print(len(df[df['賺賠2'] > 0]), len(df[df['賺賠2'] < 0]))
#    print(df[df['賺賠2'] > 0]['賺賠2'].mean, df[df['賺賠2'] < 0]['賺賠2'].mean)
#    print(len(df[df['賺賠3'] > 0]), len(df[df['賺賠3'] < 0]))
#    print(df[df['賺賠3'] > 0]['賺賠3'].mean, df[df['賺賠3'] < 0]['賺賠3'].mean)
#    print(len(df[df['賺賠4'] > 0]), len(df[df['賺賠4'] < 0])) 
#    print(df[df['賺賠4'] > 0]['賺賠4'].mean, df[df['賺賠4'] < 0]['賺賠4'].mean)
