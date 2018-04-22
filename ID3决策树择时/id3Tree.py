# -*- coding: utf-8 -*-
from math import log
import operator

def calEnt(dataSet):
    #获取数据集的行数
    numEntries=len(dataSet)
    #设置字典的数据结构
    labelCounts={}
    #提取数据集的每一行的特征向量
    for featVec in dataSet:
        #获取特征向量的最后一列的标签
        currentLabel=featVec[-1]
        #检测字典的关键字key中是否存在该标签
        #如果不存在keys()关键字
        if currentLabel not in labelCounts.keys():
            #将当前标签/0键值对存入字典中
            labelCounts[currentLabel]=0
        #否则将当前标签对应的键值加1
        labelCounts[currentLabel]+=1
    #初始化熵为0
    Ent=0.0
    #对于数据集中所有的分类类别
    for key in labelCounts:
        #计算各个类别出现的频率
        prob=float(labelCounts[key])/numEntries
        #计算各个类别信息期望值
        Ent-=prob*log(prob,2)
    #返回熵
    return Ent


#划分数据集：按照最优特征划分数据集
#@dataSet:待划分的数据集
#@axis:划分数据集的特征
#@value:特征的取值
def splitDataSet(dataSet,axis,value):
    #需要说明的是,python语言传递参数列表时，传递的是列表的引用
    #如果在函数内部对列表对象进行修改，将会导致列表发生变化，为了
    #不修改原始数据集，创建一个新的列表对象进行操作
    retDataSet=[]
    #提取数据集的每一行的特征向量
    for featVec in dataSet:
        #针对axis特征不同的取值，将数据集划分为不同的分支
        #如果该特征的取值为value
        if featVec[axis]==value:
            #将特征向量的0~axis-1列存入列表reducedFeatVec
            reducedFeatVec=featVec[:axis]
            #将特征向量的axis+1~最后一列存入列表reducedFeatVec
            #extend()是将另外一个列表中的元素（以列表中元素为对象）一一添加到当前列表中，构成一个列表
            #比如a=[1,2,3],b=[4,5,6],则a.extend(b)=[1,2,3,4,5,6]
            reducedFeatVec.extend(featVec[axis+1:])
            #简言之，就是将原始数据集去掉当前划分数据的特征列
            #append()是将另外一个列表（以列表为对象）添加到当前列表中
            ##比如a=[1,2,3],b=[4,5,6],则a.extend(b)=[1,2,3,[4,5,6]]
            retDataSet.append(reducedFeatVec)
    return retDataSet


#如何选择最好的划分数据集的特征
#使用某一特征划分数据集，信息增益最大，则选择该特征作为最优特征
def chooseBestFeatureToSplit(dataSet):
    #获取数据集特征的数目(不包含最后一列的类标签)
    numFeatures=len(dataSet[0])-1
    #计算未进行划分的信息熵
    baseEntropy=calEnt(dataSet)
    #最优信息增益    最优特征
    bestInfoGain=0.0;bestFeature=-1
    #利用每一个特征分别对数据集进行划分，计算信息增益
    for i in range(numFeatures):
        #得到特征i的特征值列表
        featList=[example[i] for example in dataSet]
        #利用set集合的性质--元素的唯一性，得到特征i的取值
        uniqueVals=set(featList)
        #信息增益0.0
        newEntropy=0.0
        #对特征的每一个取值，分别构建相应的分支
        for value in uniqueVals:
            #根据特征i的取值将数据集进行划分为不同的子集
            #利用splitDataSet()获取特征取值Value分支包含的数据集
            subDataSet=splitDataSet(dataSet,i,value)
            #计算特征取值value对应子集占数据集的比例
            prob=len(subDataSet)/float(len(dataSet))
            #计算占比*当前子集的信息熵,并进行累加得到总的信息熵
            newEntropy+=prob*calEnt(subDataSet)
        #计算按此特征划分数据集的信息增益
        #公式特征A,数据集D
        #则H(D,A)=H(D)-H(D/A)
        infoGain=baseEntropy-newEntropy
        #比较此增益与当前保存的最大的信息增益
        if (infoGain>bestInfoGain):
            #保存信息增益的最大值
            bestInfoGain=infoGain
            #相应地保存得到此最大增益的特征i
            bestFeature=i
        #返回最优特征
    return bestFeature


#当遍历完所有的特征属性后，类标签仍然不唯一(分支下仍有不同分类的实例)
#采用多数表决的方法完成分类
def majorityCnt(classList):
    #创建一个类标签的字典
    classCount={}
    #遍历类标签列表中每一个元素
    for vote in classList:
        #如果元素不在字典中
        if vote not in classCount.keys():
            #在字典中添加新的键值对
            classCount[vote]=0
        #否则，当前键对于的值加1
        classCount[vote]+=1
    #对字典中的键对应的值所在的列，按照又大到小进行排序
    #@classCount.items 列表对象
    #@key=operator.itemgetter(1) 获取列表对象的第一个域的值
    #@reverse=true 降序排序，默认是升序排序
    sortedClassCount=sorted(classCount.items,\
    key=operator.itemgetter(1), reverse=True)
    #返回出现次数最多的类标签
    return sortedClassCount[0][0]


# 创建树
def createTree(dataSet, labels):
    # 获取数据集中的最后一列的类标签，存入classList列表
    classList = [example[-1] for example in dataSet]
    # 通过count()函数获取类标签列表中第一个类标签的数目
    # 判断数目是否等于列表长度，相同表面所有类标签相同，属于同一类
    if classList.count(classList[0]) == len(classList):
        return classList[0]
    # 遍历完所有的特征属性，此时数据集的列为1，即只有类标签列
    if len(dataSet[0]) == 1:
        # 多数表决原则，确定类标签
        return majorityCnt(classList)
    # 确定出当前最优的分类特征
    bestFeat = chooseBestFeatureToSplit(dataSet)
    # 在特征标签列表中获取该特征对应的值
    bestFeatLabel = labels[bestFeat]
    # 采用字典嵌套字典的方式，存储分类树信息
    myTree = {bestFeatLabel: {}}

    ##此位置书上写的有误，书上为del(labels[bestFeat])
    ##相当于操作原始列表内容，导致原始列表内容发生改变
    ##按此运行程序，报错'no surfacing'is not in list
    ##以下代码已改正

    # 复制当前特征标签列表，防止改变原始列表的内容
    subLabels = labels[:]
    # 删除属性列表中当前分类数据集特征
    del (subLabels[bestFeat])
    # 获取数据集中最优特征所在列
    featValues = [example[bestFeat] for example in dataSet]
    # 采用set集合性质，获取特征的所有的唯一取值
    uniqueVals = set(featValues)
    # 遍历每一个特征取值
    for value in uniqueVals:
        # 采用递归的方法利用该特征对数据集进行分类
        # @bestFeatLabel 分类特征的特征标签值
        # @dataSet 要分类的数据集
        # @bestFeat 分类特征的标称值
        # @value 标称型特征的取值
        # @subLabels 去除分类特征后的子特征标签列表
        myTree[bestFeatLabel][value] = createTree(splitDataSet \
                                                      (dataSet, bestFeat, value), subLabels)
    return myTree



def predictLensesType(filename):
    #打开文本数据
    fr=open(filename)
    #将文本数据的每一个数据行按照tab键分割，并依次存入lenses
    lenses=[inst.strip().split('\t') for inst in fr.readlines()]
    #创建并存入特征标签列表
    lensesLabels=['age','prescript','astigmatic','tearRate']
    #根据继续文件得到的数据集和特征标签列表创建决策树
    lensesTree=createTree(lenses,lensesLabels)
    return lensesTree


#完成决策树的构造后，采用决策树实现具体应用
#@intputTree 构建好的决策树
#@featLabels 特征标签列表
#@testVec 测试实例
def classify(inputTree,featLabels,testVec):
    #找到树的第一个分类特征，或者说根节点'no surfacing'
    #注意python2.x和3.x区别，2.x可写成firstStr=inputTree.keys()[0]
    #而不支持3.x
    firstStr=list(inputTree.keys())[0]
    #从树中得到该分类特征的分支，有0和1
    secondDict=inputTree[firstStr]
    #根据分类特征的索引找到对应的标称型数据值
    #'no surfacing'对应的索引为0
    featIndex=featLabels.index(firstStr)
    #遍历分类特征所有的取值
    for key in secondDict.keys():
        #测试实例的第0个特征取值等于第key个子节点
        if testVec[featIndex]==key:
            #type()函数判断该子节点是否为字典类型
            if type(secondDict[key]).__name__=='dict':
                #子节点为字典类型，则从该分支树开始继续遍历分类
                classLabel=classify(secondDict[key],featLabels,testVec)
            #如果是叶子节点，则返回节点取值
            else: classLabel=secondDict[key]
    return classLabel