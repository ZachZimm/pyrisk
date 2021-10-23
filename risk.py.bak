from __future__ import print_function
import os.path
import datetime
import json
import time
import gspread
import sys
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def main():
    online = 0
    offline = 0
    runs = 1
    if(len(sys.argv) > 1):
        runs = int(sys.argv[1])
    # useOldData()
    try:
        doc_id = loadDocConfig('doc_configuration.json')
    except:
        print('Failed to load document id from \'doc_configuration.json\'')
    for x in range(runs):
        # try:
        btc, eth = update(doc_id)
            # try:
        print('-------------')
        online += 1
        writeData(btc, eth)
        displayData(btc, eth, online, offline)
        if((len(sys.argv) > 1) & (x != runs)):
            time.sleep(3)
            # except:
    print('Error: failed to write data to \'lastdata.json\'')
        # except:
    print('Error: Failed to fetch from Google Sheets')
    print('-------------')
    # Everything below was indented 2 further
    try:
        print('-------------')
        offline += 1
        btc, eth = useOldData()
        displayData(btc, eth, online, offline)
        if((len(sys.argv) > 1) & (x != runs)):
            time.sleep(5)
    except:
        print('Error: Failed to use old data')
        if((len(sys.argv) > 1) & (x != runs)):
            time.sleep(5)

def displayData(btc, eth, online, offline): 
    print(btc['symbol'] + ': ' + btc["price"] + '\t' + btc["risk"] + '\t :\t1h: ' + btc["change"][0] + ' \t24h: ' + btc["change"][1] + ' \t1w: ' + btc["change"][2])
    print(eth['symbol'] + ': ' + eth["price"] + '\t' + eth["risk"] + '\t :\t1h: ' + eth["change"][0] + ' \t24h: ' + eth["change"][1] + ' \t1w: ' + eth["change"][2])
    print('-------------',online,':',offline)

def writeData(btc, eth):
    with open(r"lastdata.json", "w") as extfile:
        extfile.truncate()
        json.dump(btc, extfile, indent=4)
        json.dump(eth, extfile, indent=4)
        extfile.close()

def useOldData():
    print("Note: Using old data, may not be up to date")
    mtime = os.path.getmtime("lastdata.json")
    now = datetime.now()
    timediff = now - datetime.fromtimestamp(mtime)
    print('Last updated ', str(timediff), ' ago')
    with open(r"lastdata.json", "r") as fo:
        fileStr = fo.read()
    delim = fileStr.find('}{') + 1
    ethStr = fileStr[delim:]
    btcStr = fileStr[0:delim]
    btc = json.loads(btcStr)
    eth = json.loads(ethStr)
    return btc, eth

def update(doc_id):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(doc_id).sheet1
    data = sheet.get_all_records()  # Get a list of all records

    btcchange = sheet.cell(6,8).value, sheet.cell(6,9).value, sheet.cell(6,10).value
    ethchange = sheet.cell(7,8).value, sheet.cell(7,9).value, sheet.cell(7,10).value
    # print(data.cell(6,8).value)
    btc = {
        "symbol": 'BTC',
        "price": sheet.cell(6,2).value,
        "risk": sheet.cell(6,4).value,
        "change": btcchange
    }
    eth = {
        "symbol": 'ETH',
        "price": sheet.cell(7,2).value,
        "risk": sheet.cell(7,4).value,
        "change": ethchange
    }
    tupl = btc, eth
    return tupl

def loadDocConfig(path):
    with open(path, "r") as fi:
        doc_config = json.load(fi)
        return doc_config

if __name__ == '__main__':
    main()