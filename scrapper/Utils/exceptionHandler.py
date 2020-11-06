import os
import sys


def handle_exception(e, risk='notify'):
    if risk == 'notify':
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(fname, exc_tb.tb_lineno, exc_type, e)
    pass
