import pandas as pd
import numpy as np
import yfinance as yf
import datetime
from datetime import date


#Computes price of a call option from given stock price and the call
#options strike price
def call(price, strike_price):
    if(price-strike_price<=0):
        return 0
    else:
        return price - strike_price

#Computes price of a put option from given stock price and the put
#options strike price
def put(price, strike_price):
    if(strike_price-price<=0):
        return 0
    else:
        return strike_price - price

#Returns an array which is a row of the matrix A
#This row contains all of the prices of the ith row put option given each outcome
#for the stock price occurs
def findCallPrice(i, num_ps, optSortedCalls, interval, minimum):
    temp = []
    strike_price = optSortedCalls.loc[i]["strike"]
    for j in range(num_ps):
        price = minimum+((j+1)*(interval/(num_ps+1)))
        temp.append(call(price, strike_price))
    return temp

#Returns expected value of the ith row put option given X which 
# contains the appropriate probability measure 
def findPutPrice(i, num_ps, optSortedPuts, interval, minimum, X):
    result = 0
    strike_price = optSortedPuts.loc[i]["strike"]
    for j in range(num_ps):
        #Price of stock in wj
        price = minimum+((j+1)*(interval/(num_ps+1)))

        #Put option value in wj multiplied by pj
        result += put(price, strike_price)*X[j][0]
    return result

def options_chain(symbol, futureDate, r, max_put_options_priced, max_calls_used):
    tk = yf.Ticker(symbol)
    #Will be replaced with date the try makes it so it must be valid
    opt = tk.option_chain(futureDate)
    optCalls = opt.calls.sort_values(by="volume", ascending=False, inplace=False,ignore_index=True)
    optPuts = opt.puts.sort_values(by="volume", ascending=False, inplace=False,ignore_index=True)
    #print(optCalls.loc[0]["volume"])
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

    discount_factor = float(1/(pow((1+r),irp)))

    num_days = int(interest_rate_period*365)
    days = datetime.timedelta(num_days)
    new_date = presentTime - days

    hist = tk.history(interval="1d", start=new_date)
    maximum = max(hist["High"])
    minimum = min(hist["Low"])
    interval = maximum - minimum

    #Picking the interval from which our finite outcomes will occur
    #Depends upon how far away from the zero line the stock is
    if((stockPrice -interval)<=0):
        minimum = 0
        interval = 2*stockPrice
    else:
        minimum = stockPrice - interval
        interval *=2 #Need large interval so we don't get a row of zeros
        #Must reach all popular put strike prices


    #Limits matrix inversions to only 4x4 matricies
    num_variables = min(max_calls_used+1,numOfCallOptions+1)#3, num

    #Irrelevant but helps conceptualize stuff
    num_ps = num_equations = num_variables + 1

    #print(optCalls.loc[0]["volume"])
    rate = 1/discount_factor
    
    B=[]
    B.append([1])
    B.append([rate*stockPrice])
    #print(optCalls.loc[0]["volume"])
    #print(rate)
    for i in range(num_ps-2):
        #opt.calls.sort_values(by="volume", ascending=False, inplace=True)
        price = float(optCalls.loc[i]["lastPrice"])
        #print(optCalls.loc[i]["volume"])
        #print(price)
        B.append([round(rate*price,2)])
    #print(B)
    B = np.array(B)
    print(B)

    #A is the matrix containing all values pertaining to the probabilities
    #for solving the system of equations
    # i.e. if we have p1+ p2 = 1 and 3p1 + 4p2 = 4 then 
    # A = [[1,1],[3,4]]
    A = []

    #First row of all 1s "p1 + p2 + p3 + ... = 1"
    #A1 = [1, 1, 1, 1, ...]
    A1=[1 for col in range(num_ps)]
    A.append(A1)
    
    #Second row is the stock price i.e. S(w1)p1 + S(w2)p2 ... = (1+r)^irp * S_0
    #A2 = [S(w1)p1 , S(w2)p2 ...]
    A2 = []
    for j in range(num_ps):
        price = minimum+((j+1)*(interval/(num_ps+1)))
        A2.append(price)
    A.append(A2)

    #All remaining rows deal with the call prices
    #num_ps-2 rows left (num_ps = num_equations rows in total)
    #A3 contatins all the rows with call prices
    # i.e. A3 = [[C1(w1)p1 , C1(w2)p2 , ...], [C2(w1)p1 , C2(w2)p2 , ...], ...]
    A3 = []
    for i in range(num_ps-2):
        if(i<numOfCallOptions):
            A3.append(findCallPrice(i, num_ps, optCalls, interval, minimum))
    A += A3

    A = np.array(A)
    print(A)

    #If we can't invert matrix A to solve equation Ax = B
    try:
        inv_A = np.linalg.inv(A)
        X = inv_A.dot(B)
    except:
        statement = "If the system has a singular matrix then there is a solution set with an infinite number of solutions"
        return statement
    
    print(X)
    #If we get negative or non-positive probabilities
    for row in X:
        for probability in row:
            if probability<=0:
                statement = "There is no probability measure which fits this model\n"
                statement2 = "Thus by the Fundemental Theorem of Asset Pricing:\n"
                statement3 = "This model (including only calls and the stock itself) is not arbitrage free"
                return statement + statement2 + statement3


    result = []
    num_put_options_priced = min(max_put_options_priced,numOfPutsOptions)

    #Puts each strike price and the corresponding estimated price for that put
    #in a 2-element list and then adds that list to the result array
    for i in range(num_put_options_priced):
        temp = []

        strike = optPuts.loc[i]["strike"]
        expected_value = findPutPrice(i, num_ps, optPuts, interval, minimum, X)
        
        temp.append(strike)
        temp.append(expected_value*discount_factor)
        result.append(temp)
        
    return result

#works for 0.05<=r<=0.2 and calls_max 2,3
print(options_chain('AAPL',"2022-06-10",0.1,5,2))
