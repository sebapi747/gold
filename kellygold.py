import pandas as pd
import datetime as dt
import numpy as np
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

def sendTelegram(text):
    telegramchatid = os.environ.get('TELEGRAM_CHAT_ID')
    telegramtoken = os.environ.get('TELEGRAM_TOKEN')
    if not telegramchatid or not telegramtoken:
        logger.error("Telegram credentials not set in environment variables")
        return
    params = {'chat_id': telegramchatid, 'text': text, 'parse_mode': 'markdown'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(telegramtoken), params)
    resp.raise_for_status()
def get_metadata():
    return {'Creator':os.uname()[1] +":"+__file__+":"+str(dt.datetime.utcnow())}
    
def tbillrate():
    df = pd.read_csv("data/TB3MS.csv")
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    df["TB3MS"] /= 100
    return df.set_index("observation_date")
def compute_gold_tr(df):
    for colname in df.columns:
        df[colname+'TR'] = df[colname]/df[colname].shift(1)
    return df
def goldprice():
    col = {"CRUDE_DUBAI":"crude", "GOLD":"gold", "PLATINUM":"platinum","SILVER":"silver","COPPER":"copper","iNATGAS":"natgas"}
    col = {"CRUDE_DUBAI":"crude (no roll)", "GOLD":"gold"}
    df = pd.read_csv("data/cmo-data-monthly.csv")[["date"]+list(col.keys())]
    df["date"] = pd.to_datetime(df["date"])+dt.timedelta(days=1)
    df = df.loc[df["date"]>=dt.datetime(1971,2,1)]
    return compute_gold_tr(df.set_index("date").rename(columns=col))
def read_shiller_out():
    df = pd.read_csv("data/shiller_out.csv")
    df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")+dt.timedelta(days=-14)
    df = df.set_index("Date")
    for c in df.columns:
        df[c] = df[c].astype(float)
    df['Rate10y'] = df['Rate10y']/100
    return df.join(tbillrate()).join(goldprice(),how="inner")

"""
def compute_bond_tr(df):
    r = df['Rate10y']
    T = 10
    duration = -(1-np.exp(-r*T))/r
    bondcarry = r.shift(1)/12
    bondtotalret = 1+(r-r.shift(1))*duration+bondcarry
    df["bondTR"] = bondtotalret
def compute_eq_tr(df):
    df['eqTR'] = df['SP500']/df['SP500'].shift(1)+df['Div']/12/df['SP500']
def compute_cpi_tr(df):
    df['cpiTR'] = 1+df['CPI'].pct_change()
    """
def compute_tbill_tr(df):
    df['tbTR'] = 1+df['TB3MS'].shift(1)*365/360/12


def metrics_monthly_ret(df):
    trcolumns = [c for c in df.columns if "TR"==c[-2:] and c!="cpiTR"]
    logret = np.log(df[trcolumns].dropna())
    mu,sigma = logret.mean()*12,logret.std()*np.sqrt(12)
    sigma["tbTR"] = 0
    mu += 0.5*sigma**2
    riskycol = trcolumns[:-1]
    mustar = np.expm1(mu[riskycol]-mu["tbTR"])
    data = {'mustar':mustar,'sigma':sigma[riskycol]}
    data['sharpe'] = data['mustar']/data['sigma']
    corr = logret[riskycol].corr()
    cov = logret[riskycol].cov()*12
    wstar = np.linalg.solve(cov,mustar)
    data['w'] = wstar/np.sum(wstar)
    for c in riskycol:
        data[f'rho({c[:-2]})'] = corr[c]
    return pd.DataFrame(data,index=riskycol)

filename = "assetreturn.png"
def show_returns(df):
    dfmetrics = metrics_monthly_ret(df)
    for c in dfmetrics.index:
        plt.plot(np.cumprod(df[c]),
                 label=f"{c[:-2]}: $\mu^*$={dfmetrics.loc[c,'mustar']:.1%}, $\sigma$={dfmetrics.loc[c,'sigma']:.0%}, S={dfmetrics.loc[c,'sharpe']:.2f}, w={dfmetrics.loc[c,'w']:.0%}")
    plt.legend()
    plt.title("Asset Total Return")
    plt.ylabel("log total return")
    plt.yscale('log')  
    plt.xlabel(f"from {str(df.index[0])[:10]} to {str(df.index[-1])[:10]}")  
    plt.grid(True)  
    plt.savefig(filename,metadata=get_metadata())
    plt.close()
    
if __name__ == "__main__":
    df = read_shiller_out()
    compute_tbill_tr(df)
    show_returns(df.loc[df.index>=dt.datetime(1960,1,1)])
    cmd = f"rsync -avz {filename} {os.environ.get('REMOTEDIR')}/{filename}"
    print(cmd)
    os.system(cmd)
