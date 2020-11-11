def usn_generator(clg_code='1cr', batch='16', dept='cs', file_=None, limit=300):
    if not file_:
        for number in range(1, limit):
            change_section = yield clg_code + batch + dept + str(number).zfill(3)
            if change_section is True:
                break
        dip = batch[0] + str(int(batch[1]) + 1)  # change
        for number in range(400, 400 + limit):
            change_section = yield clg_code + dip + dept + str(number).zfill(3)
            if change_section is True:
                break
    else:
        try:
            fh = open(file_, 'r')
            res = fh.readline()
            while res != '':
                yield res.strip().lower()
                res = fh.readline()
            raise Exception('Done reading file')
        except:
            raise Exception('error reading from file!!')
