import numpy as np
import pandas as pd
from scipy import interpolate
import matplotlib.pyplot as plt


def material():
    """对于材料碳排进行预测"""
    # 由于数据量很少，我们直接手动输入了
    # 柴油 g/MJ
    diesel_wwt = np.array([15.6, 14.8, 13.1])
    diesel_ttw = 74.3
    # 其他材料
    copper = np.array([5.7, 5.1, 3.7])
    wrought_al = np.array([15.6, 14.1, 10])
    steel = np.array([2.2, 2.2, 1.8])
    # 年份
    year_list = np.arange(2015, 2051)
    year_life = np.array([2015, 2020, 2030])

    # 柴油
    coff = interpolate.interp1d(year_life, diesel_wwt, kind='linear', fill_value='extrapolate')
    diesel_wwt = coff(year_list)
    diesel = diesel_wwt + diesel_ttw

    # 铜
    copper_new = np.interp(year_list, year_life, copper)

    # 铝
    al_new = np.interp(year_list, year_life, wrought_al)

    # 钢
    steel_new = np.interp(year_list, year_life, steel)

    # 合并数据
    index_list = pd.DataFrame(np.array(['Diesel_WWT', 'Diesel', 'Copper', 'Al', 'Steel']).reshape((-1, 1)),
                              columns=['Material'])
    emission = pd.DataFrame(np.vstack((diesel_wwt, diesel, copper_new, al_new, steel_new)),
                            columns=year_list.astype(str))

    # 存储
    df = pd.concat([index_list, emission], axis=1)
    df.to_excel('material_wtw.xlsx', index=False)


def battery_capacity():
    """电池相关内容预测"""
    # 由于数据量很少，我们直接手动输入了
    battery_density = np.array([[103, 148, 259], [103, 130, 202]])
    battery_emission =np.array([[158, 111, 58], [83.5, 64, 35]])
    # 年份
    year_list = np.arange(2015, 2051)
    year_life = np.array([2015, 2020, 2030])

    density = []
    emission = []
    for i in range(2):
        density.append(np.interp(year_list, year_life, battery_density[i]))
        emission.append(np.interp(year_list, year_life, battery_emission[i]))

    density = np.array(density)
    emission = np.array(emission)

    return year_list, density, emission


def battery_price():
    """电池价格"""
    # 实际的国内价值
    year_china = np.array([2025.5, 2025, 2024.5, 2024, 2023.5]) - 1
    price_china = np.array([[1724.75, 1725.55, 1769.78, 1764.71, 1768.05],
                            [1313.77, 1358.83, 1375.03, 1489.22, 1380.51],
                            [1538.83, 1574.02, 1604.92, 1644.36, 1623.63]])
    # 实际的国际价值
    year_inter = np.arange(2018, 2025)
    price_inter = np.array([218, 189, 165, 155, 166, 144, 115])
    ex_rate = np.array([661.7423868, 689.8456557, 689.7628807, 645.1504938, 672.6076033, 704.6747934, 712.1679012]) / 100
    # 预测年份
    year_list = np.arange(2018, 2051)

    # 我们用国际价值的缩放来作为新的缩放
    price_inter_yuan = price_inter * ex_rate
    rate_china = price_china[-1, year_china == 2023] / price_china[-1, year_china == 2024]

    # 逆向缩放
    rate_inter = price_inter_yuan[year_inter == 2023] / price_inter_yuan[year_inter == 2024]
    rate = (rate_china - 1) / (rate_inter - 1)

    price_new = (price_inter_yuan - price_inter_yuan[-1]) * rate + price_inter_yuan[-1]
    price_new = price_new / price_inter_yuan[-1] * price_china[-1, year_china == 2024]

    # 创建导出
    price_out = -np.ones((3, len(year_list)))
    price_out[-1, np.isin(year_list, year_inter)] = price_new

    # 对于2025、2026采用线性插值，之后保持不变
    price_out[-1, year_list == 2025] = price_out[-1, year_list == 2024] - 2 * (price_out[-1, year_list == 2024] -
                                                                       price_china[-1, year_china == 2024.5])
    price_out[-1, year_list >= 2026] = 2 * price_out[-1, year_list == 2025] - price_out[-1, year_list == 2024]
    price_out = np.round(price_out, 2)

    # 计算分配比例
    rate = -np.ones((2, len(year_list)))
    rate[0, year_list >= 2025] = price_china[0, year_china == 2024.5] / price_china[-1, year_china == 2024.5]
    rate[1, year_list >= 2025] = price_china[1, year_china == 2024.5] / price_china[-1, year_china == 2024.5]
    rate[0, year_list <= 2022] = price_china[0, year_china == 2022.5] / price_china[-1, year_china == 2022.5]
    rate[1, year_list <= 2022] = price_china[1, year_china == 2022.5] / price_china[-1, year_china == 2022.5]

    rate[0, year_list == 2024] = price_china[0, year_china == 2024] / price_china[-1, year_china == 2024]
    rate[1, year_list == 2024] = price_china[1, year_china == 2024] / price_china[-1, year_china == 2024]
    rate[0, year_list == 2023] = price_china[0, year_china == 2023] / price_china[-1, year_china == 2023]
    rate[1, year_list == 2023] = price_china[1, year_china == 2023] / price_china[-1, year_china == 2023]

    price_out[[0, 1]] = np.round(price_out[-1] * rate, 2)

    return year_list, price_out


def battery():
    """合并导出"""
    year_list_ca, density, emission = battery_capacity()
    year_list_pr, price_out = battery_price()

    index_list = pd.DataFrame(np.array(['density_ncm', 'density_lfp', 'emission_ncm', 'emission_lfp',
                                        'price_ncm', 'price_lfp', 'price_total']).reshape((-1, 1)), columns=[''])

    data_out = pd.DataFrame(np.vstack((density, emission,
                                       np.hstack((-np.ones((price_out.shape[0], len(year_list_ca) - len(year_list_pr))),
                                                  price_out)))),
                            columns=year_list_ca.astype(str))

    # 存储
    df = pd.concat([index_list, data_out], axis=1)
    df.to_excel('battery.xlsx', index=False)


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    battery()
