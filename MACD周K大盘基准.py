import numpy as np
'''
================================================================================
总体回测前
================================================================================
'''
#总体回测前要做的事情
def initialize(context):
    set_params()    #1设置策参数
    set_variables() #2设置中间变量
    set_backtest()  #3设置回测条件

#1
#设置策略参数
def set_params():
    g.tc=15  # 调仓频率
    g.N = 1
    g.security = "510300.XSHG"
    set_benchmark('510300.XSHG')
    g.benchmark = '000300.XSHG'
    g.pre_dea = 0
    g.pre_ema_12 = 0
    g.pre_ema_26 = 0
    g.days = 0 #记录当前的天数
    g.count = 0
    g.one = 11
    g.two = 20
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
    dt = context.current_dt
    if dt.hour == 9 and dt.minute == 30:
        g.count += 1
    if g.count % 7 == 0:
        g.count = 1
        g.days += 1
    # 将总资金等分为g.N份，为每只股票配资
    capital_unit = context.portfolio.portfolio_value/g.N

    #执行卖出操作
    if signal_stock_sell(context,data) == True:
        order_target_value(g.security,0)
        print ("时间：%d/%d/%d    操作：卖出    当前股价：%f"%(dt.year, dt.month, dt.day, data[g.security].price))
    # 执行买入操作
    if signal_stock_buy(context,data) == True:
        print ("时间：%d/%d/%d    操作：买入    当前股价：%f"%(dt.year, dt.month, dt.day, data[g.security].price))
        order_target_value(g.security,capital_unit)



#5
#获得卖出信号
#输入：context, data
#输出：sell - list
def signal_stock_sell(context,data):
    (dif_pre, dif_now) = get_dif()
    (dea_pre, dea_now) = get_dea(dif_now)
    # 如果短均线从上往下穿越长均线，则为死叉信号，标记卖出
    if dif_now < dea_now and dif_pre > dea_pre and context.portfolio.positions[g.security].sellable_amount > 0:
        return True
    return False


#6
#获得买入信号
#输入：context, data
#输出：buy - list
def signal_stock_buy(context,data):
    (dif_pre, dif_now) = get_dif()
    (dea_pre, dea_now) = get_dea(dif_now)
    if g.days >= 27:
        g.pre_ema_12 = get_EMA(g.benchmark, g.one, data)
        g.pre_ema_26 = get_EMA(g.benchmark, g.two, data)
    # 如果短均线从下往上穿越长均线，则为金叉信号，标记买入
    if dif_now > dea_now and dif_pre < dea_pre and context.portfolio.positions[g.security].sellable_amount == 0 :
        return True
    return False


#7
# 计算移动平均线数据
# 输入：股票代码-字符串，移动平均线天数-整数
# 输出：算术平均值-浮点数
def get_MA(security_code,days):
    # 获得前days天的数据，详见API
    a=attribute_history(security_code, days, '1d', ('close'))
    # 定义一个局部变量sum，用于求和
    sum=0
    # 对前days天的收盘价进行求和
    for i in range(1,days+1):
        sum+=a['close'][-i]
    # 求和之后除以天数就可以的得到算术平均值啦
    return sum/days

#8
# 计算指数移动平均线数据
# 输入：股票代码-字符串，移动指数平均线天数-整数，data
# 输出：今天和昨天的移动指数平均数-浮点数
def get_EMA(security_code,days,data):
    # 如果只有一天的话,前一天的收盘价就是移动平均
    if days==1:
    # 获得前两天的收盘价数据，一个作为上一期的移动平均值，后一个作为当期的移动平均值
        t = attribute_history(security_code, 2, '1d', ('close'))
        return t['close'][-1]
    else:
    # 如果全局变量g.EMAs不存在的话，创建一个字典类型的变量，用来记录已经计算出来的EMA值
        if 'EMAs' not in dir(g):
            g.EMAs={}
        # 字典的关键字用股票编码和天数连接起来唯一确定，以免不同股票或者不同天数的指数移动平均弄在一起了
        key="%s%d" %(security_code,days)
        # 如果关键字存在，说明之前已经计算过EMA了，直接迭代即可
        if key in g.EMAs:
            #计算alpha值
            alpha=(days-1.0)/(days+1.0)
            # 获得前一天的EMA（这个是保存下来的了）
            EMA_pre=g.EMAs[key]
            # EMA迭代计算
            EMA_now=EMA_pre*alpha+data[security_code].close*(1.0-alpha)
            # 写入新的EMA值
            g.EMAs[key]=EMA_now
            # 给用户返回昨天和今天的两个EMA值
            return EMA_now
        # 如果关键字不存在，说明之前没有计算过这个EMA，因此要初始化
        else:
            # 获得days天的移动平均
            ma=get_MA(security_code,days)
            # 如果滑动平均存在（不返回NaN）的话，那么我们已经有足够数据可以对这个EMA初始化了
            if not(isnan(ma)):
                g.EMAs[key]=ma
                # 因为刚刚初始化，所以前一期的EMA还不存在
                return ma
            else:
                # 移动平均数据不足days天，只好返回NaN值
                return float("nan")

def get_dif():
    if g.pre_ema_12 == 0 or g.pre_ema_26 == 0:
        return (0, 0)
    else:
        pre_dif = g.pre_ema_12 - g.pre_ema_26
        close_price = attribute_history(g.benchmark, 1, '1d', 'close') #close_price[0]为当天的收盘价
        g.pre_ema_12 = g.pre_ema_12 * 11 / 13 + close_price['close'][0] * 2 / 13
        g.pre_ema_26 = g.pre_ema_26 * 25 / 27 + close_price['close'][0] * 2 / 27
        return (pre_dif, g.pre_ema_12 - g.pre_ema_26)

def get_dea(dif):
    if g.pre_dea == 0:
        return (0, 0)
    else:
        pre_dea = g.pre_dea
        g.pre_dea = g.pre_dea * 8 / 10 + dif * 2 / 10
        return (pre_dea, g.pre_dea)


'''
================================================================================
每天收盘后
================================================================================
'''
# 每日收盘后要做的事情（本策略中不需要）
def after_trading_end(context):
    return
