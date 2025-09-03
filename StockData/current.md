行情数据查询函数（免费）
current - 查询当前行情快照
查询当前行情快照

函数原型：

current(symbols, fields='', include_call_auction=False)
 
    
参数：

参数名	类型	说明
symbols	str or list	查询代码，如有多个代码, 中间用 , (英文逗号) 隔开, 也支持 ['symbol1', 'symbol2'] 这种列表格式 ，使用参考symbol
fields	str	查询字段, 默认所有字段 具体字段见:tick 对象
include_call_auction	bool	是否支持集合竞价(9:15-9:25)取数，True为支持，False为不支持，默认为False
返回值：

list[dict]

示例：

current_data = current(symbols='SZSE.000001')
 
    
输出：

[{'symbol': 'SZSE.000001', 'open': 16.200000762939453, 'high': 16.920000076293945, 'low': 16.149999618530273, 'price': 16.559999465942383, 'quotes': [{'bid_p': 16.549999237060547, 'bid_v': 209200, 'ask_p': 16.559999465942383, 'ask_v': 296455}, {'bid_p': 16.540000915527344, 'bid_v': 188900, 'ask_p': 16.56999969482422, 'ask_v': 374405}, {'bid_p': 16.530000686645508, 'bid_v': 44900, 'ask_p': 16.579999923706055, 'ask_v': 187220}, {'bid_p': 16.520000457763672, 'bid_v': 20800, 'ask_p': 16.59000015258789, 'ask_v': 102622}, {'bid_p': 16.510000228881836, 'bid_v': 37700, 'ask_p': 16.600000381469727, 'ask_v': 337002}], 'cum_volume': 160006232, 'cum_amount': 2654379585.66, 'last_amount': 14153832.0, 'last_volume': 854700, 'trade_type': 7, 'created_at': datetime.datetime(2020, 10, 15, 15, 0, 3, tzinfo=tzfile('PRC'))}]
 
注意：

1. 若输入包含无效标的代码，则返回的列表只包含有效标的代码对应的dict

2. 若输入代码正确，但查询字段中包括错误字段，返回的列表仍包含对应数量的dict，但每个dict中除有效字段外，其他字段的值均为空字符串/0