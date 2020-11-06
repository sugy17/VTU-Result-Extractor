def usn_generator(clg_code='1cr', batches=['16'], depts=['cs', 'ec'], file_=None):
    if not file_:
        for dept in depts:
            for batch in batches:
                for number in range(1, 2):
                    change_section = yield clg_code + batch + dept + str(number).zfill(3)
                    if change_section is True:
                        break
                dip = batch[0] + str(int(batch[1]) + 1)  # change
                for number in range(400, 401):
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