import numpy as np
import pandas as pd
from scipy import interpolate


def truck_station():
    """预测重卡数量、加油站数量和排放变化"""
    data_path = r'data\truck_station\truck_station.xlsx'
    # 预测年份
    year_list = np.arange(2018, 2051)

    # 读取数据
    data = pd.read_excel(data_path, index_col=[0])
    # 创建导出
    data_output = np.zeros((3, len(year_list)))

    # 处理车辆数据
    hdt = data.loc[~np.isnan(data['hdt']), 'hdt']
    year = np.array(hdt.index)

    # 对于货车采用差值预测
    coff = interpolate.interp1d(year, hdt, kind='linear', fill_value='extrapolate')
    data_output[0] = np.round(coff(year_list), 2)

    # 对于加油站和排放，采用货车的比例（因为加油站的减少不仅仅是因为货车的减少，也包括电车的应用，但是这不表示加油站的需求不在了
    station = data.loc[~np.isnan(data['gas_station']), 'gas_station']
    year = np.array(station.index)
    year_max = np.array(station.index)[-1]

    station_pre = data_output[0, np.where(year_list == year_max)[0][0]:]
    station_pre = station.iloc[-1] * station_pre / np.max(station_pre)
    # 存储
    data_output[1, :year_max - year_list[0] + 1] = station[np.where(year == year_list[0])[0][0]:]
    data_output[1, year_max - year_list[0]:] = np.round(station_pre, 2)

    # 同理对排放
    emission = data.loc[~np.isnan(data['truck_emission']), 'truck_emission']
    year = np.array(emission.index)
    year_max = np.array(emission.index)[-1]

    emission_pre = data_output[0, np.where(year_list == year_max)[0][0]:]
    emission_pre = emission.iloc[-1] * emission_pre / np.max(emission_pre)
    # 存储
    data_output[2, :year_max - year_list[0] + 1] = emission[np.where(year == year_list[0])[0][0]:]
    data_output[2, year_max - year_list[0]:] = np.round(emission_pre, 2)

    # 导出
    index_list = pd.DataFrame(np.array(['hdt', 'gas_station', 'truck_emission']).reshape((-1, 1)), columns=[''])
    data_output = pd.DataFrame(data_output, columns=year_list.astype(str))
    df = pd.concat([index_list, data_output], axis=1)
    df.to_excel('truck_station_prediction.xlsx', index=False)


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    truck_station()
