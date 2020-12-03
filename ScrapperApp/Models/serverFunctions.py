from Scrapper.Utils.exceptionHandler import handle_exception

from .models import Base, session, Usn, localdb_engine, Url, Exam


# creates database
def init_db():
    try:
        # Base.metadata.drop_all(localdb_engine) #todo change
        print("remiander: uncomment line when required")
        Base.metadata.create_all(localdb_engine)
    except Exception as e:
        handle_exception(e)
        print(e)


def get_url_id(url):
    row = Url(url)
    try:
        session.add(row)
        session.commit()
        return row.id
    except Exception as e:
        session.rollback()
        handle_exception(e,risk='normal')
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
        handle_exception(e,"normal")
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
        handle_exception(e,risk='normal')
        row = session.query(Usn).filter(Usn.usn == row.usn and Usn.url == row.url).first()
        if row.status == 0 or row.status == 5 or force:
            return row
        return None

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
