"""
@File : rou_net_writer.py
@Author : 杨与桦
@Time : 2023/03/02 18:21
"""
from lxml import etree
import os

batch_size = 2  # 并行cf数


# 路网生成
class NetFile:
    def __init__(self):
        self.notes = etree.Element('nodes')
        self.edges = etree.Element('edges')

    # 生成单条道路起讫点的xml格式
    def nodes_generate(self, road_id, y):
        start_attrib = {'id': 'OJ'+road_id, 'x': '0', 'y': y, 'type': 'priority'}
        end_attrib = {'id': 'EJ'+road_id, 'x': '1000', 'y': y, 'type': 'priority'}
        etree.SubElement(self.notes, 'node', attrib=start_attrib)
        etree.SubElement(self.notes, 'node', attrib=end_attrib)

    # 生成单条道路的xml格式
    def edges_generate(self, cf_id):
        attrib = {'id': 'E'+cf_id, 'from': 'OJ'+cf_id, 'to': 'EJ'+cf_id, 'numLanes': '1', 'speed': '35'}
        etree.SubElement(self.edges, 'edge', attrib=attrib)

    # 将全部点与路写入xml文件
    def write_in(self):
        notes_text = etree.tostring(self.notes, encoding='utf-8', pretty_print=True)
        edges_text = etree.tostring(self.edges, encoding='utf-8', pretty_print=True)
        with open('./varify_notes.nod.xml', 'w', encoding='utf-8') as f:
            f.write(notes_text.decode('utf-8'))
        with open('./varify_edges.edg.xml', 'w', encoding='utf-8') as f:
            f.write(edges_text.decode('utf-8'))


# 路由生成
class RouFile:
    def __init__(self, vtype):
        """
        :param vtype: 输入'av'时构造AV后车，输入'hv'时构造HV后车
        """
        self.routes = etree.Element('routes')
        self.vtype = vtype

    # 生成单个cf对前后车的车辆类型
    def vtype_generate(self, cf_id):
        if self.vtype == 'hv':
            min_gap = '2.98'
            length = '4.7'  # 可变值
        else:
            min_gap = '5.38'
            length = '5.18'
        follower_attrib = {'id': 'FT'+cf_id, 'minGap': min_gap, 'length': length, 'sigma': '0'}
        etree.SubElement(self.routes, 'vType', attrib={'id': 'LT'+cf_id})
        etree.SubElement(self.routes, 'vType', attrib=follower_attrib)

    # 生成单个cf对的运行路线
    def route_generate(self, cf_id):
        etree.SubElement(self.routes, 'route', attrib={'id': 'R'+cf_id, 'edges': 'E'+cf_id})

    # 生成单个cf对的具体车辆
    def vehicle_generate(self, cf_id):
        leader = {'id': 'L'+cf_id, 'route': 'R'+cf_id, 'type': 'LT'+cf_id, 'depart': '0'}
        follower = {'id': 'F'+cf_id, 'route': 'R'+cf_id, 'type': 'FT'+cf_id, 'depart': '0'}
        etree.SubElement(self.routes, 'vehicle', attrib=leader)
        etree.SubElement(self.routes, 'vehicle', attrib=follower)

    # 将以上信息写入xml文件
    def write_in(self):
        text = etree.tostring(self.routes, encoding='utf-8', pretty_print=True)
        with open('./varify_routes.rou.xml', 'w', encoding='utf-8') as f:
            f.write(text.decode('utf-8'))


def renew_sumo_xml(batch):
    """
更新xml文件与sumocfg文件
    :param batch: 单次并行的cf数
    """
    network = NetFile()
    route = RouFile('hv')
    # i为cf编号，作为某一cf对的唯一编号，从0至50
    for i in range(batch):
        network.nodes_generate(str(i), str(10 * i))
        network.edges_generate(str(i))
        route.vtype_generate(str(i))
        route.route_generate(str(i))
        route.vehicle_generate(str(i))
    network.write_in()
    route.write_in()
    cmd = 'netconvert--node-files=varify_notes.nod.xml--edge' \
          '-files=varify_edges.edg.xml--output-file=varify_network.net.xml'  # 生成net.xml的命令
    os.system(cmd)


if __name__ == '__main__':
    renew_sumo_xml(batch_size)
