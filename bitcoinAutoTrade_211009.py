# Modified Version by Innyoung Kim
# https://ldgeao99.tistory.com/443?category=875616

from re import M, split
import time
import pyupbit
import datetime
import os

access = "4vyHNWPAzNMd9g5WH8axAIbw28ELA9VzwALmHydR"
secret = "06vulF2qAvA6SYZ8fZc4U9YajbgVG1lhQaJ5ff02"

def my_get_daily_ohlcv_from_base(ticker, base):
    """
    :param ticker:
    :param base:
    :return:
    """
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute60", count = 24*8)
        df = df.resample('24H', base=base).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        return df
    except Exception as x:
        return None


def get_k(ticker, base):
    k = 0
    
    df = my_get_daily_ohlcv_from_base(ticker, base)

    days = len(df) - 1
    for i in range(0, days):
        noise_ratio = 1.0 - abs(df.iloc[i]['open'] - df.iloc[i]['close'])/(df.iloc[i]['high'] - df.iloc[i]['low'])
        k += noise_ratio/float(days)
    return k

def get_target_price(ticker, k, base):
    df = my_get_daily_ohlcv_from_base(ticker, base)
    index = len(df) - 2
    target_price = df.iloc[index]['close'] + (df.iloc[index]['high'] - df.iloc[index]['low']) * k
    return target_price

def get_start_time(ticker, base):
    df = my_get_daily_ohlcv_from_base(ticker, base)
    start_time = df.index[len(df) - 1]
    return start_time

def get_my_net_worth():
    balances = upbit.get_balances()

    for i in range(len(balances)):
        if balances[i]['currency'] == 'KRW':
            my_KRW = float(balances[i]['balance'])
            break

    for i in range(len(balances)):
        if balances[i]['currency'] == 'BTC':
            my_BTC = float(balances[i]['balance'])*float(get_current_price("KRW-BTC"))
            break

    for i in range(len(balances)):
        if balances[i]['currency'] == 'ETH':
            my_ETH = float(balances[i]['balance'])*float(get_current_price("KRW-ETH"))
            break

    my_net_worth = my_KRW + my_BTC + my_ETH
    
    return my_net_worth

def get_current_price(ticker):
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_ma_score(ticker, base):
    ma_score = 0.0

    df = my_get_daily_ohlcv_from_base(ticker, base)
    days = len(df) - 1  
    
    for i in range(2, days):
        df_tmp = df['close'][0:i]
        ma = df_tmp.rolling(len(df_tmp)).mean().iloc[-1]
        current_price = get_current_price(ticker)
        if ma <= current_price:
            ma_score += 1.0/(days-2.0)

    return ma_score

def get_volatility_control_ratio(ticker, base):
    volatility_control_ratio = 0.0
    target_volatility = 0.02

    df = my_get_daily_ohlcv_from_base(ticker, base)
    index = len(df) - 2 # Starting day - 1
    current_price = get_current_price(ticker)
    yesterdaty_volatility = (df.iloc[index]['high'] - df.iloc[index]['low'])/current_price

    volatility_control_ratio = target_volatility/yesterdaty_volatility

    return volatility_control_ratio

upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

kkk = 0
my_coin_BTC = {}
my_coin_ETH = {}
for iii in range(1, 24):
    my_coin_BTC[iii] = 0.0
    my_coin_ETH[iii] = 0.0

# Restart my_coin
if os.path.isfile('./restart'):
    file_restart = open("./restart", 'r')
    while True:
        line = file_restart.readline()
        if not line: break
        line = line.split(' ,')
        my_coin_BTC[int(line[0])] =  float(line[1])
        my_coin_ETH[int(line[0])] =  float(line[2])
    
    file_restart.close()

while True:
    try:
        kkk += 1
        now = datetime.datetime.now()

        # BTC
        for iii in range(1, 24):
            start_time = get_start_time("KRW-BTC", iii)
            end_time = start_time + datetime.timedelta(days=1)
            k = get_k("KRW-BTC", iii)

            if start_time < now < end_time - datetime.timedelta(seconds=500):
                target_price = get_target_price("KRW-BTC", k, iii)
                current_price = get_current_price("KRW-BTC")
                betting_total = float(get_my_net_worth()/23.0/2.0)
                betting_ratio = get_ma_score("KRW-BTC", iii)*get_volatility_control_ratio("KRW-BTC", iii)
                betting_amount = betting_total*betting_ratio

                if (target_price < current_price) and (my_coin_BTC[iii] == 0.0) :
                    upbit.buy_market_order("KRW-BTC", betting_amount*0.9995)
                    my_coin_BTC[iii] = betting_amount*0.9995/current_price

            else:
               upbit.sell_market_order("KRW-BTC", my_coin_BTC[iii]*0.99999)
               my_coin_BTC[iii] = 0.0
            
            if kkk%5 == 0:
                file_log = open("log", 'a')
                data = "------------------BTC-Time: {}-----------------\n".format(now)
                file_log.write(data)
                data = "Start Time: {}, k: {}, target price:{}, current price:{}\nbetting total: {}, betting_ratio: {}, betting_amount:{}\n".format(start_time, k, target_price, current_price, betting_total, betting_ratio, betting_amount)
                file_log.write(data)
                file_log.close()
            time.sleep(0.2)
        
        # ETH
        for iii in range(1, 24):
            start_time = get_start_time("KRW-ETH", iii)
            end_time = start_time + datetime.timedelta(days=1)
            k = get_k("KRW-ETH", iii)

            if start_time < now < end_time - datetime.timedelta(seconds=500):
                target_price = get_target_price("KRW-ETH", k, iii)
                current_price = get_current_price("KRW-ETH")
                betting_total = float(get_my_net_worth()/23.0/2.0)
                betting_ratio = get_ma_score("KRW-ETH", iii)*get_volatility_control_ratio("KRW-ETH", iii)
                betting_amount = betting_total*betting_ratio

                if (target_price < current_price) and (my_coin_ETH[iii] == 0.0):
                    upbit.buy_market_order("KRW-ETH", betting_amount*0.9995)
                    my_coin_ETH[iii] = betting_amount*0.9995/current_price

            else:
               upbit.sell_market_order("KRW-ETH", my_coin_ETH[iii]*0.99999)
               my_coin_ETH[iii] = 0.0
            
            if kkk%5 == 0:
                file_log = open("log", 'a')
                data = "------------------ETH-Time: {}-----------------\n".format(now)
                file_log.write(data)
                data = "Start Time: {}, k: {}, target price:{}, current price:{}\nbetting total: {}, betting_ratio: {}, betting_amount:{}\n".format(start_time, k, target_price, current_price, betting_total, betting_ratio, betting_amount)
                file_log.write(data)
                file_log.close()
            time.sleep(0.2)

        if kkk%5 == 0:
            file_log = open("log", 'a')
            data = "----------------information-------------\n{}\n{}".format(my_coin_BTC, my_coin_ETH)
            file_log.write(data)
            file_log.close()

            # Write restart file
            file_restart = open("restart", 'a')
            for i in range(1, 24):
                data = "{}, {}, {}\n".format(i, my_coin_BTC[i], my_coin_ETH[i])
                file_restart.write(data)
            file_restart.close()

        time.sleep(0.2)

    except Exception as e:
        print(e)
        time.sleep(1)