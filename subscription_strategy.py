
import new_stock_subscription
import get_stock_daily_info


def strategy1(df_subscription, df_stock):
    # 如果每檔都買, 以撥券日的開盤價賣出, 預期獲益為何
    df = df_subscription[df_subscription['證券代號'].isin(df_stock['證券代號'])]
    df = df[df['中籤率(%)'] > 0]
    df = df[df['證券代號'].str.endswith('A') == False]
    df = df[df['證券代號'].str.endswith('B') == False]

    df = df[df['抽籤日期'].str.startswith('2023')]

    print(df)
#    for i in range(len(df)):
#        print(df.loc[i, '撥券日期(上市、上櫃日期)'])
    for index, row in df.iterrows():
        x = stock_info_df[(stock_info_df['日期'] == row['撥券日期(上市、上櫃日期)']) & ( stock_info_df['證券代號'] == row['證券代號'])]

        buy_price = row.loc['承銷價(元)']
        try:
            sell_price = x['開盤價'].iloc[0]
        except:
            if row['撥券日期(上市、上櫃日期)'] == '20130821':
                continue
            if row['撥券日期(上市、上櫃日期)'] == '20140723':
                continue
            if row['撥券日期(上市、上櫃日期)'] == '20160928':
                continue
            if row['撥券日期(上市、上櫃日期)'] == '20160927':
                continue
            if row['證券代號'] == '4413':
                continue
            if row['撥券日期(上市、上櫃日期)'] == '20231129':
                continue
            print(row)
            print(x)
            exit(-1)
        amount = row['申購股數']
        print(f"[{row['證券代號']}] {row['抽籤日期']} {sell_price*amount/100}-{buy_price*amount/100}-70 => {(sell_price-buy_price)/100*amount-70}")


if __name__ == '__main__':
    new_stock_subscription_df = new_stock_subscription.get_new_stock_subscription_info()
    print(new_stock_subscription_df)
    print(new_stock_subscription_df.info())

    stock_info_df = get_stock_daily_info.get_stock_otc_daily_info()
    print(stock_info_df)
    print(stock_info_df.info())
#    print(df_all)
    strategy1(new_stock_subscription_df, stock_info_df)
