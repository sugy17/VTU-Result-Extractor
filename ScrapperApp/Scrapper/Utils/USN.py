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
    else:  # unused
        try:
            fh = open(file_, 'r')
            res = fh.readline()
            while res != '':
                yield res.strip().lower()
                res = fh.readline()
            raise Exception('Done reading file')
        except:
            raise Exception('error reading from file!!')


def usn_inp(inp):
    for i in inp.split(","):
        if '-' in i:
            inp = i.lower()
            lwr = inp[7:10]
            upr = inp[18:]
            if lwr > upr:
                lwr, upr = upr, lwr
            for j in range(int(lwr), int(upr) + 2):
                yield inp[:7] + str(j).zfill(3)
        else:
            yield i.lower()
