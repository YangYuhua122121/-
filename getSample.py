"""
@File : getSample.py
@Author : 杨与桦
@Time : 2023/03/02 18:18
"""
import random

import pandas as pd


def sample_get(frame_info, trj_type, batch):
    """
获取样本的时间戳、前后车前保险杠位置（一维)、前后车速度、长度信息，并随机选取batch对CF的数据
    :param frame_info: 帧文件路径
    :param trj_type: 后车轨迹类型，包含av与hv两个选项
    :param batch: 生成的样本中含有的cf数量
    :return: 样本信息，具有双行索引（id，step）；其中id为一个浮点数，小数点前表示场景id，后表示车辆id；step表示步数，一步等于0.1秒
    """

    def cf_structure(all_frame_info, cf_type):
        """
    用于将跟驰对的数据构建于同一行

        :param all_frame_info:全数据帧DataFrame
        :param cf_type:定义跟驰对类型，包括av_x, hv_av, hv_hv; 其中前项为后车
        :return:以跟驰对为行数据的DataFrame, 包含：'f_seg', 'f_len', 'f_id', 'f_time', 'f_pos', 'f_speed', 'f_accer'以及l
        """
        #  筛选条件
        c1 = (all_frame_info['local_veh_id'] == all_frame_info['follower_id']) & (all_frame_info['follower_id'] != 0)
        c2 = (all_frame_info['local_veh_id'] == all_frame_info['leader_id']) & (all_frame_info['follower_id'] != 0)
        c3 = (all_frame_info['local_veh_id'] == all_frame_info['follower_id']) & (all_frame_info['follower_id'] == 0)
        c4 = (all_frame_info['local_veh_id'] == all_frame_info['leader_id']) & (all_frame_info['follower_id'] == 0)
        #  分别筛选HV与AV后车的相关数据
        hvf_follower = all_frame_info[c1][['segment_id', 'length', 'follower_id', 'local_time',
                                          'filter_pos', 'filter_speed', 'filter_accer']]
        hvf_leader = all_frame_info[c2][['segment_id', 'length', 'leader_id', 'local_time', 'filter_pos',
                                         'filter_speed', 'filter_accer']]
        avf_follower = all_frame_info[c3][['segment_id', 'length', 'follower_id', 'local_time',
                                          'filter_pos', 'filter_speed', 'filter_accer']]
        avf_leader = all_frame_info[c4][['segment_id', 'length', 'leader_id', 'local_time', 'filter_pos',
                                        'filter_speed', 'filter_accer']]
        #  更改与重置索引
        hvf_follower.columns = ['f_seg', 'f_len', 'f_id', 'f_time', 'f_pos', 'f_speed', 'f_accer']
        hvf_leader.columns = ['l_seg', 'l_len', 'l_id', 'l_time', 'l_pos', 'l_speed', 'l_accer']
        avf_follower.columns = ['f_seg', 'f_len', 'f_id', 'f_time', 'f_pos', 'f_speed', 'f_accer']
        avf_leader.columns = ['l_seg', 'l_len', 'l_id', 'l_time', 'l_pos', 'l_speed', 'l_accer']
        # hvf_follower = hvf_follower[:-1]  # 不知名原因导致的hv后车数据的行数不相等，经核验该剔除方式仅损失四百多条帧数据
        hvf_leader.reset_index(drop=True, inplace=True)
        hvf_follower.reset_index(drop=True, inplace=True)
        avf_leader.reset_index(drop=True, inplace=True)
        avf_follower.reset_index(drop=True, inplace=True)  # 统一行索引
        hvf = pd.concat([hvf_leader, hvf_follower], axis=1)
        avf = pd.concat([avf_leader, avf_follower], axis=1)
        hvf = hvf[(hvf['f_seg'] == hvf['l_seg'])]
        avf = avf[(avf['f_seg'] == avf['l_seg'])]
        if cf_type == 'av_x':
            return avf
        elif cf_type == 'hv_hv':
            return hvf[hvf['l_id'] != 0]
        elif cf_type == 'hv_av':
            return hvf[hvf['l_id'] == 0]

    def pos2head_pos(cf_info):
        cf_info['l_pos'] = cf_info['l_pos']+cf_info['l_len']/2
        cf_info['f_pos'] = cf_info['f_pos']+cf_info['f_len']/2  # 将中心位置坐标更换为车头坐标
        return cf_info

    def ttc_cal(cf_info):
        cf_info['gap'] = cf_info['l_pos']-cf_info['f_pos']-cf_info['l_len']
        cf_info['v_delta'] = cf_info['f_speed']-cf_info['l_speed']
        cf_info['TTC'] = cf_info['gap']/cf_info['v_delta']
        cf_info.loc[cf_info['TTC'] > 30, 'TTC'] = 0
        cf_info.loc[cf_info['TTC'] < 0, 'TTC'] = 0
        return cf_info

    def raw_index_get(seg_veh_info):
        #  获取初始cf索引（由seg_id和veh_id构成）
        indices = []
        for ind in seg_veh_info.index:
            indices.append(ind[:2])  # 获取[f_seg, f_id]
        indices = set(indices)  # 清除同索引
        indices = list(indices)
        return indices

    def a_cf_index_renew(a_cf_seg_veh_info, a_cf_seg_veh_id):
        # 用于更新某个cf数据块的索引标签
        # 有唯一指定的id标记某cf数据块，其格式为seg_id.veh_id
        # 输出数据的列索引包括cf索引和行数标号
        seg = int(a_cf_seg_veh_id[0])
        veh = a_cf_seg_veh_id[1]/100
        new_id = seg+veh
        multi_index = pd.MultiIndex.from_product([[new_id], range(len(a_cf_seg_veh_info))])
        df = pd.DataFrame(a_cf_seg_veh_info.values, index=multi_index)
        return df

    def index_renew(seg_veh_info, seg_veh_index):
        first = True
        res = None
        for idx in seg_veh_index:
            if first:  # 初始化DataFrame
                res = a_cf_index_renew(seg_veh_info.loc[idx], idx)
                first = False
            else:  # 构建DataFrame
                res = pd.concat([res, a_cf_index_renew(seg_veh_info.loc[idx], idx)], axis=0)
        res.columns = ['f_time', 'f_pos', 'l_pos', 'f_speed', 'l_speed', 'f_len', 'l_len', 'f_accer', 'gap']
        return res

    def new_index_get(sv_info):
        seg_veh_indices = []
        for idx in sv_info.index:
            seg_veh_indices.append(idx[0])
        seg_veh_indices = set(seg_veh_indices)
        return list(seg_veh_indices)

    def short_data_remove(sv_info, cf_index):
        threshold_size = 190  # 指定输出数据集中单个cf对的帧数最小值
        out_indices = []  # 定义待去除cf对的编号列表
        for idx in cf_index:
            if len(sv_info.loc[idx]) < threshold_size:
                out_indices.append(idx)
        sv_info.drop(index=out_indices, inplace=True, level=0)
        return sv_info

    def final_remove(sv_info, cf_index):
        threshold_frame = 20  # 指定符合条件的帧数阈值
        out_indices = []
        for idx in cf_index:
            a_cf_obj_info = sv_info.loc[idx]['f_speed']
            b_cf_obj_info = sv_info.loc[idx]['gap']
            c_cf_obj_info = sv_info.loc[idx]['f_accer']
            # 存在减速停车事件
            if len(a_cf_obj_info[a_cf_obj_info < 0.1]) <= threshold_frame:
                out_indices.append(idx)
            # 忽略不合理的最小停车间距
            if len(b_cf_obj_info[b_cf_obj_info < 1]) >= 1:
                out_indices.append(idx)
            # 加速过程较短
            if len(c_cf_obj_info[c_cf_obj_info > 1]) >= 100:
                out_indices.append(idx)
        sv_info.drop(index=out_indices, inplace=True, level=0)
        return sv_info

    def get_min_gap(sv_info, cf_index):
        for idx in cf_index:
            c = sv_info.loc[idx]['gap'].min()
            sv_info.loc[idx, 'gap'] = c  # 将gap更换为min_gap
        return sv_info

    def get_batch(sv_info, batch_size):
        all_cf_index = new_index_get(sv_info)
        barch_index = random.sample(all_cf_index, batch_size)
        return sv_info.loc[barch_index, :]

    def process_packing(cf_info):
        cf_info = pos2head_pos(cf_info)
        cf_info = ttc_cal(cf_info)
        seg_veh_info = cf_info.groupby(['f_seg', 'f_id', 'f_time'])[['f_time', 'f_pos', 'l_pos', 'f_speed', 'l_speed',
                                                                     'f_len', 'l_len', 'f_accer', 'gap']].mean()
        raw_index = raw_index_get(seg_veh_info)
        sv_info = index_renew(seg_veh_info, raw_index)
        sv_index = new_index_get(sv_info)
        long_sv_data = short_data_remove(sv_info, sv_index)
        long_sv_index = new_index_get(long_sv_data)
        final_data = final_remove(long_sv_data, long_sv_index)
        final_index = new_index_get(final_data)
        final_data = get_min_gap(final_data, final_index)
        result = get_batch(final_data, batch)
        return result

    if trj_type == 'av':
        av_x = cf_structure(frame_info, 'av_x')
        return process_packing(av_x)
    elif trj_type == 'hv':
        hv_x = cf_structure(frame_info, 'hv_hv')
        return process_packing(hv_x)


def index_get(sv_info):
    """
用于获取数据的cf分类索引
    :param sv_info: 帧数据
    :return: cf分类索引的列表
    """
    seg_veh_indices = []
    for idx in sv_info.index:
        seg_veh_indices.append(idx)
    seg_veh_indices = set(seg_veh_indices)
    return list(seg_veh_indices)


if __name__ == '__main__':
    path = './all_seg_paired_cf_trj_final_with_large_vehicle.csv'
    hv_info = pd.read_csv(path)
    hv_info = sample_get(hv_info, 'av', 90)
    hv_info.to_csv('./processed_data_sample.csv')
