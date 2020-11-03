import re
from bs4 import BeautifulSoup as bs

sem_regx = re.compile('Semester')
exam_name_regx = re.compile('<b>.*>(.*?) EXAMINATION RESULTS')  ##improve
catch_alert_regx = re.compile(r'alert\((.*)\)')


def parse_indexpage(page):
    soup = bs(page, 'html.parser')
    img_src = soup.find(alt="CAPTCHA code")['src']
    token = soup.find('input')['value']
    return img_src, token


def parse_resultpage(page):
    soup = bs(page, 'html.parser')
    # print(soup.find_all('div',{'class':'divTableCell'}))
    name = soup.find('table').find_all('tr')[1].find_all('td')[1].text[2:]
    sems = [list(i for i in e.split() if i.isdigit())[0] for e in
            soup(text=sem_regx)]  # sems=[ e[11] for e in soup(text=sem_regx)]
    result = soup.find_all('div', {'class': 'divTableBody'})
    return name, sems, result
