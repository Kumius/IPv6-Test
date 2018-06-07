# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 21:45:05 2018

@author: Kumius
"""

'''
处理由ipv6.py生成的数据

数据格式为：
[序号，http/ip支持情况（4种，包括时间），是否支持IPV4/6, 建链时间差异，传输速度差异，页面是否有差异]
共26列，例如：
[{0, 0.0 * 5} * 4, 0, 0, 0, 0]
其中，
是否支持IPV4/6 = 0 | 1 | 2，1代表IPV4，2代表IPV6
页面是否有差异，很可能是页面时间、IP地址导致的

制作图例：
1、部署规模；主要是
2、速度
3、差异化


关于是否支持V4，可能是因为墙的缘故，可能V4不通，反而V6能通，但是没法完成传输（比如RESET攻击）
'''


import os
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt



'''
['1', '0', '0.018', '0.0', '0.0', '3.001', '0.0',
      '-1', '0.0', '0.0', '0.0', '0.0', '0.0',
      '0', '0.018', '0.0', '0.0', '3.001', '0.0',
      '-1', '0.0', '0.0', '0.0', '0.0', '0.0',
      '2', '0', '0', '0\n']
'''



def count_v6(filename):
    '''
    返回文件中的网站总数、可访问个数、部署V6的个数
    '''
    cnt_v46 = 0
    cnt_v6 = 0
    file = open(filename)
    for i, line in enumerate(file):
        line = line.split(",")
        ipv_46 = int(line[-4])
        
        if ipv_46 != 0:
            cnt_v46 += 1
        if ipv_46 & 2 == 2:
            cnt_v6 += 1
        
    return i+1, cnt_v46, cnt_v6


def conn_time(filename):
    '''
    返回所有建链时间比例非0的数据
    用于制作CDF图
    '''
    file = open(filename)
    time_ratio = []
    for i, line in enumerate(file):
        line = line.split(",")
        ratio = float(line[-3])
        if ratio != 0 and ratio <= 1:
            time_ratio.append(ratio)
    return time_ratio


def handle_v6(path):
    sum_all = 0
    sum_v46 = 0
    sum_v6 = 0
    for file in os.listdir(path):
        #print(file)
        cnt_all, cnt_v46, cnt_v6 = count_v6(path + file)
        sum_all += cnt_all
        sum_v46 += cnt_v46
        sum_v6 += cnt_v6
        #print(cnt_all, cnt_v46, cnt_v6)
    return sum_all, sum_v46, sum_v6

def handle_speed(path):
    time_ratio = []
    for file in os.listdir(path):
        time_ratio.extend(conn_time(path + file))
    return time_ratio

#print(count_v6(path + "output-1-15366.csv"))

path = "output/"
#sum_all, sum_v46, sum_v6 = handle_v6(path)



def draw_cdf(data, label):
    ecdf = sm.distributions.ECDF(data)
    x = np.linspace(min(data), max(data), 10000)
    y = ecdf(x)
    plt.plot(x, y, label=label)
    
    

time_ratio = handle_speed(path)
draw_cdf(time_ratio, "speed")












