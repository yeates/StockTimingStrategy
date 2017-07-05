import numpy as np
'''
================================================================================
总体回测前
================================================================================
'''
#总体回测前要做的事情
def initialize(context):
    set_params(context)    #1设置策参数
    set_variables() #2设置中间变量
    set_backtest()  #3设置回测条件

#1
#设置策略参数
def set_params(context):
    g.security = "510300.XSHG"
    set_benchmark('510300.XSHG')
    g.benchmark = '000300.XSHG'
    g.days = 0
    g.start = context.current_dt.date()
    g.one = 5
    g.two = 26
    g.three = 135
    g.pre_volume_one = 0
    g.pre_volume_two = 0
    g.n=13
    g.zs=0.03

#2
#设置中间变量
def set_variables():
    return

#3
#设置回测条件
def set_backtest():
    set_option('use_real_price', True) #用真实价格交易
    log.set_level('order', 'error')






'''
================================================================================
每天开盘前
================================================================================
'''
#每天开盘前要做的事情
def before_trading_start(context):
    set_slip_fee(context)


#4
# 根据不同的时间段设置滑点与手续费
def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 根据不同的时间段设置手续费
    dt=context.current_dt

    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))

    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))

    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))

    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))



'''
================================================================================
每天交易时
================================================================================
'''
def handle_data(context, data):
  # ## 止损
    d = dp_stoploss(2, g.n, g.zs)
    if d:
        if len(context.portfolio.positions)>0:
            for stock in list(context.portfolio.positions.keys()):
                order_target(stock, 0)
        return

    dt = context.current_dt
    if dt.hour == 9 and dt.minute == 30:
        g.days += 1
        if g.days == g.two:
            end = dt.date()
            df_one = get_price(g.benchmark, start_date=end - timedelta(days=g.one), end_date=end, frequency='daily', fields=['volume'])
            df_two = get_price(g.benchmark, start_date=end - timedelta(days=g.two), end_date=end, frequency='daily', fields=['volume'])
            g.pre_volume_one = df_one['volume'].mean()
            g.pre_volume_two = df_two['volume'].mean()
    end = context.current_dt.date()
    df = get_price(g.benchmark, start_date=g.start, end_date=end, frequency='daily', fields=['close','volume'])
    a = df['volume'].values[0]
    #record(volume=a)
    #print df['volume'].values
    g.start = end

    df_one = get_price(g.benchmark, start_date=end - timedelta(days=g.one), end_date=end, frequency='daily', fields=['volume'])
    df_two = get_price(g.benchmark, start_date=end - timedelta(days=g.two), end_date=end, frequency='daily', fields=['volume'])
    df_three = get_price(g.benchmark, start_date=end - timedelta(days=g.three), end_date=end, frequency='daily', fields=['volume'])
    volume_one = df_one['volume'].mean()
    volume_two = df_two['volume'].mean()
    volume_three = df_three['volume'].mean()
    cash = context.portfolio.cash
    record(two=volume_three)
    record(one=volume_two)
    if g.pre_volume_one < volume_one and g.pre_volume_one < g.pre_volume_two and volume_one > volume_two:
        #买入
        if cash > 0 : order_target_value(g.security, cash)
        print '买出'
    if g.pre_volume_one > volume_one and g.pre_volume_two > volume_two and g.pre_volume_one > g.pre_volume_two and volume_one < volume_two:
        #卖出
        order_target_value(g.security, 0)
        print '卖入'
        #print g.pre_volume_one, volume_one
    #elif volume_three > volume_one:
     #   order_target_value(g.security, 0)
    if g.days > g.two:
        g.pre_volume_one = volume_one
        g.pre_volume_two = volume_two


def dp_stoploss(kernel=2, n=10, zs=0.03):
    '''
    方法1：当大盘N日均线(默认60日)与昨日收盘价构成“死叉”，则发出True信号
    方法2：当大盘N日内跌幅超过zs，则发出True信号
    '''
    # 止损方法1：根据大盘指数N日均线进行止损
    if kernel == 1:
        t = n+2
        hist = attribute_history('000300.XSHG', t, '1d', 'close', df=False)
        temp1 = sum(hist['close'][1:-1])/float(n)
        temp2 = sum(hist['close'][0:-2])/float(n)
        close1 = hist['close'][-1]
        close2 = hist['close'][-2]
        if (close2 > temp2) and (close1 < temp1):
            return True
        else:
            return False
    # 止损方法2：根据大盘指数跌幅进行止损
    elif kernel == 2:
        hist1 = attribute_history('000300.XSHG', n, '1d', 'close',df=False)
        if ((1-float(hist1['close'][-1]/hist1['close'][0])) >= zs):
            return True
        else:
            return False
'''
================================================================================
每天收盘后
================================================================================
'''
# 每日收盘后要做的事情（本策略中不需要）
def after_trading_end(context):
    return
