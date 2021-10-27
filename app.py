import sys
import io
import random
import logging
from flask import Flask, flash, Response, redirect, request, render_template, url_for
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

import pandas as pd
import numpy as np
# from pandas_datareader import data as web
import yfinance
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import mplfinance as mpf

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
RISK_SCATTER_TICKERS = ['BTC-USD', 'SPY']
END=dt.datetime.today()+ dt.timedelta(days=1)
START=END - dt.timedelta(days=730)


@app.route("/",methods=["POST","GET"])
def index():
    # ticker = str(request.args.get("ticker", 'GLP'))
    ticker='BTC-USD'
    default_indicators = 'risk riskscatter'
    if(request.method == "POST"):
        
        # form_name = request.form['form-name']
        if('download_tickers' in request.form):
            download_tickers = request.form['download_tickers']
            download_multiple_stocks(download_tickers)
            ticker=download_tickers.split(' ')[0]
        elif('ticker' in request.form):
            new_tick = request.form['ticker']
            new_tick = new_tick.replace('-','.') # yahoo uses '-' in crypto tickers (BTC-USD) which interferes with the retrieving of variables from the url
            new_tick = new_tick.replace('/','')
            save_to_csv_yahoo(ticker)
            new_start = request.form['start']
            new_start = new_start.replace('-','.') # same thing with dates, so I replaced them with '.'
            new_end = request.form['end']
            new_end = new_end.replace('-','.')
            new_start_dt = dt.datetime.today() - dt.timedelta(days=365) # Maybe a slightly wasetful way to handle no
            if(new_start != ''):                                        # entry, but oh well
                new_start_dt = dt.datetime.strptime(new_start, "%Y.%m.%d").date()
                global START
                START = new_start_dt
            new_end_dt = dt.datetime.today() + dt.timedelta(days=1) # Because crypto uses UTC time, sometimes
            if(new_end != ''):                                      # Your local day will be a day behind,
                new_end_dt = dt.datetime.strptime(new_end, "%Y.%m.%d").date() # Causing the latest daily candle
                global END                                          # not to appear
                END = new_end_dt
            
            new_indicators = request.form['indicators']
            new_indicators = new_indicators.replace(',','')
            if(new_indicators == ''):
                new_indicators = 'none'
            # return redirect("/mplfinance2-{new_tick}-{new_start}-{new_end}-{new_indicators}.png")
            # return redirect(url_for('plot_finance2',ticker=new_tick, start=new_start, end=new_end, indicators=new_indicators))
            return render_template("app.html", ticker=new_tick, sday=new_start_dt.day, smonth=new_start_dt.month,
                                    syear=new_start_dt.year, eday=new_end_dt.day, emonth=new_end_dt.month, 
                                    eyear=new_end_dt.year, indicators=new_indicators)

        # print('\n\n\n\n\n' + str(download_tickers) + '\n\n\n\n', file=sys.stderr)
    return render_template("app.html", ticker=ticker, sday=START.day, smonth=START.month,
                                    syear=START.year, eday=END.day, emonth=END.month, 
                                    eyear=END.year, indicators=default_indicators)

@app.route("/options", methods=["POST", "GET"])
def options(): # This page doesn't do much, I kind of switched focus when I realized that yfinance
    ticker = yfinance.Ticker('MSFT') # doesn't provide historical options pricing
    optchain = ticker.option_chain(ticker.options[0])
    return render_template("options.html", options=ticker.options, optchain=optchain[1]['contractSymbol'])

@app.route("/matplot-as-image-<int:num_x_points>.png")
def plot_png(num_x_points=50):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(num_x_points)
    axis.plot(x_points, [random.randint(1, 30) for x in x_points])

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


@app.route("/matplot-as-image-<int:num_x_points>.svg")
def plot_svg(num_x_points=50):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(num_x_points)
    axis.plot(x_points, [random.randint(1, 30) for x in x_points])

    output = io.BytesIO()
    FigureCanvasSVG(fig).print_svg(output)
    return Response(output.getvalue(), mimetype="image/svg+xml")

@app.route("/mplfinance-<string:ticker>-<int:syear>.png", methods=["POST","GET"]) # No longer used
def plot_finance(ticker='AAPL', syear=2010):
    output = io.BytesIO()
    
        
    # indicators = ['risk','riskscatter'] 
    indicators = [ 'risk','riskscatter', 'sma'] #'riskdif']
    # indicators = ['risk','riskscatter', 'sma', 'ext', 'hull'] 
    output = mplfinance_plot(data, ticker, indicators, 'candlestick', syear, 1, 1, 2021, 10, 22)
    return Response(output.getvalue(), mimetype="image/png")

@app.route("/mplfinance2-<string:ticker>-<start>-<end>-<indicators>.png", methods=["POST","GET"])
def plot_finance2(ticker, start, end, indicators):
    data = get_df_from_csv(ticker)
    output = io.BytesIO()
    ticker = ticker.replace('.','-')
    data = get_df_from_csv(ticker)
    indicators = indicators.split(' ')
    start = dt.datetime.strptime(start, "%Y.%m.%d").date()
    end = dt.datetime.strptime(end, "%Y.%m.%d").date()
    # indicators = ['risk','riskscatter'] 
    # indicators = [ 'risk','riskscatter', 'sma'] #'riskdif']
    # indicators = ['risk','riskscatter', 'sma', 'ext'] 
    output = mplfinance_plot(data, ticker, indicators, 'candlestick', start.year, start.month, start.day, end.year, end.month, end.day)
    print('\n\n\n\n\n' + str(ticker) + '\n' + str(start) + '\n' + str(end) + '\n' + str(indicators) + '\n\n\n\n\n',file=sys.stderr)
    return Response(output.getvalue(), mimetype="image/png")

def get_df_from_csv(ticker):
    try:
        df = pd.read_csv('./data/' + ticker + '.csv')
    except FileNotFoundError:
        print('File does not exist')
    else:
        df = df.dropna(subset=['Adj Close'])
        return df

def save_to_csv_yahoo(ticker):
    # df = web.DataReader(ticker.strip(), 'yahoo', start, end)
    df = yfinance.download(ticker.strip(), period="MAX")
    df.to_csv('./data/' + ticker + ".csv")
    return df

def normalize(data):
    max_value = data.max()
    min_value = data.min()
    # data = (data - min_value) / (max_value - min_value)
    if(min_value > 0):
        data = ((data - min_value) / (max_value - min_value))
    elif(min_value < 0):
        data = ((data + min_value) / (max_value - min_value))
    else:
        data = (data / max_value)
    return data

def WMA(s, period):
       return s.rolling(period).apply(lambda x: ((np.arange(period)+1)*x).sum()/(np.arange(period)+1).sum(), raw=True)

def HMA(s, period):
       return WMA(WMA(s, period//2).multiply(2).sub(WMA(s, period)), int(np.sqrt(period)))

def SMA(s, period): # This causes errors for some reason
    return s.rolling(window=140, min_periods=1).mean()

def define_hull(df):
    df['hma9'] = HMA(df['Close'],9)
    df['hma140'] = HMA(df['Close'],140)
    df['hma200'] = HMA(df['Close'],200)
    df['hma500'] = HMA(df['Close'],500)

    return df

def define_risk(df):
    ma50 = 0 # To calculate 'risk'
    df['sma50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    df['sma350'] = df['Close'].rolling(window=350, min_periods=1).mean()
    df['risk'] = df['sma50']/df['sma350'] # 'risk' 
    df['risk'] = normalize(df['risk'])

    df['hma50'] = HMA(df['Close'],50)
    df['hma350'] = HMA(df['Close'],350)
    df['hrisk'] = df['hma50']/df['sma350']
    df['hrisk'] = normalize(df['hrisk'])
    return df

def define_risk_dif(df): # Is this a measure of momentum?
    df['riskdif'] = df['risk'] - df['hrisk']
    df['0'] = (df['riskdif'] * 0)
    df['difcrossover'] = np.where((df['riskdif'] > 0) & (df['riskdif'].shift(1) <= 0), df['Close'] * 1, np.nan)
    df['difcrossunder'] = np.where((df['riskdif'] < 0) & (df['riskdif'].shift(1) >= 0), df['Close'] * 1, np.nan)
    return df

def define_risk_scatter(df,ticker):
    if(ticker == 'SPY'):
        bbound1 = 0.7
        bbound2 = 0.6
        sbound1 = 0.8
        sbound2 = 0.91
        hbbound1 = 0.5
        hsbound1 = 0.9
    elif(ticker == 'BTC-USD'):
        bbound1 = 0.35
        bbound2 = 0.24
        sbound1 = 0.75
        sbound2 = 0.8

        hbbound1 = 0.2
        hsbound1 = 0.6
    else:
        bbound1 = 0.4
        bbound2 = 0.3
        sbound1 = 0.90
        sbound2 = 0.8
        hbbound1 = 0.3
        hsbound1 = 0.85
    df['BuySignal1'] = np.where(df['risk'] < bbound1, df['Close'] * 1, np.nan)
    df['BuySignal2'] = np.where(df['risk'] < bbound2, df['Close'] * 1, np.nan)
    df['SellSignal1'] = np.where(df['risk'] > sbound1, df['Close'] * 1, np.nan)
    df['SellSignal2'] = np.where(df['risk'] > sbound2, df['Close'] * 1, np.nan)

    df['HBuySignal1'] = np.where(df['hrisk'] < hbbound1, df['Close'] * 1, np.nan)
    df['HSellSignal1'] = np.where(df['hrisk'] > hsbound1, df['Close'] * 1, np.nan)
    return df

def define_sma(df):
    df['sma20'] = df['Close'].rolling(window=20, min_periods=1).mean()
    df['sma140'] = df['Close'].rolling(window=140, min_periods=1).mean()
    df['sma200'] = df['Close'].rolling(window=200, min_periods=1).mean()
    return df

def define_ma_ext(df):
    df['sma140'] = SMA(df['Close'], 140)
    df['ext'] = ((df['Close'] - df['sma140']) / df['sma140']) * 100
    df['E0'] = (df['Close'] * 0)
    df['ext'] = normalize(df['ext'])
    return df

def plot_indicator(df,index):   # Not really sure if this works, I haven't used it for a long time. Maybe the matlibplot SVG chart would be better for standalone indicators anyways? Or a second panel?
    df.index = pd.DatetimeIndex(df['Date'])
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 8})
    fig = mpf.figure(figsize=(12, 8),style=s)
    ax = fig.add_subplot(2,1,1)
    ax.set_title(index)
    buf=io.BytesIO()
    mpf.plot(df, type='line', ax=ax, show_nontrading=True,savefig=buf)
    return buf

def download_multiple_stocks(tickers):
    tickers = tickers.split(' ')
    if(len(tickers) == 1):
        save_to_csv_yahoo(tickers[0])
    for x in tickers:
        save_to_csv_yahoo(x)

def intersection(lst1, lst2): # Returns the intersection of two lists
    return list(set(lst1) & set(lst2))
        
def define_indicators(_ticker, _df, _indicators):
    reqSMA = ['sma', 'ext', 'risk', 'riskscatter', 'riskdif'] # SMA (simple moving average)
    if(len(intersection(reqSMA, _indicators)) > 0): # Check to see if the two lists have any shared members
        _df = define_sma(_df)
    reqHULL = ['hull', 'risk', 'riskscatter', 'riskdif']
    if(len(intersection(reqHULL, _indicators)) > 0):
        _df = define_hull(_df)
    reqEXT = ['ext']
    if(len(intersection(reqEXT, _indicators)) > 0):
        _df = define_ma_ext(_df)
    reqRISK = ['risk', 'riskscatter', 'riskdif'] # risk - plots two lines each derrived from the quotient of (short term MA / long term MA)
    if(len(intersection(reqRISK, _indicators)) > 0): # The quoteients are normalized to a scale of 0-1, low values represent low instantaneous risk
        _df = define_risk(_df)
        if(('riskscatter' in _indicators)):
            _df = define_risk_scatter(_df, _ticker)
        if('riskdif' in _indicators):
            _df = define_risk_dif(_df)
    return _df
        
def add_indicators(_ticker, _df,_indicators):
    panels = 1
    _adps = [] # Indicators: risk riskscatter riskdif sma ext hull
               # Eventually I should make them customizable, ie sma:9, hull:500 riskscatter:.2,.9
    if('sma' in _indicators): # Check to see if reqSMA (str list) and _indicators (string) have any shared members
        _adps.append(mpf.make_addplot(_df['sma20']))
        _adps.append(mpf.make_addplot(_df['sma140']))
        _adps.append(mpf.make_addplot(_df['sma200']))
    if('hull' in _indicators):
        _df = define_hull(_df)
        # _adps.append(mpf.make_addplot(_df['hma9'],color='#adff2f'))
        _adps.append(mpf.make_addplot(_df['hma140'],color='#adff2f'))
        _adps.append(mpf.make_addplot(_df['hma200'],color='#adff2f'))
        # _adps.append(mpf.make_addplot(_df['hma500'],color='#adff2f')) For some reason, HMA() only uses df_sub. I think it has something to do with
    if('ext' in _indicators):                                                                                                       #df[].rolling()
        _adps.append(mpf.make_addplot(_df['ext'],color='#adff2f', panel=panels))
        # _adps.append(mpf.make_addplot(_df['E0'], panel=panels))
        # _adps.append(mpf.make_addplot(_df['0'], color='#0000ff',panel=panels))
        panels = panels + 1
    if('risk' in _indicators):
        _adps.append(mpf.make_addplot(_df['risk'], color='#ff5500', panel=panels)) # while high values represent high instantaneous risk. The
        _adps.append(mpf.make_addplot(_df['hrisk'], color='#adff2f',panel=panels)) # directionality of the risk plot (its derivative) is likewise
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.1, color='#0000ff', panel=panels))
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.2, color='#003cff', panel=panels))
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.3, color='#0078ff', panel=panels))
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.4, color='#009dff', panel=panels))
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.5, color='#00c5ff', panel=panels)) # These are just horizontal lines to both ensure that
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.6, color='#00ee83', panel=panels)) # at least the range of 0.1-0.9 is visible on the second
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.7, color='#00f560', panel=panels)) # panel and to be used as reference for the eye 
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.8, color='#a2ff00', panel=panels))
        _adps.append(mpf.make_addplot((_df['risk'] * 0) + 0.9, color='#ff0000', panel=panels))
        panels = panels + 1
    if(('riskscatter' in _indicators)): # Buy/Sell scatter plot
        # SMA calculated risk signals
        # _adps.append(mpf.make_addplot(_df['BuySignal1'] * 0.96,type="scatter", color=['#00aa00']))
        # _adps.append(mpf.make_addplot(_df['BuySignal2'] * 0.96,type="scatter", color=['#005500']))
        # _adps.append(mpf.make_addplot(_df['SellSignal1'] * 1.04,type="scatter", color=['#ff0000']))
        # _adps.append(mpf.make_addplot(_df['SellSignal2'] * 1.04,type="scatter", color=['#8a0000']))
        # HMA calculated risk signals
        if(_df['HBuySignal1'].isnull().all() == False):
            _adps.append(mpf.make_addplot(_df['HBuySignal1'] * 0.96,type="scatter", color=['#00aa00']))
        if(_df['HSellSignal1'].isnull().all() == False):
            _adps.append(mpf.make_addplot(_df['HSellSignal1'] * 1.04,type="scatter", color=['#ff0000']))
    if('riskdif' in _indicators):
        _adps.append(mpf.make_addplot(_df['riskdif'], color='#febf01',panel=panels)) # Riskdif plots a point whenver the two different risk 
        if(_df['difcrossover'].isnull().all() == False):
            _adps.append(mpf.make_addplot(_df['difcrossover'],type="scatter", color=['#febf01'])) # measurments cross (on their individually
            _adps.append(mpf.make_addplot(_df['0'], panel=panels))
        if(_df['difcrossunder'].isnull().all() == False):
            _adps.append(mpf.make_addplot(_df['difcrossunder'],type="scatter", color=['#adff2f'])) # normalized scales)
        panels = panels + 1
    
    return _adps

def mplfinance_plot(df, ticker, indicators, chart_type, syear, smonth, sday, eyear, emonth, eday):
    start = f"{syear}-{smonth}-{sday}"
    end = f"{eyear}-{emonth}-{eday}"
    df.index = pd.DatetimeIndex(df['Date'])
    # if(('riskscatter' in indicators) and (ticker not in RISK_SCATTER_TICKERS)):
    #     indicators.remove('riskscatter')
    df = define_indicators(ticker, df, indicators)
    df_sub = df.loc[start:end]
    s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 16, 'text.color': '#c4d0ff',
                            'axes.labelcolor':'#c4d0ff', 'xtick.color':'#c4d0ff', 'ytick.color':'#c4d0ff'},
                            facecolor="#434345", edgecolor="#000000", figcolor="#292929", y_on_right=False) 
    fig = mpf.figure(figsize=(12, 8), style=s)
    title = ticker
    adps = add_indicators(ticker, df_sub, indicators)
    buf = io.BytesIO()
    if('line' in indicators):
        chart_type = 'line'
    if('renko' in indicators):
        chart_type = 'renko' # doesn't work when addplot is set in mpf.plot()
        adps=False # maybe?
    # hlines = dict(hlines=[0.2,0.8], colors=['g','r'], linestyle='-.') # Only works on primary y axis
    mpf.plot(df_sub, type=chart_type, title=title, tight_layout=True, addplot=adps,
              volume=False, figscale=3, show_nontrading=True, style=s, 
              savefig=buf)#panel_ratios=(3,1),hlines=hlines,mav=(50,350))
    return buf

if __name__ == "__main__":
    # import webbrowser
    # webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True, host='0.0.0.0')
    app.debug = True
    app.secret_key = 'WX78654H'