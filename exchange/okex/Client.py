#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

from OkcoinSpotAPI import OKCoinSpot
from OkcoinFutureAPI import OKCoinFuture
import os

#初始化apikey，secretkey,url
apikey = os.environ.get('OKEX_API_KEY')
secretkey = os.environ.get('OKEX_SECRET_KEY')
okcoinRESTURL = 'www.okex.com'   #请求注意：国内账号需要 修改为 www.okcoin.cn

#现货API
okcoinSpot = OKCoinSpot(okcoinRESTURL,apikey,secretkey)

#期货API
okcoinFuture = OKCoinFuture(okcoinRESTURL,apikey,secretkey)

coin = 'dpy_eth'

# print(len(okcoinSpot.get_kline(coin, '1day', 7)))
# print (u' Spot ticker ')
# print (okcoinSpot.ticker(coin))
#
# print (u' Spot depth ')
# print (okcoinSpot.depth(coin))
#
# print (u' Spot trades history')
# print (okcoinSpot.trades(coin))

#print (u' Spot user info ')
#print (okcoinSpot.userinfo())

#print (u' Spot trade ')
#print (okcoinSpot.trade(coin,'buy','0.1','0.2'))

#print (u' 现货批量下单 ')
#print (okcoinSpot.batchTrade(coin,'buy','[{price:0.1,amount:0.2},{price:0.1,amount:0.2}]'))

#print (u' 现货取消订单 ')
#print (okcoinSpot.cancelOrder(coin,'18243073'))

#print (u' 现货订单信息查询 ')
print (okcoinSpot.orderinfo(coin,'-1'))

# print (u' 现货批量订单信息查询 ')
# print (okcoinSpot.ordersinfo(coin,'18243800,18243801,18243644','0'))

print (u' 现货历史订单信息查询 ')
print (okcoinSpot.orderHistory(coin,'1','1','20'))

#print (u' 期货行情信息')
#print (okcoinFuture.future_ticker(coin,'this_week'))

#print (u' 期货市场深度信息')
#print (okcoinFuture.future_depth('btc_usd','this_week','6'))

#print (u'期货交易记录信息')
#print (okcoinFuture.future_trades(coin,'this_week'))

#print (u'期货指数信息')
#print (okcoinFuture.future_index(coin))

#print (u'美元人民币汇率')
#print (okcoinFuture.exchange_rate())

#print (u'获取预估交割价')
#print (okcoinFuture.future_estimated_price(coin))

#print (u'获取全仓账户信息')
#print (okcoinFuture.future_userinfo())

#print (u'获取全仓持仓信息')
#print (okcoinFuture.future_position(coin,'this_week'))

#print (u'期货下单')
#print (okcoinFuture.future_trade(coin,'this_week','0.1','1','1','0','20'))

#print (u'期货批量下单')
#print (okcoinFuture.future_batchTrade(coin,'this_week','[{price:0.1,amount:1,type:1,match_price:0},{price:0.1,amount:3,type:1,match_price:0}]','20'))

#print (u'期货取消订单')
#print (okcoinFuture.future_cancel(coin,'this_week','47231499'))

#print (u'期货获取订单信息')
#print (okcoinFuture.future_orderinfo(coin,'this_week','47231812','0','1','2'))

#print (u'期货逐仓账户信息')
#print (okcoinFuture.future_userinfo_4fix())

#print (u'期货逐仓持仓信息')
#print (okcoinFuture.future_position_4fix(coin,'this_week',1))




