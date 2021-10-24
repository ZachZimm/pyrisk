import sys
import io
import random
import logging
from flask import Flask, flash, Response, redirect, request, render_template, request, url_for
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
risk_scatter_tickers = ['BTC-USD', 'SPY']


@app.route("/",methods=["POST","GET"])
def index():
    """ Returns html with the img tag for your plot.
    """
    num_x_points = int(request.args.get("num_x_points", 50))
    ticker = str(request.args.get("ticker", 'GLP'))
    tickers = str(request.args.get("tickers", 'MSFT'))
    ticker2='SPY'
    # print('This is standard output', file=sys.stderr)
    if(request.method == "POST"):
        tickers = request.form['ts']
        download_multiple_stocks(tickers)
        ticker2 = tickers.split(' ')[0]
        return plot_finance(ticker2, 2015)
        print('\n\n\n\n\n' + str(tickers) + '\n\n\n\n', file=sys.stderr)
    else:
        print('\n\n\n\n\n' + 'No Tickers' + '\n\n\n\n', file=sys.stderr)
    return render_template("app.html", num_x_points=num_x_points, ticker='BTC-USD', syear=2017,
                                        ticker2=ticker2, syear2=2006)

@app.route("/options", methods=["POST", "GET"])
def options():
    ticker = yfinance.Ticker('MSFT')
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

@app.route("/mplfinance-<string:ticker>-<int:syear>.png", methods=["POST","GET"])
def plot_finance(ticker='AAPL', syear=2010):
    output = io.BytesIO()
    data = get_df_from_csv(ticker)
    # indicators = ['risk','riskscatter'] 
    indicators = [ 'risk','riskscatter', 'sma'] #'riskdif']
    # indicators = ['risk','riskscatter', 'sma', 'ext'] 
    output = mplfinance_plot(data, ticker, indicators, 'candlestick', syear, 1, 1, 2021, 10, 22)
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

    return df

def define_risk(df):
    ma50 = 0 # To calculate 'Risk'
    df['sma50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    df['sma350'] = df['Close'].rolling(window=350, min_periods=1).mean()
    df['Risk'] = df['sma50']/df['sma350'] # 'Risk' 
    df['Risk'] = normalize(df['Risk'])

    df['hma50'] = HMA(df['Close'],50)
    df['hma350'] = HMA(df['Close'],350)
    df['hRisk'] = df['hma50']/df['sma350'] # 'Risk'   Mixing HMA with SMA is likely to cause errors as things are currently set up
    df['hRisk'] = normalize(df['hRisk'])
    df['riskdif'] = df['Risk'] - df['hRisk']
    df['0'] = (df['Risk'] * 0)
    
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

    df['BuySignal1'] = np.where(df['Risk'] < bbound1, df['Close'] * 1, np.nan)
    df['BuySignal2'] = np.where(df['Risk'] < bbound2, df['Close'] * 1, np.nan)
    df['SellSignal1'] = np.where(df['Risk'] > sbound1, df['Close'] * 1, np.nan)
    df['SellSignal2'] = np.where(df['Risk'] > sbound2, df['Close'] * 1, np.nan)

    df['HBuySignal1'] = np.where(df['hRisk'] < hbbound1, df['Close'] * 1, np.nan)
    df['HSellSignal1'] = np.where(df['hRisk'] > hsbound1, df['Close'] * 1, np.nan)
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

def mplfinance_plot(df, ticker, indicators, chart_type, syear, smonth, sday, eyear, emonth, eday):
    start = f"{syear}-{smonth}-{sday}"
    end = f"{eyear}-{emonth}-{eday}"
    df.index = pd.DatetimeIndex(df['Date'])
    if('risk' in indicators): # This section is kind of a mess. And it would be better if I only had one if/else block,
        df = define_risk(df)  # but I would rather have data calculated for all dates than do df_sub before this block
        if(('riskscatter' in indicators) and (ticker in risk_scatter_tickers)):
            df = define_risk_scatter(df, ticker)
    if('sma' in indicators):
        df = define_sma(df)
    if(('hull' in indicators) or ('hrisk' in indicators)):
        df = define_hull(df)
    if('ext' in indicators):
        df = define_ma_ext(df)
    
    df_sub = df.loc[start:end]
    
    s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 24, 'text.color': '#c4d0ff',
                            'axes.labelcolor':'#c4d0ff', 'xtick.color':'#c4d0ff', 'ytick.color':'#c4d0ff'},
                            facecolor="#434345", edgecolor="#000000", figcolor="#292929", y_on_right=False) 
    fig = mpf.figure(figsize=(12, 8), style=s)
    adps = []
    title = ticker
    if('risk' in indicators):
        adps.append(mpf.make_addplot(df_sub['Risk'], color='#ff5500', panel=1))#, secondary_y=True)) # Risk line plot and reference lines
        adps.append(mpf.make_addplot(df_sub['hRisk'], color='#adff2f',panel=1))
        if('riskdif' in indicators):
            adps.append(mpf.make_addplot(df_sub['riskdif'], color='#febf01',panel=2))
            adps.append(mpf.make_addplot(df_sub['difcrossover'],type="scatter", color=['#febf01']))
            adps.append(mpf.make_addplot(df_sub['difcrossunder'],type="scatter", color=['#adff2f']))
        # adps.append(mpf.make_addplot(df_sub['0'], color='#0000ff',panel=2)) # Creates a secondary axis for some reason?
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.1, color='#0000ff', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.2, color='#003cff', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.3, color='#0078ff', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.4, color='#009dff', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.5, color='#00c5ff', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.6, color='#00ee83', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.7, color='#00f560', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.8, color='#a2ff00', panel=1))# secondary_y=True,))
        adps.append(mpf.make_addplot((df_sub['Risk'] * 0) + 0.9, color='#ff0000', panel=1))# secondary_y=True,))
    if(('risk' in indicators) and ('riskscatter' in indicators) and (ticker in risk_scatter_tickers)): # Buy/Sell scatter plot
        # adps.append(mpf.make_addplot(df_sub['BuySignal1'],type="scatter", color=['#00aa00']))
        # adps.append(mpf.make_addplot(df_sub['BuySignal2'],type="scatter", color=['#005500']))
        # adps.append(mpf.make_addplot(df_sub['SellSignal1'],type="scatter", color=['#ff0000']))
        # adps.append(mpf.make_addplot(df_sub['SellSignal2'],type="scatter", color=['#8a0000']))

        adps.append(mpf.make_addplot(df_sub['HBuySignal1'],type="scatter", color=['#00aa00']))
        adps.append(mpf.make_addplot(df_sub['HSellSignal1'],type="scatter", color=['#ff0000']))
        
    if('sma' in indicators): # Just some SMA lines
        adps.append(mpf.make_addplot(df_sub['sma20']))
        adps.append(mpf.make_addplot(df_sub['sma140']))
        adps.append(mpf.make_addplot(df_sub['sma200']))
    if('hull' in indicators):
        # adps.append(mpf.make_addplot(df_sub['hma9'],color='#adff2f'))
        adps.append(mpf.make_addplot(df_sub['hma140'],color='#adff2f'))
        adps.append(mpf.make_addplot(df_sub['hma200'],color='#adff2f'))
    if(('ext' in indicators) and ('sma' in indicators)):
        adps.append(mpf.make_addplot(df_sub['ext'], panel=2))
        adps.append(mpf.make_addplot(df_sub['E0'], panel=2))
    buf = io.BytesIO()
    # hlines = dict(hlines=[0.2,0.8], colors=['g','r'], linestyle='-.') # Only works on primary y axis
    mpf.plot(df_sub, type=chart_type, title=title, tight_layout=True, addplot=adps,
              volume=False, figscale=3, show_nontrading=True, style=s, 
              savefig=buf)#panel_ratios=(3,1),hlines=hlines,mav=(50,350))
    return buf

if __name__ == "__main__":
    import webbrowser

    # webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True, host='0.0.0.0')
    app.debug = True
    app.secret_key = 'WX78654H'