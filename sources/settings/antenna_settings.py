#yapf: disable
span_option = [
    {'key': 'sometime', 'text': ''},
    {'key': 'priority', 'text': '優先'},
    {'key': 'once', 'text': '一度'},
    {'key': 'daily', 'text': '毎日'},
    {'key': 'w_mon', 'text': '月曜'},
    {'key': 'w_tue', 'text': '火曜'},
    {'key': 'w_wed', 'text': '水曜'},
    {'key': 'w_thu', 'text': '木曜'},
    {'key': 'w_fri', 'text': '金曜'},
    {'key': 'w_sat', 'text': '土曜'},
    {'key': 'w_sun', 'text': '日曜'},
    {'key': 'every_1d', 'text': '1日'},
    {'key': 'every_2d', 'text': '2日'},
    {'key': 'every_3d', 'text': '3日'},
    {'key': 'every_10d', 'text': '10日'},
    {'key': 'complete', 'text': '完了'}
]

span_sort_score = {
    'daily': '01',
    'w_mon': '02',
    'w_tue': '02',
    'w_wed': '02',
    'w_thu': '02',
    'w_fri': '02',
    'w_sat': '02',
    'w_sun': '02',
    'priority': '03',
    'once': '04',
    'every_1d': '05',
    'every_2d': '06',
    'every_3d': '07',
    'every_10d': '08',
    'sometime': '09',
    'complete': '10'
}

span_to_weekday = {
    'w_mon': 0,
    'w_tue': 1,
    'w_wed': 2,
    'w_thu': 3,
    'w_fri': 4,
    'w_sat': 5,
    'w_sun': 6,
}