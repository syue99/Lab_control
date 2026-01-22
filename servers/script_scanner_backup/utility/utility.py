import datetime as _datetime


def base_path_list():
    """Gets ['', year, month, trunk] list for data vault paths."""
    date = _datetime.datetime.now()

    year = '%04d' % date.year
    month = '%02d' % date.month  # Padded with a zero if one digit
    day = '%02d' % date.day    # Padded with a zero if one digit
    trunk = year + '_' + month + '_' + day

    return ['', year, month, trunk]
