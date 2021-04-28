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
    try:
        inp = inp.lower()
        for i in inp.split(","):
            if '-' in i:
                lwr = int(i[7:10])
                upr = int(i[18:])
                if lwr > upr:
                    lwr, upr = upr, lwr
                if upr - lwr > 300:
                    upr = 300 + lwr
                    print("Reducing range to 300 usns!!")
                for j in range(lwr, upr + 1):
                    yield i[:7] + str(j).zfill(3)
            else:
                yield i.lower()
    except Exception as e:
        print(e)
