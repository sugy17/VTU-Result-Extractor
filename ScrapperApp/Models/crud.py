from Scrapper.Utils.exceptionHandler import handle_exception

from .models import session, Usn, Url, Exam


def get_url_id(url):
    row = Url(url)
    try:
        session.add(row)
        session.commit()
        return row.id
    except Exception as e:
        session.rollback()
        handle_exception(e, risk='normal')
        row = session.query(Url).filter(Url.name == url).first()
        return row.id


def get_exam_id(exam):
    row = Exam(exam)
    try:
        session.add(row)
        session.commit()
        return row.id
    except Exception as e:
        session.rollback()
        handle_exception(e, "normal")
        row = session.query(Exam).filter(Exam.name == exam).first()
        return row.id


def check_usn(usn, url_id, exam_id, force=False):
    row = Usn(usn, url_id, exam_id)
    try:
        session.add(row)
        session.commit()
        return row
    except Exception as e:
        session.rollback()
        handle_exception(e, risk='normal')
        row = session.query(Usn).filter(Usn.usn == row.usn, Usn.url == row.url).first()
        if row.status == 0 or row.status == 5 or force:
            return row
        return None


def get_urls():
    res = []
    for i in session.query(Url):
        res.append(i.to_json())
    return res


def get_exams():
    res = []
    for i in session.query(Exam):
        res.append(i.to_json())
    return res


def query_exam_name(exam_id):
    return session.query(Exam).filter(Exam.id == exam_id).first().name


def query_usn_data(url_id, exam_id, usn=None):
    res = []
    if not usn:
        for i in session.query(Usn).filter(Usn.url_id == url_id, Usn.exam_id == exam_id):
            res.append(i.to_json())
    else:
        return session.query(Usn).filter(Usn.url_id == url_id, Usn.exam_id == exam_id, Usn.usn == usn).first().to_json()
    return res

# def get_table(exam_name):
#     EXAM = Table(
#         exam_name, metadata,
#         Column('usn', String(10), primary_key=True),
#         Column('url', Integer, primary_key=True),
#         Column('description', String(20)),
#         Column('status', SmallInteger)
#     )
#     metadata.create_all(localdb_engine)
#     mapper(UsnTracker, EXAM)
#     return UsnTracker
#
#
# def check_usn(usn,url,exam):
#     EXAM = get_table(exam)  # add later if required
#     try:
#         row = EXAM(usn,url)
#         session.add(row)
#         session.commit()
#         return row
#     except:
#         row = session.query(UsnTracker).filter(UsnTracker.usn == row.usn and UsnTracker.url == row.url).first()
#         if row.status != 0:
#             return None