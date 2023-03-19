"""
@File : ga2sumo.py
@Author : 杨与桦
@Time : 2023/03/02 18:12
"""
import pandas as pd
import traci
from sys import stdout
import getSample
from sko.GA import GA
import numpy as np
import matplotlib.pyplot as plt

batch = 90  # 定义了单次并行的cf数量,更改该值时，应同时更改rou_net_writer.py中的相同参数
n = 5  # 定义了待标定的参数个数.更改参数时，应注意：目标函数和验证函数中的参数定义与vtype赋值、参数上下界的修改、新增df列名
varify = 30  # 定义用于模型验证的数据量（帧）
b = [0.96, 4.27]
a = [0.77, 4.39]
tau = [1.55, 4.75]
reaction_time = [0.1, 2]


# 使用TTC误差
# 用于优化与验证的误差函数，指定mode为opt或varify，可分别用于优化与验证。
# def obj_function(xl, xf, xt, sl, sf, st, ll, mode):
#     if (sf-sl > 0) and (st-sl > 0):  # TTC计算要求速度差为正
#         sim_ttc = (xl-xf-ll)/(sf-sl)
#         true_ttc = (xl-xt-ll)/(st-sl)
#         ttc_cal = True
#     else:
#         sim_ttc = 0
#         true_ttc = 0
#         ttc_cal = False
#     trj_error = abs(xf - xt)  # 轨迹真实误差
#     ttc_error = abs(sim_ttc-true_ttc)  # TTC误差
#     if mode == 'varify':
#         print(sim_ttc, true_ttc, ttc_cal)
#     if mode == 'opt':
#         if ttc_cal and (sim_ttc < 30) and (true_ttc < 30):
#             return 30*ttc_error+trj_error
#         else:
#             return trj_error
#     else:
#         if ttc_cal and (sim_ttc < 30) and (true_ttc < 30):
#             return ttc_error
#         else:
#             return 0  # 无效的TTC将忽略


# 使用速度误差
# def obj_function(vf, vt):
#     abs_error = abs(vf-vt)
#     return abs_error

# 使用轨迹误差
# def obj_function(xf, xt):
#     abs_error = abs(xf-xt)
#     return abs_error

# 使用车头间距误差
def obj_function(xl, xf, xt):
    t_headway = xl-xt
    s_headway = xl-xf
    return abs(t_headway-s_headway)/t_headway


# sumo运行的主函数，包括对前车真实轨迹的输入与后车仿真轨迹的输出
# mode参数指定用于ga还是用于验证('opt', 'varify')
def run(cf_info_batch, cf_index_barch, mode):
    overall_error = np.array([[0]*batch])
    xfl = []
    xtl = []
    # l_length = None
    # 根据mode选择起始条件与终止条件
    if mode == 'opt':
        step = 0
        init1 = 0
        init2 = 1
        stop = 190-varify
    else:
        step = 190-varify
        init1 = 190-varify
        init2 = 191-varify
        # step = 0
        # init1 = 0
        # init2 = 1
        stop = 189

    while traci.simulation.getMinExpectedNumber() > 0:
        step_overall_error = []  # 初始化某一步骤下误差的收集列表
        traci.simulationStep()
        if step == init1:
            for i, cf_id in enumerate(cf_index_barch):  # 次序索引用于vehicle的命名
                a_cf_info = cf_info_batch.loc[cf_id]
                init_info = a_cf_info.iloc[init2]  # 获取初始信息（第一步）
                traci.vehicle.setLength(f'L{i}', init_info['l_len'])  # 设置前车长度
                traci.vehicle.setLength(f'F{i}', init_info['f_len'])  # 设置后车长度
                traci.vehicle.setMinGap(f'F{i}', init_info['gap'])  # 设置停车最小间距
                # l_length = init_info['l_len']
                y = traci.vehicle.getPosition(f'L{i}')[1]
                traci.vehicle.moveToXY(f'L{i}', f'E{i}', -1, x=init_info['l_pos'], y=y)
                traci.vehicle.moveToXY(f'F{i}', f'E{i}', -1, x=init_info['f_pos'], y=y)  # 设置初始位置(下一步)
        elif step == init2:
            for i, cf_id in enumerate(cf_index_barch):  # 次序索引用于vehicle的命名
                a_cf_info = cf_info_batch.loc[cf_id]
                init_info = a_cf_info.iloc[init2]
                y = traci.vehicle.getPosition(f'L{i}')[1]
                traci.vehicle.setPreviousSpeed(f'F{i}', max(0, init_info['f_speed']))  # 设置后车初速度
                traci.vehicle.setPreviousSpeed(f'L{i}', max(0, init_info['l_speed']))  # 设置前车初速度
                traci.vehicle.moveToXY(f'L{i}', 'E0', '-1', x=a_cf_info.iloc[init2+1]['l_pos'], y=y)  # 控制前车轨迹
            # 仿真进行
        elif step < stop:  # 正式运行
            for i, cf_id in enumerate(cf_index_barch):  # 次序索引用于vehicle的命名
                a_cf_info = cf_info_batch.loc[cf_id]
                y = traci.vehicle.getPosition(f'L{i}')[1]
                traci.vehicle.moveToXY(f'L{i}', f'E{i}', -1, x=a_cf_info.iloc[step+1]['l_pos'], y=y)  # 控制下一步的前车轨迹
                traci.vehicle.setPreviousSpeed(f'L{i}', max(0, a_cf_info.iloc[step]['l_speed']))  # 控制前车速度
                pos_l = a_cf_info.iloc[step]['l_pos']  # 获取前车轨迹
                pos_f = traci.vehicle.getPosition(f'F{i}')[0]  # 获取后车仿真轨迹
                pos_t = a_cf_info.iloc[step]['f_pos']  # 获取后车真实轨迹
                # sp_l = a_cf_info.iloc[step]['l_speed']  # 获取前车速度
                # sp_f = traci.vehicle.getSpeed(f'F{i}')  # 获取后车仿真速度
                # sp_t = a_cf_info.iloc[step]['f_speed']  # 获取后车真实速度
                # a_cf_step_error = obj_function(pos_l, pos_f, pos_t, sp_l, sp_f, sp_t, l_length, mode)  # 获取该步骤误差
                a_cf_step_error = obj_function(pos_l, pos_f, pos_t)
                step_overall_error.append(a_cf_step_error)
        else:  # 训练结束
            traci.close()
            stdout.flush()  # 关闭仿真
            return overall_error
        if step > init2:  # 初始化完成，开始统计
            # step_overall_error.append(0)  # 防止remove报错
            # step_overall_error = set(step_overall_error)
            # step_overall_error.remove(0)
            # if len(step_overall_error) != 0:  # 筛除无效ttc误差列表
            step_overall_error_array = np.array([step_overall_error])
            overall_error = np.concatenate([overall_error, step_overall_error_array], axis=0)
        step += 1


#  优化参数为一矩阵，在GA中转换为的一维向量
def ga_function(x):
    traci.start(['sumo', '-c', './varify.sumocfg'])
    global error_distribution
    # 设置参数，并将其赋值至对应的车辆上
    for value in range(batch):
        exec(f'a{value} = {x[n*value]}')
        exec(f'fb{value} = {x[n*value+1]}')
        exec(f'tau{value} = {x[n*value+2]}')
        exec(f'lb{value} = {x[n*value+3]}')
        exec(f'as{value} = {x[n*value+4]}')
        traci.vehicle.setAccel(f'F{value}', eval(f'a{value}'))
        traci.vehicle.setDecel(f'F{value}', eval(f'fb{value}'))
        traci.vehicle.setTau(f'F{value}', eval(f'tau{value}'))
        traci.vehicle.setDecel(f'L{value}', eval(f'lb{value}'))
        traci.vehicle.setActionStepLength(f'F{value}', eval(f'as{value}'))
    """
    各轨迹的目标函数相加得到系统目标函数，由于各轨迹相互独立，系统取到最优值时，各轨迹也同时取到最优值
    """
    overall_error = run(hv_info, hv_index, 'opt')
    mean_error = np.mean(overall_error)  # 获取轨迹误差
    error_distribution.append(mean_error)
    return mean_error


# 验证参数在未知数据集中的效果，输入参数应为一维向量
def param_varify(cf_info_batch, cf_index_batch, x):
    traci.start(['sumo', '-c', './varify.sumocfg'])
    # 设置参数，并将其赋值至对应的车辆上
    for value in range(batch):
        exec(f'a{value} = {x[n * value]}')
        exec(f'fb{value} = {x[n * value + 1]}')
        exec(f'tau{value} = {x[n * value + 2]}')
        exec(f'lb{value} = {x[n * value + 3]}')
        exec(f'as{value} = {x[n * value + 4]}')
        traci.vehicle.setAccel(f'F{value}', eval(f'a{value}'))
        traci.vehicle.setDecel(f'F{value}', eval(f'fb{value}'))
        traci.vehicle.setTau(f'F{value}', eval(f'tau{value}'))
        traci.vehicle.setDecel(f'L{value}', eval(f'lb{value}'))
        traci.vehicle.setActionStepLength(f'F{value}', eval(f'as{value}'))
    overall_error = run(cf_info_batch, cf_index_batch, 'varify')
    error_mean = np.mean(overall_error)
    error_std = np.std(overall_error)
    print('验证中，误差均值与方差：', error_mean, error_std)  # 输出每个后车在验证集中平均误差的均值与方差
    return overall_error


if __name__ == "__main__":
    path = './processed_data_sample.csv'
    error_distribution = []
    hv_info = pd.read_csv(path, index_col=0)
    hv_index = getSample.index_get(hv_info)
    lb = [a[0], b[0], tau[0], b[0], reaction_time[0]]*batch
    ub = [a[1], b[1], tau[1], b[1], reaction_time[1]]*batch
    ga = GA(func=ga_function, n_dim=n * batch, size_pop=10, max_iter=15, lb=lb, ub=ub)
    ga.run()
    param_matrix = np.reshape(ga.best_x, (batch, n))  # 获取最佳参数的矩阵

    param_df = pd.DataFrame(param_matrix, columns=['Accel', 'Decel', 'tau', 'lb', 'actionStepLength'])
    plt.plot(error_distribution)
    plt.show()
    error_array = param_varify(hv_info, hv_index, ga.best_x)
    print('优化后的最优值为', ga.best_y)

    hv_info.reset_index(level=0, inplace=True, names='id')  # 获取minGap参数
    min_gap_param = hv_info.groupby('id')['gap'].mean().values
    min_gap_param = pd.Series(min_gap_param, name='minGap')
    error_col = np.mean(error_array.T, axis=1)
    error_col = pd.Series(error_col, name='error')
    param_df = pd.concat([param_df, min_gap_param, error_col], axis=1)

    param_df.to_csv('./traffic flow parameter_av.csv')  # 保存参数
