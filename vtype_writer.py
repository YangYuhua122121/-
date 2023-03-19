"""
@File : vtype_writer.py
@Author : 杨与桦
@Time : 2023/03/19 14:16
"""
from lxml import etree
import pandas as pd


# 车辆类型生成
class VtypeFile:
    def __init__(self, mode):
        self.routes = etree.Element('routes')
        self.mode = mode

    # 生成单个cf对前后车的车辆类型
    def vtype_generate(self, cf_id, param_s):
        if self.mode == 'hv':
            sigma = '0.5'
            length = '4.7'
            impatience = '0.7'
        else:
            sigma = '0'
            length = '5.18'
            impatience = '0'
        a = str(param_s['Accel'].round(2))
        b = str(param_s['Decel'].round(2))
        t = str(param_s['tau'].round(2))
        at = str(param_s['actionStepLength'].round(2))
        m = str(param_s['minGap'].round(2))
        y = str(param_s['jmDriveAfterYellowTime'])
        follower_attrib = {'id': f'{self.mode}{cf_id}',
                           'accel': a,
                           'decel': b,
                           'tau': t,
                           'minGap': m,
                           'actionStepLength': at,
                           'length': length,
                           'sigma': sigma,
                           'jmDriveAfterYellowTime': y,
                           'impatience': impatience}
        etree.SubElement(self.routes, 'vType', attrib=follower_attrib)

    # 将以上信息写入xml文件
    def write_in(self, md):
        text = etree.tostring(self.routes, encoding='utf-8', pretty_print=True)
        with open(f'./vtype of {md}.rou.xml', 'w', encoding='utf-8') as f:
            f.write(text.decode('utf-8'))


def renew_sumo_xml(m, param_df: pd.DataFrame):
    # m可选择av或hv
    vt = VtypeFile(m)
    for i in param_df.index:
        s = param_df.iloc[i]
        vt.vtype_generate(i, s)
    vt.write_in(m)


if __name__ == '__main__':
    av_path = './final traffic flow parameter_av.csv'
    hv_path = './final traffic flow parameter_hv.csv'
    av_info = pd.read_csv(av_path)
    hv_info = pd.read_csv(hv_path)
    renew_sumo_xml('hv', hv_info)
    renew_sumo_xml('av', av_info)
