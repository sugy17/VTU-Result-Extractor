import asyncio
import re

import aiohttp
import random

from . import host
from .Parsers.HTMLParser import exam_name_regx, catch_alert_regx, parse_indexpage #, parse_syllabuspage
from .Utils.captchaDecode import read_captcha
from .Utils.exceptionHandler import handle_exception
from .Utils.httpUtil import get_page, post_page
# from typing import Set
# from semester_stats_report import SubjectReport
# from .Parsers.PDFParser import parse_pdf_subjects


async def get_exam_name(indexpage_url):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        index_page = await get_page(session, host + indexpage_url)
    # print(host + indexpage_url)
    if len(index_page) < 5000:
        return 0
    return exam_name_regx.findall(index_page, re.DOTALL)[0]


# async def sync_subject_details():
#     async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#         try:
#             syllbuspage = await get_page(session, "https://vtu.ac.in/b-e-scheme-syllabus/")
#             # pdf_urls = parse_syllabuspage(syllbuspage)
#             pdf_urls = ['https://vtu.ac.in/pdf/2018syll/cs.pdf','https://vtu.ac.in/wp-content/uploads/2019/12/csesch.pdf']
#             for url in pdf_urls:
#                 try:
#                     pdf = await get_page(session, url, get_blob=True)
#                     sub_keep = await parse_pdf_subjects(pdf)
#                     send_subs_to_db(sub_keep)
#                     print(len(sub_keep), sub_keep)
#                 except Exception as e:
#                     handle_exception(e, risk='notify')
#         except Exception as e:
#             # handle_exception(e, risk='notify')
#             pass


async def get_resultpage(usn, indexpage_url, resultpage_url, save=True):
    retry_count = 0
    # cookie = {'PHPSESSID': 'q6k5bedrobcjob6opttgg11i14'+str(ccount)}
    while True:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                index_page, img_src, token, captcha_blob, captcha_code = "", "", "", "", ""
                try:
                    index_page = await get_page(session, host + indexpage_url)
                except Exception as e:
                    handle_exception(e)
                    if save:
                        await asyncio.sleep(random.uniform(0, 3))
                    # continue
                if len(index_page) < 5000:
                    retry_count += 1
                    if not save:
                        if retry_count > 3:
                            return None  # return meaning full error codes or throw exception
                    else:
                        await asyncio.sleep(5)
                    continue
                try:
                    img_src, token = parse_indexpage(index_page)
                    captcha_blob = await get_page(session, host + img_src, True)
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(0, 3))
                    continue
                if len(captcha_blob) < 1000:
                    continue
                try:
                    captcha_code = await read_captcha(captcha_blob)  ##cpu blocking
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(0, 3))
                    continue
                # print(captcha_code)
                if len(captcha_code) != 6:
                    continue
                data = {'Token': token, 'lns': usn, 'captchacode': captcha_code}
                resultpage = ""
                try:
                    resultpage = await post_page(session, host + resultpage_url, data)
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(3, 6))
                    continue
                # if len(resultpage) < 1000:  #optimise alert decetion
                try:
                    alert = catch_alert_regx.findall(resultpage)[0]
                    if 'captch' in alert:
                        continue
                    elif 'not available' in alert:
                        print(usn, alert)
                        return 8
                    elif 'check' in alert or 'after' in alert or 'again' in alert:
                        # print(usn, alert)
                        await asyncio.sleep(random.uniform(0, 3))
                        continue
                    # print(usn, alert)
                    # return meaning full err data
                except Exception as e:
                    handle_exception(e, 'expected')
                    pass
                return resultpage
        except Exception as e:
            handle_exception(e)
