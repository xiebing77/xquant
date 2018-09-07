# xquant
量化交易

## 运行环境
### 普通模式
python3.6
mongodb3.6
### docker模式
为了标准化运行环境，特采用docker，请先安装docker！
#### db容器
1. 创建db容器
> docker run -d -v <宿主目录>:/db_data --name xquant-db mongo
2. 进入db容器
> docker exec -i -t xquant-db /bin/bash  
3. 退出db容器
> exit

#### xquant容器
1. 创建xquant镜像
> cd xquant/docker  
  docker build -t "xquant:v0.0.1" .
##### 交互式
1. 第一次
> docker run -i -t -v <宿主目录>:/xquant --name xquant dd1e3f6e2749 /bin/bash  
3. 第二次及以后
> docker start xquant  
  docker attach xquant

##### 后台

## 数据
### 登录
mongo mongodb://<user>:<password>@localhost/binance
### 导出
mongodump -d binance -c kline_1day_btc_usdt  
mongodump -d binance -c kline_btc_usdt
### 导入
mongorestore -d binance -c kline_1day_btc_usdt kline_1day_btc_usdt.bson  
mongorestore -d binance -c kline_btc_usdt kline_btc_usdt.bson
## 程序入口
main.py
### 使用方式
参见kdj_btc_usdt.sh

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
目前完全支持binance</br>
部分支持okex（调试未完成）
### engine
引擎</br>
目前已经支持实盘、历史回测</br>
实时仿真待续...
### strategy
策略库
