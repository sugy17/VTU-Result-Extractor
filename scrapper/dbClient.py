import os
from semester_stats_report import ScoreReport, StudentReport, SubjectReport
from semester_stats_report import SemesterClient
import csv
from typing import Set
from . import db_url


def chunk(lst, n):
    # Helper Function for The Code Below
    # This just Splits up the Below into sublists.
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


def send_files_to_db(exam_name):
    # This is the Main Client, Use it to POST data.
    cl = SemesterClient(db_url)
    # We are keeping Sets to Avoid Duplication.
    stu_keep: Set[StudentReport] = set()
    sub_keep: Set[SubjectReport] = set()
    sco_keep: Set[ScoreReport] = set()
    for f_name in os.listdir(os.path.join('DATA', exam_name)):
        with open(os.path.join('DATA', exam_name, f_name)) as f:
            _data = csv.reader(f.readlines(), delimiter=",")
            # For Each Row:

            for x in _data:
                x = x[: len(x) - 2]
                # Create Student
                stu_keep.add(StudentReport(Name=x[1], Usn=x[0]))
                for y in chunk(x[3:], 6):
                    # Subject And Score for Each.
                    sub_keep.add(
                        SubjectReport(
                            Code=y[0],
                            Name=y[1],
                            MinExt=19,
                            MinTotal=40,
                            MaxTotal=100,
                            Credits=4,
                        )
                    )
                    sco_keep.add(
                        ScoreReport(Usn=x[0], SubjectCode=y[0], Internals=y[2], Externals=y[3])
                    )

        # Data is scrubbed!
        # Send the StudentReports First
        cl.bulk().student(list(stu_keep))
        # Send Subject Reports Second.
        cl.bulk().subject(list(sub_keep))
        # Send the Score Reports AT THE LAST:
        cl.bulk().scores(list(sco_keep))
