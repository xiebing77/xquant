#!/usr/bin/python
import numpy as np
import pandas as pd
import talib


def KDJ(df, n=9,ksgn='close'):
    '''
    【输入】
        df, pd.dataframe格式数据源
        n，时间长度
        ksgn，列名，一般是：close收盘价
    【输出】    
        df, pd.dataframe格式数据源,
        增加了一栏：_{n}，输出数据
    '''

    lowList= pd.Series(df['low']).rolling(n).min()  
    lowList.fillna(value=pd.Series(df['low']).expanding().min(), inplace=True)
 
    highList = pd.Series(df['high']).rolling(n).max()
    highList.fillna(value=pd.Series(df['high']).expanding().max(), inplace=True)

    p = pd.Series([float(x) for x in df[ksgn]])
    rsv = (p - lowList) / (highList - lowList) * 100
    df['RSV'] = rsv
    df['kdj_k'] = rsv.ewm(com=2,adjust=False).mean() #pd.ewma(rsv,com=2)
    df['kdj_d'] = df['kdj_k'].ewm(com=2).mean() #pd.ewma(df['kdj_k'],com=2)
    df['kdj_j'] = 3.0 * df['kdj_k'] - 2.0 * df['kdj_d']

    return        

def MACD(df,fastperiod=12, slowperiod=26, signalperiod=9):
	fastEMA = df['close'].ewm(span=fastperiod).mean()
	slowEMA = df['close'].ewm(span=slowperiod).mean()

	df['12ema'] = fastEMA
	df['26ema'] = slowEMA
	df['macd dif'] = fastEMA - slowEMA
	df['macd dea'] = df['macd dif'].ewm(span=signalperiod).mean()
	return 


