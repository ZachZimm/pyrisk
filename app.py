""" Shows how to use flask and matplotlib together.
Shows SVG, and png.
The SVG is easier to style with CSS, and hook JS events to in browser.
python3 -m venv venv
. ./venv/bin/activate
pip install flask matplotlib
python flask_matplotlib.py
"""
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
from pandas_datareader import data as web
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
    # print('This is standard output', file=sys.stderr)
    if(request.method == "POST"):
        tickers = request.form['ts']
        download_multiple_stocks(tickers)
        # save_to_csv_yahoo(tickers, 1999, 1, 1, 2021, 10, 22)
        print('\n\n\n\n\n' + str(tickers) + '\n\n\n\n', file=sys.stderr)
    else:
        print('\n\n\n\n\n' + 'No Tickers' + '\n\n\n\n', file=sys.stderr)
    return render_template("app.html", num_x_points=num_x_points, ticker='BTC-USD', syear=2017,
                                        ticker2='SPY', syear2=2006)

@app.route("/options", methods=["POST", "GET"])
def options():
    ticker = yfinance.Ticker('MSFT')
    optchain = ticker.option_chain(ticker.options[0])
    return render_template("options.html", options=ticker.options, optchain=optchain[1]['contractSymbol'])

@app.route("/matplot-as-image-<int:num_x_points>.png")
def plot_png(num_x_points=50):
    """ renders the plot on the fly.
    """
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(num_x_points)
    axis.plot(x_points, [random.randint(1, 30) for x in x_points])

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


@app.route("/matplot-as-image-<int:num_x_points>.svg")
def plot_svg(num_x_points=50):
    """ renders the plot on the fly.
    """
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
    indicators = ['risk','riskscatter'] 
    # indicators = ['sma']
    output = mplfinance_plot(data, ticker, indicators, 'candle', syear, 1, 1, 2021, 10, 22)
    return Response(output.getvalue(), mimetype="image/png")

# @app.route("/updatedata", methods=["POST", "GET"])
# def update_data():
#     if (request.method) == "POST":
#         tickers = request.form['ts'].split(',')
#         print('\n\n\n\n\n' + str(tickers) + '\n\n\n\n', file=sys.stderr)
#         download_multiple_stocks(1999, 1, 1, 2021, 10, 20, *tickers)
#         return index()
#     else:
#         ftickers = request.form['ts']
#         return "<h1>{ftickers}</h1>"
    # return redirect(url_for("index", ticker='SPY', num_x_points=50))
    

def get_df_from_csv(ticker):
    try:
        df = pd.read_csv('./' + ticker + '.csv')
    except FileNotFoundError:
        print('File does not exist')
    else:
        df = df.dropna(subset=['Adj Close'])
        return df

def save_to_csv_yahoo(ticker):
    # df = web.DataReader(ticker.strip(), 'yahoo', start, end)
    df = yfinance.download(ticker.strip(), period="MAX")
    df.to_csv(ticker + ".csv")
    return df

def define_risk(df):
    ma50 = 0 # To calculate 'Risk'
    df['sma50'] = df['Adj Close'].rolling(window=50, min_periods=1).mean()
    df['sma350'] = df['Adj Close'].rolling(window=350, min_periods=1).mean()
    df['Risk'] = df['sma50']/df['sma350'] # 'Risk'
    max_value = df['Risk'].max()
    min_value = df['Risk'].min()
    # if(min_value > 0):
    #     df['Risk'] = ((df['Risk'] - min_value) / (max_value - min_value))
    # elif(min_value < 0):
    #     df['Risk'] = ((df['Risk'] + min_value) / (max_value - min_value))
    # else:
    #     df['Risk'] = (df['Risk'] / max_value)
    df['Risk'] = (df['Risk'] - min_value) / (max_value - min_value)
    return df

def define_risk_scatter(df,ticker):
    if(ticker == 'SPY'):
        bbound1 = 0.7
        bbound2 = 0.6
        sbound1 = 0.8
        sbound2 = 0.9
    elif(ticker == 'BTC-USD'):
        bbound1 = 0.35
        bbound2 = 0.24
        sbound1 = 0.75
        sbound2 = 0.8
    else:
        bbound1 = 0.4
        bbound2 = 0.3
        sbound1 = 0.90
        sbound2 = 0.8

    df['BuySignal1'] = 0.0
    df['BuySignal1'] = np.where(df['Risk'] < bbound1, df['Adj Close'] * 0.95, np.nan)
    df['BuySignal2'] = 0.0
    df['BuySignal2'] = np.where(df['Risk'] < bbound2, df['Adj Close'] * 0.95, np.nan)
    df['SellSignal1'] = np.where(df['Risk'] > sbound1, df['Adj Close'] * 1.05, np.nan)
    df['SellSignal2'] = np.where(df['Risk'] > sbound2, df['Adj Close'] * 1.05, np.nan)
    return df

def define_sma(df):
    df['sma20'] = df['Adj Close'].rolling(window=20, min_periods=1).mean()
    df['sma140'] = df['Adj Close'].rolling(window=140, min_periods=1).mean()
    df['sma200'] = df['Adj Close'].rolling(window=200, min_periods=1).mean()
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
    if('risk' in indicators):
        df = define_risk(df)
        if(('riskscatter' in indicators) and (ticker in risk_scatter_tickers)):
            df = define_risk_scatter(df, ticker)
    if('sma' in indicators):
        df = define_sma(df)
    df_sub = df.loc[start:end]
    
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 24, 'text.color': '#EDEDED',
                            'axes.labelcolor':'#EDEDED', 'xtick.color':'#EDEDED', 'ytick.color':'#EDEDED'}, 
                            facecolor="#434345", edgecolor="#000000", figcolor="#434345")
    fig = mpf.figure(figsize=(12, 8), style=s)
    adps = []
    title = ticker
    if('risk' in indicators):
        adps.append(mpf.make_addplot(df_sub['Risk'], color='#ff5500', panel=1))#, secondary_y=True)) # Risk line plot and reference lines
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
        adps.append(mpf.make_addplot(df_sub['BuySignal1'],type="scatter", color=['#00aa00']))
        adps.append(mpf.make_addplot(df_sub['BuySignal2'],type="scatter", color=['#005500']))
        adps.append(mpf.make_addplot(df_sub['SellSignal1'],type="scatter", color=['#ff0000']))
        adps.append(mpf.make_addplot(df_sub['SellSignal2'],type="scatter", color=['#8a0000']))
    if('sma' in indicators): # Just some SMA lines
        adps.append(mpf.make_addplot(df_sub['sma20']))
        adps.append(mpf.make_addplot(df_sub['sma140']))
        adps.append(mpf.make_addplot(df_sub['sma200']))
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