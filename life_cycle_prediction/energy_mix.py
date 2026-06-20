import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA


def consumption_prediction():
    """各省份电力结构预测"""
    # 数据文件
    data_path = r'data\grid\power_consumption.xlsx'
    # 实际年份和预测年份
    year_real = np.arange(2015, 2025)
    year_pre = np.arange(2025, 2051)

    # 读取
    data_all = pd.read_excel(data_path)
    # 从2015预测到2050
    data_output = np.zeros((len(data_all) + 1, len(year_pre) + len(year_real)))
    data_index = np.zeros((len(data_all) + 1, 3)).astype(str)
    data_index[-1] = ''

    ####################################################
    # 用ARIMA效果不是很好，改成用线性

    # 预测总值的增长，后面用于均一化
    power_sum = np.sum(data_all.loc[:, year_real].values, axis=0)
    # 线性预测
    coff = np.polyfit(year_real, power_sum, 1)
    # 预测
    forecast_data = coff[0] * year_pre + coff[1]
    print('总值的相关系数是：%.4f' % np.corrcoef(year_real, power_sum)[0, 1])
    # 合并
    power_sum = np.round(np.hstack((power_sum, forecast_data)), 2)

    # 逐条预测
    base = 0
    for region in ['N', 'NE', 'E', 'C', 'S', 'SW', 'NW']:
        # 选出数据
        data = data_all.loc[data_all['Area'] == region].reset_index(drop=True)
        # 先把所处电网和省份复制进去
        data_index[base:base + len(data), 0] = data['adcode'].values
        data_index[base:base + len(data), 1] = region
        data_index[base:base + len(data), 2] = data['Province'].values
        # 逐个预测
        for i in range(base, base + len(data)):
            data_now = data.loc[i - base, year_real].values.astype(float)

            # 线性预测
            coff = np.polyfit(year_real, data_now, 1)
            # 预测
            forecast_data = coff[0] * year_pre + coff[1]
            print('%s的相关系数是：%.4f' % (data.iloc[i - base, 2], np.corrcoef(year_real, data_now)[0, 1]))

            # plt.plot(year_real, data_now)
            # plt.plot(year_pre, forecastdata)
            # plt.show()

            data_output[i] = np.hstack((data_now, forecast_data))

        base = base + len(data)

    ####################################################

    # ####################################################
    # # ARIMA预测
    #
    # # 预测总值的增长，后面用于均一化
    # power_sum = np.sum(data_all.iloc[:, 2:].values, axis=0)
    # # 使用ARIMA预测，2024-2050
    # model = ARIMA(power_sum, order=(1, 1, 1))
    # model_fit = model.fit()
    # forecast_data = np.round(model_fit.forecast(27), 2)
    # # 合并
    # power_sum = np.hstack((power_sum, forecast_data))
    #
    # base = 0
    # for region in ['N', 'NE', 'E', 'C', 'S', 'SW', 'NW']:
    #     # 选出数据
    #     data = data_all.loc[data_all['Area'] == region].reset_index(drop=True)
    #     # 先把所处电网和省份复制进去
    #     data_index[base:base + len(data), 0] = region
    #     data_index[base:base + len(data), 1] = data['Province'].values
    #     # 逐个预测
    #     for i in range(base, base + len(data)):
    #         data_now = data.loc[i - base, np.arange(2015, 2024)].values.astype(float)
    #         # 使用ARIMA预测，2024-2050
    #         model = ARIMA(data_now, order=(1, 1, 1))
    #         model_fit = model.fit()
    #         forecast_data = np.round(model_fit.forecast(27), 2)
    #
    #         # plt.plot(np.arange(2015, 2024), data_now)
    #         # plt.plot(np.arange(2024, 2036), forecastdata)
    #         # plt.show()
    #
    #         data_output[i] = np.hstack((data_now, forecast_data))
    #
    #     base = base + len(data)
    # ####################################################

    # 要按照预测好的归一化
    data_output = np.round(data_output / np.sum(data_output, axis=0) * power_sum, 2)
    data_output[-1] = power_sum

    # 存储
    df = pd.DataFrame(np.hstack((data_index, data_output)),
                 columns=np.hstack(('adcode', 'Area', 'Province', np.hstack((year_real, year_pre)).astype(str))))
    df[np.hstack((year_real, year_pre)).astype(str)] = df[np.hstack((year_real, year_pre)).astype(str)].astype(float)
    df.to_excel('china_power_consumption.xlsx', index=False)


def energy_mix():
    """预测电力结构"""
    from scipy import interpolate

    data_mix = r'data\grid\energy_mix.xlsx'
    data_power = r'data_output\grid\china_power_consumption.xlsx'
    # 年份
    year_list = np.arange(2015, 2051)
    year_life = np.array([2015, 2020, 2030])
    # 计算顺序
    region_list = [['North', 'N'], ['East ', 'E'], ['Central', 'C'], ['Northeast', 'NE'], ['Northwest', 'NW'],
                   ['Southwest', 'SW'], ['South', 'S']]
    mix_list = ['NG', 'Coal', 'Nuclear', 'Biomass', 'Hydro', 'Wind', 'Solar', 'Others']


    # 读取数据
    data_mix = pd.read_excel(data_mix, sheet_name=None, index_col=[0])
    data_power = pd.read_excel(data_power)

    # # 采用线性的数组
    # line_pairs = [[0, 1], [0, 3],
    #               [1, 1], [1, 7],
    #               [2, 1], [2, 4], [2, 7],
    #               [3, 3], [3, 7],
    #               [4, 0], [4, 1], [4, 3], [4, 7],
    #               [5, 1], [5, 2], [5, 3], [5, 7],
    #               [6, 1], [6, 3], [6, 7]]
    # # 转换为集合以便快速查找
    # pair_set = {(i, j) for i, j in line_pairs}

    # 先计算全生命周期排放，顺序为Coal-fired、NG-fired、Biomass、Nuclear
    lca = data_mix['LCA']
    pol = np.zeros((4, len(year_list)))
    for i in range(4):
        if i != 3:
            coff = interpolate.interp1d(year_life, lca.iloc[:, i], kind='linear', fill_value='extrapolate')
            pol[i] = coff(year_list)
        else:
            pol[i] = np.interp(year_list, year_life, lca.iloc[:, i])

        # # Biomass用线性插值，其他用三次样条
        # if i != 2 :
        #     coff = np.polyfit(year_life, lca.iloc[:, i], 2)
        #     pol[i] = coff[0] * np.square(year_list) + coff[1] * year_list + coff[2]
        # else:
        #     pol[i] = np.interp(year_list, year_life, lca.iloc[:, i])

        # plt.plot(year_list, pol[i])
        # plt.scatter(year_life, lca.iloc[:, i])
        # plt.show()

    pol = np.round(pol, 2)

    # 我们一个地区一个地区来
    for r in range(len(region_list)):
        data = []
        for year in year_life:
            data.append(data_mix[str(year)].loc[mix_list, region_list[r][0]].values *
                        np.sum(data_power.loc[data_power['Area'] == region_list[r][1], str(year)]))
        data = np.array(data).T

        # 插值预测
        power_mix = np.zeros((data.shape[0], len(year_list)))
        for m in range(data.shape[0]):
            # print('正在处理%s的%s，对应编号为(%d, %d)' % (region_list[r][0], mix_list[m], r, m))
            # 创建线性插值函数，允许外推
            coff = interpolate.interp1d(year_life, data[m], kind='linear', fill_value='extrapolate')
            power_mix[m] = coff(year_list)

            # if (r, m) in pair_set:
            #     # 创建线性插值函数，允许外推
            #     coff = interpolate.interp1d(year_life, data[m], kind='linear', fill_value='extrapolate')
            #     power_mix[m] = coff(year_list)
            # else:
            #     # 二次拟合
            #     coff = np.polyfit(year_life, data[m], 2)
            #     power_mix[m] = coff[0] * np.square(year_list) + coff[1] * year_list + coff[2]

            # plt.plot(year_list, power_mix[m])
            # plt.scatter(np.array([2015, 2020, 2030]), data[m])
            # plt.show()

        # 按照预测的总量归一化
        power_mix = power_mix / np.sum(power_mix, axis=0)
        power_mix = np.round(
            power_mix * np.sum(data_power.loc[data_power['Area'] == region_list[r][1], year_list.astype(str)].values,
                               axis=0), 2)
        # 给出与数据对应的索引
        # 创建一个布尔矩阵
        mask = np.array(['Coal', 'NG', 'Biomass', 'Nuclear'])[:, None] == np.array(mix_list)[None, :]  # shape (2, 8)
        # 找到每行中True的位置，即索引
        indices = np.where(mask)[1]
        # 计算每千万时排放
        pol_kwh = np.round(np.sum((power_mix / np.sum(power_mix, axis=0))[indices] * pol, axis=0), 2)

        # 合并数据
        index_list = pd.DataFrame(np.hstack((np.full((len(mix_list) + 1, 1), region_list[r][1]),
                                             np.vstack((np.array(mix_list).reshape((-1, 1)), 'LCA')))),
                                  columns=['Area', 'PowerMix'])
        power_mix = pd.DataFrame(np.vstack((power_mix, pol_kwh)), columns=year_list.astype(str))

        # 存储
        if r == 0:
            df = pd.concat([index_list, power_mix], axis=1)
        else:
            df = pd.concat([df, pd.concat([index_list, power_mix], axis=1)], axis=0)

    # 分别导出
    df.to_excel('energy_mix_prediction.xlsx', index=False)

    pd.DataFrame(np.hstack((np.array(['Coal-fired', 'NG-fired', 'Biomass', 'Nuclear']).reshape((-1, 1)), pol)),
                 columns=np.hstack(('Year', year_list.astype(str)))
                 ).to_excel('lca_prediction.xlsx', index=False)


def energy_mix_map():
    """把数据匹配到地图上"""
    mix = r'data_output\grid\energy_mix_prediction.xlsx'
    locations = r'data_output\grid\china_power_consumption.xlsx'
    map_china = r'..\..\data\adcode\china_map_location_fix.xlsx'


    mix = pd.read_excel(mix)
    locations = pd.read_excel(locations, usecols=['adcode', 'Area']).iloc[:-1].rename(columns={'adcode': 'provcode_amap'})
    map_china = pd.read_excel(map_china, usecols=['adcode_amap', 'provcode_amap'])

    # 先合并县级行政区和地理区划，得到带有地理单元的县级数据
    df_map = pd.merge(map_china, locations, on='provcode_amap', how='left')
    # 香港和澳门采用广东的，台湾就空着
    df_map.loc[df_map['provcode_amap'] == 810000, 'Area'] = 'S'
    df_map.loc[df_map['provcode_amap'] == 820000, 'Area'] = 'S'

    # 取出电力结构
    mix = mix.loc[mix['PowerMix'] == 'LCA'].reset_index(drop=True)[np.hstack(('Area', np.arange(2015, 2051).astype(str)))]

    # 再合并电力结构，台湾就置入0
    df_result = pd.merge(df_map, mix, on='Area', how='left').fillna(0)

    # 导出
    df_result.to_excel('power_emission_map.xlsx', index=False)


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    energy_mix_map()
