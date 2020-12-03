from typing import Set
import camelot
import aiofiles
from PyPDF2 import PdfFileReader, PdfFileWriter
from semester_stats_report import SubjectReport

from ..Utils.exceptionHandler import handle_exception


async def parse_pdf_subjects(pdf):
    try:
        print(len(pdf))
        fp = await aiofiles.open("temp.pdf", mode="wb")
        await fp.close()
        pdf_writer = PdfFileWriter()
        input_pdf = PdfFileReader(str('temp.pdf'))
        for i in range(1, 8):
            try:
                pdf_writer.addPage(input_pdf.getPage(i))
            except:
                pass
        async with aiofiles.open('temp.pdf', mode="wb") as o_file:
            await pdf_writer.write(o_file)
        # pandas.set_option('display.width', 1000)
        # pandas.set_option('display.max_columns', 20)
        sub_keep: Set[SubjectReport] = set()
        tables = camelot.read_pdf("temp.pdf", pages='all', multiple_tables=True, flavor="lattice")
        for table in tables:
            try:
                # print(i.df.iloc[2:-1, [1, 2, 6, 7, 9]])
                table = table.df.iloc[2:-1, [1, 2, 7, 8, 10]]
                for sub in table:
                    # print(table.iloc[sub,:])
                    subcode, subname, internal, external, creds = table.iloc[sub, :]
                    print(subcode, internal, external, creds)
                minext, mintotal, maxtotal = 0, 0, 0
                sub_keep.add(
                    SubjectReport(
                        Code=subcode.replace('\n', ''),
                        Name=subname.replace('\n', ''),
                        MinExt=minext,
                        MinTotal=mintotal,
                        MaxTotal=maxtotal,
                        Credits=int(creds)
                    )
                )
            except Exception as e:
                # try:
                #     #print(i.df.iloc[1:, :])
                #     li.append(i.df.iloc[1:, :])
                # except:
                #     pass
                handle_exception(e, None)
                pass
        # print(li)
        return sub_keep
    except Exception as e:
        handle_exception(e, 'notify')
