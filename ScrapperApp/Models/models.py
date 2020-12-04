import datetime

from sqlalchemy import create_engine, Column, Integer, String, MetaData, SmallInteger, ForeignKey, \
    Boolean

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from Scrapper.Utils.exceptionHandler import handle_exception

DB_URI = 'sqlite:///../data/ServerManagement.db'
localdb_engine = create_engine(DB_URI)  # , echo=True)
Session = sessionmaker()
Session.configure(bind=localdb_engine)
session = Session(autoflush=False)

Base = declarative_base()
metadata = MetaData()

# status code
codes = {
    0: 'error',
    1: 'complete',
    2: 'queued',
    3: 'processing',
    4: 'trying to connect to vtu',
    5: 'not sent to semstat db yet',
    6: 'updated',
    7: 'canceled',
    8: 'invalid',
    9: 'usn list invalid format',
    # 10: 'not avaliable', #add later if required
}


# Exam Model
class Exam(Base):
    __tablename__ = 'Exam'
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(100), unique=True)

    requests = relationship("Progress", back_populates="exam")
    usns = relationship("Usn")

    def __init__(self, name):
        self.name = name

    def to_json(self):
        return {'id': self.id, 'name': self.name}


# Url Model
class Url(Base):
    __tablename__ = 'Url'
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(100), unique=True)

    requests = relationship("Progress", back_populates="url")
    usns = relationship("Usn")

    def __init__(self, url):
        self.name = url

    def to_json(self):
        return {'id': self.id, 'name': self.name}


# UsnTracker Model (dynamic)
class Usn(Base):
    __tablename__ = 'Usn'
    usn = Column(String(10), primary_key=True)
    url_id = Column(Integer, ForeignKey('Url.id'), primary_key=True)
    exam_id = Column(Integer, ForeignKey('Exam.id'), primary_key=True)
    # description = Column(String(20))
    status = Column(SmallInteger)

    def __init__(self, usn, url_id, exam_id):
        self.usn = usn
        self.url_id = url_id
        self.exam_id = exam_id
        self.status = 2
        self.description = None

    def to_json(self):
        return {'usn': self.usn, 'status': codes[self.status]}


# RequestTracker Model
class Progress(Base):
    __tablename__ = 'Progress'
    id = Column(Integer, primary_key=True, autoincrement=True)

    url_id = Column(String(50), ForeignKey('Url.id'))
    exam_id = Column(String(50), ForeignKey('Exam.id'))
    description = Column(String(50))

    created_at = Column(String(50))
    batch = Column(Integer)
    status = Column(SmallInteger)
    usn = Column(String(10))
    dept = Column(String(8))
    rtype = Column(SmallInteger)
    inp = Column(String(300))
    update = Column(Boolean)
    reval = Column(Boolean)

    url = relationship("Url", back_populates="requests")
    exam = relationship("Exam", back_populates="requests")

    # UniqueConstraint(url_id, batch, exam_id, dept, rtype)

    def __init__(self, batch=None, dept=None, rtype=1, url_id=None, exam_id=None,
                 created_at=None, inp=None,
                 update=False, reval=False):
        self.batch = batch
        self.dept = dept
        self.status = 2
        self.rtype = rtype
        self.inp = inp
        self.url_id = url_id
        self.exam_id = exam_id
        self.update = update
        self.reval = reval
        if not created_at:
            self.created_at = str(datetime.datetime.now())
        else:
            self.created_at = created_at

    # __table_args__ = (Index("HISTORY_IDX", "url", "dept", "batch","exam"),)

    def to_json(self):
        to_serialize = ['id', 'description', 'created_at', 'batch', 'usn', 'inp', 'update', 'reval']
        d = {}
        for attr_name in to_serialize:
            d[attr_name] = getattr(self, attr_name)
        d['status'] = codes[self.status]
        d['rtype'] = self.rtype
        if self.exam_id:
            d['exam'] = self.exam.name
        else:
            d['exam'] = None
        if self.url_id:
            d['url'] = self.url.name
        else:
            d['url'] = None
        return d


# creates database
def init_db():
    try:
        # Base.metadata.drop_all(localdb_engine) #todo change
        print("sqlite: DB Create mode - use if exisiting.")
        Base.metadata.create_all(localdb_engine)
    except Exception as e:
        handle_exception(e)
        print(e)
