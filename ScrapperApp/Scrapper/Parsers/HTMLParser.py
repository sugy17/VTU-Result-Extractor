import re
from bs4 import BeautifulSoup as bs

sem_regx = re.compile('Semester')
exam_name_regx = re.compile('<b>.*>(.*?) EXAMINATION RESULTS')  ##improve
catch_alert_regx = re.compile(r'alert\((.*)\)')
hrefs_regx = re.compile(r'href.*?"(.*?\.pdf)"')


def parse_syllabuspage(page):
    print(len(hrefs_regx.findall(page)), hrefs_regx.findall(page))
    return hrefs_regx.findall(page)

  
def parse_for_links(page):
    soup = bs(page, 'html.parser')
    tabs = soup.find('ul', {'class': 'logmod__tabs'}).find_all('li')
    res = {}
    for tab in tabs:
        exam_type = tab.find('a').text.replace(' ','') #CBCS or NOn CBCS
        if exam_type not in res:
                res[exam_type] = []
        content = soup.find('div', {'class': 'logmod__tab '+tab['data-tabtar']})
        links = content.find_all('div', {'class': 'panel-heading'})
        for link in links:
                res[exam_type].append({'link':'https://results.vtu.ac.in/'+re.findall("'.*?'",link['onclick'])[0][1:][:-1],'desc':link.find('b').text}) 
    return res

#parse_for_links(open('test.html')) 

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


