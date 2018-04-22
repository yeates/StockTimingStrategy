import talib
from jqdata import *
import numpy
from sklearn.ensemble import RandomForestClassifier

'''
================================================================================
总体回测前
================================================================================
'''


# 总体回测前要做的事情
def initialize(context):
    set_params(context)  # 1设置策参数
    set_variables()  # 2设置中间变量
    set_backtest()  # 3设置回测条件


# 1
# 设置策略参数
def set_params(context):
    g.security = '600326.XSHG'  # 买卖股
    # g.benchmark = '000300.XSHG' # 训练股是大盘
    g.benchmark = g.security  # 训练股是买卖股本身
    BAYES_train(context)
    set_benchmark(g.security)  # 设置基准收益


# 2
# 设置中间变量
def set_variables():
    return


# 3
# 设置回测条件
def set_backtest():
    set_option('use_real_price', True)  # 用真实价格交易
    log.set_level('order', 'error')


# 随机森林训练分类器
def BAYES_train(context):
    end_date = context.previous_date  # 结束时间为回测的开始时间的前一天

    trading_days = get_all_trade_days().tolist()
    end_date_index = trading_days.index(end_date)
    start_date_index = end_date_index - (200 * 12)  # 周期为 200*12 个交易日的数据用于训练

    x_train = []  # 特征
    y_train = []  # 标记

    # 计算指标作为特征，并自动标记
    for index in range(start_date_index, end_date_index):

        start_day = trading_days[index - 30]  # 指标的计算范围为30个交易日
        end_day = trading_days[index]
        stock_data = get_price(g.benchmark, start_date=start_day, end_date=end_day, frequency='daily',
                               fields=['close', 'volume'])  # 获得前三十天的收盘价
        close_prices = stock_data['close'].values  # 将收盘价提取出来
        volume = stock_data['volume'].values

        # 通过90天收盘价和成交量计算指标
        vol_data = talib.OBV(close_prices, volume)[-2]

        features = []
        features.append(vol_data)

        label = False  # 标记为跌(False)
        if close_prices[-1] > close_prices[-2]:  # 如果今天的收盘价超过了昨天，那么标记为涨(True)
            label = True
        x_train.append(features)
        y_train.append(label)
    # n_estimators就是森林中包含的树的数目
    g.rfc_module = RandomForestClassifier(n_estimators=10)
    g.rfc_module.fit(x_train, y_train)  # 训练分类器


'''
================================================================================
每天交易时
================================================================================
'''


def handle_data(context, data):
    dt = context.previous_date
    trading_days = get_all_trade_days().tolist()
    index = trading_days.index(dt)
    today_stock_data = get_price(g.security, start_date=trading_days[index - 30], end_date=trading_days[index],
                                 frequency='daily', fields=['close', 'volume'])
    close_prices = today_stock_data['close'].values
    volume = today_stock_data['volume'].values

    # 计算指标
    vol_data = talib.OBV(close_prices, volume)[-2]

    # 添加今日的特征
    features = []
    x = []
    features.append(vol_data)
    x.append(features)

    flag = g.rfc_module.predict(x[0])  # 预测的涨跌结果

    cash = context.portfolio.portfolio_value
    if flag == True:
        if cash > 0:
            # 买入
            order_target_value(g.security, cash)
            print ("时间：%d/%d/%d    操作：买入    当前股价：%f" % (dt.year, dt.month, dt.day, data[g.security].price))
    elif flag == False:
        # 卖出
        order_target_value(g.security, 0)
        print ("时间：%d/%d/%d    操作：卖出    当前股价：%f" % (dt.year, dt.month, dt.day, data[g.security].price))