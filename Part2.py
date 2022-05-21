import pandas as pd
import numpy as np
import yfinance as yf
import datetime
from datetime import date


def options_chain(symbol, futureDate, r):
    tk = yf.Ticker(symbol)
    #Will be replaced with date the try makes it so it must be valid
    opt = tk.option_chain(futureDate)
    numOfCallOptions = len(opt.calls)
    numOfPutsOptions = len(opt.puts)
    #print(opt.calls.iloc[0])
    
    # data available via: opt.calls, opt.puts
    stockPrice = (tk.info['bid'] + tk.info['ask']) /2

    today = date.today()
    todayDate = today.strftime("%d/%m/%Y")
    presentTime = datetime.datetime.strptime(todayDate, "%d/%m/%Y")

    futureTime = datetime.datetime.strptime(futureDate, '%Y-%m-%d')
    difference = futureTime - presentTime
    total_seconds = difference.total_seconds()
    interest_rate_period = total_seconds/(60*60*24*365) #in years
    irp =interest_rate_period
    print(interest_rate_period)

    num_days = int(interest_rate_period*365)
    days = datetime.timedelta(num_days)
    new_date = presentTime - days
    print(new_date)

    hist = tk.history(interval="1d", start=new_date)
    maximum = max(hist["High"])
    minimum = min(hist["Low"])
    interval = maximum - minimum

    #Limits matrix inversions to only 6x6 matricies
    num_variables = min(5,numOfCallOptions+1)

    B=[]
    B.append([1])
    B.append([pow((1+r),irp)*stockPrice])
    for i in range(num_variables-2):
        rate = float(pow((1+r),irp))
        price = float(opt.calls.loc[i]["lastPrice"])
        B.append([round(rate*price,2)])
    print(B)
    B = np.array(B)

    A=[1 for col in range(num_variables)]
    A2 = []
    for i in range(num_variables):
        A2 +=[]




    "p1 + p2 +p3 = 1"

    return stockPrice
options_chain('AAPL',"2022-06-10",0.01)