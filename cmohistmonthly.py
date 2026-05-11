import os, requests, re
import pandas as pd
import datetime as dt
import time
import matplotlib.pyplot as plt
from dotenv import load_dotenv

def sendTelegram(text):
    telegramchatid = os.environ.get('TELEGRAM_CHAT_ID')
    telegramtoken = os.environ.get('TELEGRAM_TOKEN')
    if not telegramchatid or not telegramtoken:
        logger.error("Telegram credentials not set in environment variables")
        return
    params = {'chat_id': telegramchatid, 'text': text, 'parse_mode': 'markdown'}
    resp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(telegramtoken), params)
    resp.raise_for_status()
    
def get_cmo_monthly():
    fileout = "data/cmo-data-monthly.csv"
    if os.path.exists(fileout) and time.time() - os.path.getmtime(fileout) < 14*86400:
        print("INFO: File is less than 2 weeks old → skipping")
        return
    response = requests.get("https://www.worldbank.org/en/research/commodity-markets", timeout=30)
    response.raise_for_status()
    match = re.search(r'href=([^ ]*?.xlsx)', response.text)
    url = match.group(1)
    url = url.strip('"')
    
    basename = os.path.basename(url)
    headers = {'accept':'*/*', 'user-agent': 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Raspbian Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36'}
    print("INFO: getting remote xls file")
    resp = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(basename, 'wb') as fd:
        fd.write(resp.content)
        
    csvout = basename.replace(".xlsx",".csv")
    cmd  = f'ssconvert --export-type=Gnumeric_stf:stf_csv {basename} {csvout}'
    print(cmd)
    os.system(cmd)
    
    #df = pd.read_csv(csvout, skiprows=5, header=[0, 1], na_values=['…'])
    #df.columns = df.columns.droplevel(1)
    #df = df.rename(columns={'Unnamed: 0_level_0':'date'})
    df = pd.read_csv(csvout, skiprows=6, na_values=['…'])
    df = df.rename(columns={'Unnamed: 0':'date'})
    # Convert directly with string manipulation
    df['date'] = pd.to_datetime(df['date'].str.replace('M', '-') + '-01') + pd.offsets.MonthEnd(0)
    df.to_csv(fileout,index=False)
    print(f"output {len(df)} lines to {fileout}")
    sendTelegram(f"output {len(df)} lines to {fileout}")

def copy_themis_data():
    sshpath = os.environ.get('THEMISSSH')
    cmd = f"rsync -avz {sshpath}/stlouis/data/TB3MS.csv data/TB3MS.csv"
    os.system(cmd)
    cmd = f"rsync -avz {sshpath}/shiller/data/shiller.csv data/shiller.csv"
    os.system(cmd)
    
if __name__ == "__main__":
    load_dotenv()
    try:
       get_cmo_monthly()
       copy_themis_data()
    except Exception as e:
       sendTelegram(str(e))
