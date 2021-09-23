from sqlalchemy.sql.expression import null
from ..Utils.httpUtil import get_page
import re
import aiohttp
from bs4 import BeautifulSoup as bs

sem_regx = re.compile('Semester')
exam_name_regx = re.compile('<b>.*>(.*?) EXAMINATION RESULTS')  # improve
catch_alert_regx = re.compile(r'alert\((.*)\)')
hrefs_regx = re.compile(r'href.*?"(.*?\.pdf)"')


def parse_syllabuspage(page):
    print(len(hrefs_regx.findall(page)), hrefs_regx.findall(page))
    return hrefs_regx.findall(page)


async def parse_for_links(link, page, broad_link_desc=None):
    soup = bs(page, 'html.parser')
    tabs = soup.find('ul', {'class': 'logmod__tabs'})
    res = {}
    if not tabs:
        broad_links = [(link+"/"+re.findall("'.*?'", str(i))[0][1:][:-1], i.find('b').text)
                       for i in soup.find_all(onclick=re.compile("window.open\(.*?',"))]
        for broad_link in broad_links:
            try:
                async with aiohttp.ClientSession() as session:
                    page = await get_page(session, broad_link[0])
            except Exception as e:
                return {}
            res = {**res, **await parse_for_links(broad_link[0], page, (broad_link_desc + " - ") if  broad_link_desc else "" + broad_link[1])}
    else:
        tabs = tabs.find_all('li')
        for tab in tabs:
            # differentiaties various examniations along with CBCS ,NOn CBCS , reval etc
            exam_type = broad_link_desc + " - " + \
                tab.find('a').text.replace(' ', '')
            if exam_type not in res:
                res[exam_type] = []
            content = soup.find(
                'div', {'class': 'logmod__tab '+tab['data-tabtar']})
            links = content.find_all('div', {'class': 'panel-heading'})
            for link in links:
                res[exam_type].append({'link': 'https://results.vtu.ac.in/'+re.findall(
                    "'.*?'", link['onclick'])[0][1:][:-1], 'desc': link.find('b').text})
    return res


def parse_indexpage(page):
    soup = bs(page, 'html.parser')
    img_src = soup.find(alt="CAPTCHA code")['src']
    token = soup.find('input')['value']
    return img_src, token


# same logic used for parsing reval page also, separation done while sending files to db
def parse_resultpage(page):
    soup = bs(page, 'html.parser')
    # print(soup.find_all('div',{'class':'divTableCell'}))
    name = soup.find('table').find_all('tr')[1].find_all('td')[1].text[2:]
    sems = [list(i for i in e.split() if i.isdigit())[0] for e in
            soup(text=sem_regx)]  # sems=[ e[11] for e in soup(text=sem_regx)]
    result = soup.find_all('div', {'class': 'divTableBody'})
    return name, sems, result