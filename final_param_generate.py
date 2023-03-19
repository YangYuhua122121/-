"""
@File : break_yellow_param.py
@Author : 杨与桦
@Time : 2023/03/19 12:05
"""
import pandas as pd
import random

yellow_data = pd.read_csv('./break_yellow_threshold.CSV')
av_data = pd.read_csv('./traffic flow parameter_av.csv')
hv_data = pd.read_csv('./traffic flow parameter_hv.csv')
av_data = av_data[av_data['error'] <= 0.167]  # 去除超出平均值误差的参数组
hv_data = hv_data[hv_data['error'] <= 0.2314]
hv_data.reset_index(drop=True, inplace=True)
av_data.reset_index(drop=True, inplace=True)
yellow_data['proportion'] = (yellow_data['proportion']/100)  # 更改为百分比

yellow_data['hv_num'] = (yellow_data['proportion']*len(hv_data)).round()  # 获取HV闯黄灯参数分配数目
break_yellow_lst = []  # 初始化闯黄灯参数分布列表
for row in yellow_data.index:
    value = yellow_data.iloc[row][0]
    n = int(yellow_data.iloc[row][2])
    a_lst = [value]*n
    break_yellow_lst += a_lst
random.shuffle(break_yellow_lst)  # 随机置乱参数分布
break_yellow_s = pd.Series(break_yellow_lst)  # 转Series

hv_data['jmDriveAfterYellowTime'] = break_yellow_s  # 新增参数列
av_data['jmDriveAfterYellowTime'] = 0

hv_data.to_csv('./final traffic flow parameter_hv.csv')
av_data.to_csv('./final traffic flow parameter_av.csv')
