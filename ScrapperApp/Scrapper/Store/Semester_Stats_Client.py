import os
import csv
from typing import Set

from semester_stats_report import ScoreReport, StudentReport, SubjectReport
from semester_stats_report import SemesterClient

from .. import semstats_url
from ..Utils.exceptionHandler import handle_exception
from ..Utils.subjects import get_default_marks


def chunk(lst, n):
    # Helper Function for The Code Below
    # This just Splits up the Below into sublists.
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


async def send_subs_to_db(sub_keep):
    cl = SemesterClient(semstats_url)
    # Send Subject Reports Second.
    await cl.bulk().subject(list(sub_keep))


async def send_student_to_db(_data):
    try:
        if len(_data) == 0:
            print("semstat-report: Student data was empty")
            return True
        # Add singelly queried results
        cl = SemesterClient(semstats_url)
        # We are keeping Sets to Avoid Duplication.
        stu, usn = None, None
        sub_keep: Set[SubjectReport] = set()
        sco_keep: Set[ScoreReport] = set()
        temp = set()
        for x in _data:
            x = x[: len(x) - 1]
            # Create Student
            stu = StudentReport(Name=x[1], Usn=x[0])
            usn = x[0]
            for y in chunk(x[3:], 6):
                # Subject And Score for Each.
                temp.add(
                    (y[0], y[1], x[2])
                )
            for y in chunk(x[3:], 6):
                sco_keep.add(
                    ScoreReport(Usn=x[0], SubjectCode=y[0], Internals=y[2], Externals=y[3])
                )

        for code, name, sem in temp:
            MinExt, MinTotal, MaxTotal, Credits = get_default_marks(code, name, sem)
            sub_keep.add(
                SubjectReport(
                    Code=code,
                    Name=name,
                    MinExt=MinExt,
                    MinTotal=MinTotal,
                    MaxTotal=MaxTotal,
                    Credits=Credits,
                )
            )

        try:
            # put student report obj
            await cl.student(usn).put(stu)
        except:
            pass
        # Send Subject Reports Second.
        await cl.bulk().subject(list(sub_keep))
        # Send the Score Reports AT THE LAST:
        await cl.bulk().scores(list(sco_keep))
        return True
    except Exception as e:
        handle_exception(e)
        return False


async def send_files_to_db(exam_name, files):
    try:
        if len(files) == 0:
            print("semstat-report: no files recived to send.")
            return True
        # params eg: 'AUGUST _ SEPTEMBER-2020' ['Data-CS-2016-2015-8.csv']
        # This is the Main Client, Use it to POST data.
        cl = SemesterClient(semstats_url)
        # We are keeping Sets to Avoid Duplication.
        stu_keep: Set[StudentReport] = set()
        sub_keep: Set[SubjectReport] = set()
        sco_keep: Set[ScoreReport] = set()
        temp = set()
        for f_name in files:
            sem = str(f_name.split('-')[4]).replace('.csv', '')
            f_name = os.path.join('..', 'data', 'files', exam_name, f_name)
            with open(f_name) as f:
                _data = csv.reader(f.readlines(), delimiter=",")
                # For Each Row:

                for x in _data:
                    x = x[: len(x) - 1]
                    # Create Student
                    stu_keep.add(StudentReport(Name=x[1], Usn=x[0]))
                    for y in chunk(x[3:], 6):
                        # Subject And Score for Each.
                        temp.add(
                            (y[0], y[1])
                        )
                    for y in chunk(x[3:], 6):
                        sco_keep.add(
                            ScoreReport(Usn=x[0], SubjectCode=y[0], Internals=y[2], Externals=y[3])
                        )

            for code, name in temp:
                MinExt, MinTotal, MaxTotal, Credits = get_default_marks(code, name, sem)
                sub_keep.add(
                    SubjectReport(
                        Code=code,
                        Name=name,
                        MinExt=MinExt,
                        MinTotal=MinTotal,
                        MaxTotal=MaxTotal,
                        Credits=Credits,
                    )
                )

            # Data is scrubbed!
            # Send the StudentReports First
            await cl.bulk().student(list(stu_keep))
            # Send Subject Reports Second.
            await cl.bulk().subject(list(sub_keep))
            # Send the Score Reports AT THE LAST:
            await cl.bulk().scores(list(sco_keep))
            return True
    except Exception as e:
        handle_exception(e)
        return False

