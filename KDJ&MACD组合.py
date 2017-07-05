import math

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

    g.security = '510300.XSHG'
    g.benchmark = '000300.XSHG'
    set_universe([g.security])
    set_benchmark("510300.XSHG")
    #KDJ
    #设定KDJ指标初始值
    g.K1 = 50
    g.D1 = 50
    g.N = 14

    #MACD
    g.tc=15  # 调仓频率
    g.pre_dea = 0
    g.pre_ema_12 = 0
    g.pre_ema_26 = 0
    g.days = 0 #记录当前的天数
    g.count = 0
    g.one = 7
    g.two = 23

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
每天开盘时
================================================================================
'''
def handle_data(context, data):
    dt = context.current_dt
    if dt.hour == 9 and dt.minute == 30:
        g.days += 1

    ##预处理(KDJ)
    count = g.N #设定KDJ基期值
    a = 1.0/3
    b = 1.0/3
    K2 = 50
    D2 = 50
    close_price = history(count, unit='1d', field='close', security_list=None)
    if not math.isnan(close_price[g.security][0]):
        g.K1,g.D1,K2,D2,J2 = KDJ(count,a,b,g.K1,g.D1)

    capital_unit = context.portfolio.portfolio_value
    #执行卖出操作
    if signal_stock_sell(context,data, close_price, K2, D2) == True:
        order_target_value(g.security,0)
        print ("时间：%d/%d/%d    操作：卖出    当前股价：%f"%(dt.year, dt.month, dt.day, data[g.security].price))
    # 执行买入操作
    if signal_stock_buy(context,data, close_price, K2, D2) == True:
        print ("时间：%d/%d/%d    操作：买入    当前股价：%f"%(dt.year, dt.month, dt.day, data[g.security].price))
        order_target_value(g.security,capital_unit)

    g.K1 = K2
    g.D1 = D2


#5
#获得卖出信号
#输入：context, data
#输出：sell - list
def signal_stock_sell(context,data, close_price, K2, D2):
    macd = False
    kdj = False
    ## MACD
    (dif_pre, dif_now) = get_dif()
    (dea_pre, dea_now) = get_dea(dif_now)
    # 如果短均线从上往下穿越长均线，则为死叉信号，标记卖出
    if dif_now < dea_now and dif_pre > dea_pre and context.portfolio.positions[g.security].sellable_amount > 0:
        macd = True
        pass

    ## KDJ
    #设定k、d平滑因子a、b，不过目前已经约定俗成，固定为1/3
    if not math.isnan(close_price[g.security][0]):
        # 取得当前的现金
        cash = context.portfolio.cash
        # 取得当前价格
        current_price = data[g.security].price
    	#k线由右边向下交叉d值时做卖，k线由右边向上交叉d值做买
        if K2>75 and D2>75 and g.K1 > g.D1 and K2 < D2 and context.portfolio.positions[g.security].amount > 0:
            kdj = True
            pass

    return macd or kdj

#6
#获得买入信号
#输入：context, data
#输出：buy - list
def signal_stock_buy(context,data, close_price, K2, D2):
    macd = False
    kdj = False
    ## MACD
    (dif_pre, dif_now) = get_dif()
    (dea_pre, dea_now) = get_dea(dif_now)
    if g.days >= 27:
        g.pre_ema_12 = get_EMA(g.benchmark, g.one, data)
        g.pre_ema_26 = get_EMA(g.benchmark, g.two, data)
    # 如果短均线从下往上穿越长均线，则为金叉信号，标记买入
    if dif_now > dea_now and dif_pre < dea_pre and context.portfolio.positions[g.security].sellable_amount == 0 :
        macd = True
        pass

    ## KDJ
    if not math.isnan(close_price[g.security][0]):
        cash = context.portfolio.cash
        current_price = data[g.security].price
        if K2<25 and D2<25 and g.K1< g.D1 and K2>D2:
            # 计算可以买多少只股票
            number_of_shares = int(cash/current_price)
            # 购买量大于0时，下单
            if number_of_shares > 0:
                # 买入股票
                kdj = True
                pass
    return macd or kdj

######  KDJ
#定义KDJ计算函数，输入为基期长度count、平滑因子a，输出为KDJ指标值。
#K1为前一日k值,D1为前一日D值,K2为当日k值,D2为当日D值,J为当日J值
def KDJ(count,a,b,K1,D1):
    h = attribute_history(g.security, count, unit='1d',fields=('close', 'high', 'low'),skip_paused=True)
    # 取得过去count天的最低价格
    low_price = h['low'].min()
    # 取得过去count天的最高价格
    high_price = h['high'].max()
    # 取得当日收盘价格
    current_close = h['close'][-1]
    if high_price!=low_price:
        #计算未成熟随机值RSV(n)＝（Ct－Ln）/（Hn-Ln）×100
        RSV = 100*(current_close-low_price)/(high_price-low_price)
    else:
        RSV = 50
    #当日K值=(1-a)×前一日K值+a×当日RSV
    K2=(1-a)*K1+a*RSV
    #当日D值=(1-a)×前一日D值+a×当日K值
    D2=(1-b)*D1+b*K2
    #计算J值
    J2 = 3*K2-2*D2
    return g.K1,g.D1,K2,D2,J2


######  MACD
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
