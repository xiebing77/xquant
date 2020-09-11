# xquant
量化交易

## 运行环境
python3.6
mongodb3.6
## 实盘
python3 real.py -e binance -sc strategy/kd/kd_btc_usdt.jsn -sii testkdj -v 500 --log
## 回测
python3 backtest.py -m binance -sc strategy/kd/kd_btc_usdt.jsn -r 2020-4-1~2020-4-12
## 目录说明
### utils
工具，不仅限于本项目
### common
本项目共用
### db
数据库</br>
目前支持mongodb
### exchange
交易所</br>
目前完全支持binance(现货、保证金杠杆、期货合约，都支持)</br>
部分支持okex（调试未完成）
### md
市场行情数据</br>
目前支持本地数据库行情数据、交易所实时行情数据
### engine
引擎</br>
目前已经支持实盘、历史回测</br>
实时仿真待续...
### strategy
策略库

