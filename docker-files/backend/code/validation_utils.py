def validateData(data):
    it = iter(data)
    the_len = len(next(it))
    if not all(len(l) == the_len for l in it):
        raise ValueError('Not all lists have same length!')
    if the_len <= 1 or len(data) <= 1:
        raise ValueError('Not enough data provided!')
    for l in data[1:]:
        for element in l[1:]:
            if element not in ["0", "1"]:
                raise ValueError('Only 0 or 1 allowed!')