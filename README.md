# code-for-competition
该存储库用于展示课题所用的代码,主要是车辆模型标定的代码，其中：  
- getSample.py用于将Waymo的原始跟驰对数据进行重构、筛选，以获取本项目所期望的数据格式  
- rou_net_writer.py可以自动编写模型标定、验证所需的SUMO路网与车流文件，文件构造与车辆标定相适应
- ga_with_sumo.py可以接受getSample输出的数据，借助TraCI以SUMO为平台，对跟驰模型进行标定、验证。其中标定采用了遗传算法  
- final traffic flow parameter_iv.csv是final_param_generate.py的生成文件，分别为HV与AV的全部相关参数
- vtype_writer.py可以接受HV与AV的全部参数，并生成SUMO所需的<vType>格式，用于rou文件的编写  
--- 
- test2_50%_low.rou.xml和test2.net.xml分别为车流与路网文件，用于SUMO仿真，这里只展示了其中某次试验所用的仿真文件
