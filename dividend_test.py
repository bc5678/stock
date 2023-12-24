import pandas as pd

df = pd.read_pickle('dividend_strategy.pkl')
print(df)
print(len(df))
print()

# 如果除權息前一段時間, 股價有一定程度的漲或跌, 是否會影響除權息後的漲跌？
for s in ['賺賠4W前', '賺賠3W前', '賺賠2W前', '賺賠1W前']:
    for percent in range(0, 31):
        percent = percent / 100.0
        sub_df = df[df[s]/(df['除權息前賣出價']*10) > percent]
        sub_df = sub_df[sub_df[s]/(sub_df['除權息前賣出價']*10) <= (percent+0.01)]
        print(f'{percent+0.01} >= {s}/除權息前賣出價 > {percent}: {len(sub_df)}')
        for s2 in ['賺賠1W後', '賺賠2W後', '賺賠3W後', '賺賠4W後']:
            win_df = sub_df[sub_df[s2] > 0]
            print(f'{s2} > 0: {len(win_df)} = {len(win_df)/len(sub_df)}%')
            if len(win_df)/len(sub_df) >= 0.8:
                print(win_df)
    for percent in range(0, -31, -1):
        percent = percent / 100.0
        sub_df = df[df[s]/(df['除權息前賣出價']*10) < percent]
        sub_df = sub_df[sub_df[s]/(sub_df['除權息前賣出價']*10) >= (percent-0.01)]
        print(f'{percent} > {s}/除權息前賣出價 >= {percent-0.01}: {len(sub_df)}')
        for s2 in ['賺賠1W後', '賺賠2W後', '賺賠3W後', '賺賠4W後']:
            win_df = sub_df[sub_df[s2] > 0]
            print(f'{s2} > 0: {len(win_df)} = {len(win_df)/len(sub_df)}')
            if len(win_df)/len(sub_df) >= 0.8:
                print(win_df)
        
        
# 如果除權息前一段時間無腦買進, 在除權息前一日賣掉, 或是除權息日買進, 一段時間無腦賣掉, 賺賠如何？
print(len(df))
for s in ['賺賠4W前', '賺賠3W前', '賺賠2W前', '賺賠1W前', '賺賠1W後', '賺賠2W後', '賺賠3W後', '賺賠4W後']:
    w = len(df[df[s] > 0])
    e = len(df[df[s] == 0])
    l = len(df[df[s] < 0])
    print(f"{s} > 0: {w} ({w/len(df):.2f}), {s} = 0: {e} ({e/len(df):.2f}), {s} < 0: {l} ({l/len(df):.2f})")
#for x in [df[df['賺賠4W前'] > 0], df[df['賺賠3W前'] > 0], df[df['賺賠2W前'] > 0], df[df['賺賠1W前'] > 0]]:
#    print(len(x[x['賺賠4W前']/x['除權息前賣出價'] > 0.5]))
    #print(len(x), len(x[x['賺賠1W後'] > 0])/len(x), len(x[x['賺賠2W後'] > 0])/len(x), len(x[x['賺賠3W後'] > 0])/len(x), len(x[x['賺賠4W後'] > 0])/len(x))
#for x in [df[df['賺賠4W前'] < 0], df[df['賺賠3W前'] < 0], df[df['賺賠2W前'] < 0], df[df['賺賠1W前'] < 0]]:
#    print(len(x), len(x[x['賺賠1W後'] > 0])/len(x), len(x[x['賺賠2W後'] > 0])/len(x), len(x[x['賺賠3W後'] > 0])/len(x), len(x[x['賺賠4W後'] > 0])/len(x))
