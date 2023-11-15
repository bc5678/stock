import pandas as pd
import requests
import io


url = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=20220412&type=ALLBUT0999&_=1649743235999'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/111.25 (KHTML, like Gecko) Chrome/99.0.2345.81 Safari/123.36'}

res = requests.get(url,headers=headers)

lines = [l for l in res.text.split('\n') if len(l.split(',"'))>=10]
df = pd.read_csv(io.StringIO(','.join(lines)))
df = df.applymap(lambda s:(str(s).replace('=','').replace(',','').replace('"',''))).set_index('證券代號')
df = df.applymap(lambda s:pd.to_numeric(str(s),errors='coerce')).dropna(how='all',axis=1)
