from library import *

def inject_script(driver: webdriver.Chrome):
    driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {
            'source': """
                console.clear = () => console.log('Console was cleared')
                const i = setInterval(()=>{
                if (window.turnstile)
                    {clearInterval(i)
                        window.turnstile.render = (a,b) => {
                        let params = {
                            sitekey: b.sitekey,
                            pageurl: window.location.href,
                            data: b.cData,
                            pagedata: b.chlPageData,
                            action: b.action,
                            userAgent: navigator.userAgent,
                            json: 1
                        }
                        let div = document.createElement('div')
                        div.id = 'intercepted-params'
                        div.innerHTML = JSON.stringify(params)
                        document.body.appendChild(div)
                        window.cfCallback = b.callback
                        
                        return
                    } 
                }
                },50)
                const j = setInterval(()=>{
                    let token = document.getElementById('token')
                    if (token)
                    {
                        clearInterval(j)
                        cfCallback(token.innerHTML)
                        return
                    }
                },50)
            """
        }
    )

def bypass_cloudflare(driver: webdriver.Chrome, api_key: str) -> bool:
    intercepted_params = None

    for _ in range(3):
        driver.refresh()
        sleep(3)
        try:
            intercepted_params = driver.find_element(By.ID, 'intercepted-params')
            break
        except:
            continue

    if not intercepted_params:
        return False
            
    params = json.loads(intercepted_params.text)
    data0 = {
        "key": api_key,
        "method": "turnstile",
        "sitekey": params["sitekey"],
        "action": params["action"],
        "data": params["data"],
        "pagedata": params["pagedata"],
        "useragent": params["userAgent"],
        "json": 1,
        "pageurl": params["pageurl"],
    }

    response = requests.post(f"https://2captcha.com/in.php?", data=data0)
    s = response.json()["request"]
    
    while True:
        solu = requests.get(f"https://2captcha.com/res.php?key={api_key}&action=get&json=1&id={s}").json()
        if solu["request"] == "CAPCHA_NOT_READY":
            sleep(5)
        elif "ERROR" in solu["request"]:
            return False
        else:
            break
        
    solu = solu['request']
            
    driver.execute_script(f"""
        let div = document.createElement('div')
        div.id = 'token'
        div.innerHTML = '{solu}'
        document.body.appendChild(div)
    """)
    
    sleep(3)
    return True

def get_page_content(url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)

    inject_script(driver)

    driver.get(url)

    bypass_cloudflare(driver, '647be8568171d89c96ebd688c764c76a')

    result = driver.page_source

    driver.quit()

    return result

def get_schedule():
    games = []
    
    url = 'https://www.tbf.org.tr/ligler/bsl-2024-2025/maclar'

    soup = BeautifulSoup(get_page_content(url), 'html.parser')
    table = soup.find('table', id='TableMaclar')

    rows = table.find_all('tr', attrs=({'tabindex': "@ForCounter"}))

    for row in rows:
        cells = row.find_all('td')

        info = {}
        info['round'] = cells[get_col_index(table, 'Hafta')].get_text()
        info['playDate'] = datetime.strptime(cells[get_col_index(table, 'Tarih')].get_text(strip=True), '%d.%m.%Y').strftime('%Y-%m-%d')
        
        info['homeTeam'] = {
            'extid': cells[get_col_index(table, 'A Takım')].get_text(),
            'name': cells[get_col_index(table, 'A Takım')].get_text()
        }

        info['visitorTeam'] = {
            'extid': cells[get_col_index(table, 'B Takım')].get_text(),
            'name': cells[get_col_index(table, 'B Takım')].get_text()
        }

        info['state'] = 'Finished'
        info['type'] = 'Regular'

        try:
            info['homeScores'] = {
                'final': int(cells[get_col_index(table, 'Sonuç')].get_text(strip=True).split('-')[0].strip())
            }
        except:
            continue

        info['visitorScores'] = {
            'final': int(cells[get_col_index(table, 'Sonuç')].get_text(strip=True).split('-')[1].strip())
        }

        info['competition'] = 'TBL'

        info['extid'] = cells[get_col_index(table, 'Tarih')].get('data-link').split('/')[-1]
        info['source'] = 'https://www.tbf.org.tr' + cells[get_col_index(table, 'Tarih')].get('data-link')

        games.append(info)
            
    return games

def get_boxscore(extid):
    info = {}
    url = f'https://www.tbf.org.tr/ligler/bsl-2024-2025/mac-detay/{extid}/istatistik'
    
    soup = BeautifulSoup(get_page_content(url), 'html.parser')
    
    info['extid'] = extid
    info['source'] = url
    info['type'] = 'Regular'

    turkish_months = {
        'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4,
        'Mayıs': 5, 'Haziran': 6, 'Temmuz': 7, 'Ağustos': 8,
        'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12
    }

    date_str = soup.find('span', id='body_ctl00_lblMacZamani').get_text(strip=True)
    day, month, year, _ = date_str.split()
    month_num = turkish_months[month]

    date_obj = datetime(int(year), month_num, int(day)).date()
    info['playDate'] = date_obj.strftime('%Y-%m-%d')

    info['homeTeam'] = {
        'extid': soup.find('h3', id='body_ctl00_lblTakimA_Ismi').get_text(),
        'name': soup.find('h3', id='body_ctl00_lblTakimA_Ismi').get_text()
    }

    info['visitorTeam'] = {
        'extid': soup.find('h3', id='body_ctl00_lblTakimB_Ismi').get_text(),
        'name': soup.find('h3', id='body_ctl00_lblTakimB_Ismi').get_text()
    }

    info['homeScores'] = {
        'QT1': int(soup.find('h6', id='body_ctl00_lblSonuc_1Ceyrek').get_text(strip=True).split('-')[0].strip()),
        'QT2': int(soup.find('h6', id='body_ctl00_lblSonuc_2Ceyrek').get_text(strip=True).split('-')[0].strip()),
        'QT3': int(soup.find('h6', id='body_ctl00_lblSonuc_3Ceyrek').get_text(strip=True).split('-')[0].strip()),
        'QT4': int(soup.find('h6', id='body_ctl00_lblSonuc_4Ceyrek').get_text(strip=True).split('-')[0].strip()),
        'extra': 0,
        'final': int(soup.find('span', id='body_ctl00_lblTakimA_Sayi2').get_text())
    }
    info['homeScores']['extra'] = info['homeScores']['final'] - info['homeScores']['QT1'] - info['homeScores']['QT2'] - info['homeScores']['QT3'] - info['homeScores']['QT4']

    info['visitorScores'] = {
        'QT1': int(soup.find('h6', id='body_ctl00_lblSonuc_1Ceyrek').get_text(strip=True).split('-')[1].strip()),
        'QT2': int(soup.find('h6', id='body_ctl00_lblSonuc_2Ceyrek').get_text(strip=True).split('-')[1].strip()),
        'QT3': int(soup.find('h6', id='body_ctl00_lblSonuc_3Ceyrek').get_text(strip=True).split('-')[1].strip()),
        'QT4': int(soup.find('h6', id='body_ctl00_lblSonuc_4Ceyrek').get_text(strip=True).split('-')[1].strip()),
        'extra': 0,
        'final': int(soup.find('span', id='body_ctl00_lblTakimB_Sayi2').get_text())
    }
    info['visitorScores']['extra'] = info['visitorScores']['final'] - info['visitorScores']['QT1'] - info['visitorScores']['QT2'] - info['visitorScores']['QT3'] - info['visitorScores']['QT4']


    # Stats
    info['stats'] = []

    home_table = soup.find('table', id='FilterPlayer2')

    home_players = home_table.find('tbody').find_all('tr')[:-2]

    for player in home_players:
        cells = player.find_all('td')

        stat = {}
        stat['team'] = info['homeTeam']['extid']

        stat['player_name'] = cells[get_col_index(home_table, 'Basketbolcu')].get_text(strip=True)
        stat['player_extid'] = cells[get_col_index(home_table, 'Basketbolcu')].find('a').get('href').split('/')[-1]

        item = {}
        item['2pts Attempts'] = int(cells[get_col_index(home_table, '2S')].next_element.get_text(strip=True).split('/')[-1] or 0)
        item['2pts Made'] = int(cells[get_col_index(home_table, '2S')].next_element.get_text(strip=True).split('/')[0] or 0)
        item['3pts Attempts'] = int(cells[get_col_index(home_table, '3S')].next_element.get_text(strip=True).split('/')[-1] or 0)
        item['3pts Made'] = int(cells[get_col_index(home_table, '3S')].next_element.get_text(strip=True).split('/')[0] or 0)
        item['Assists'] = int(cells[get_col_index(home_table, 'AS')].get_text(strip=True) or 0)
        item['Block Shots'] = int(cells[get_col_index(home_table, 'BL')].get_text(strip=True) or 0)
        item['Defensive rebounds'] = int(cells[get_col_index(home_table, 'SR')].get_text(strip=True) or 0)
        item['Offensive rebounds'] = int(cells[get_col_index(home_table, 'HR')].get_text(strip=True) or 0)
        item['Total rebounds'] = int(cells[get_col_index(home_table, 'TR')].get_text(strip=True) or 0)
        item['FT Attempts'] = int(cells[get_col_index(home_table, 'SA')].next_element.get_text(strip=True).split('/')[-1] or 0)
        item['FT Made'] = int(cells[get_col_index(home_table, 'SA')].next_element.get_text(strip=True).split('/')[0] or 0)
        item['Minutes played'] = round(int(cells[get_col_index(home_table, 'SÜ')].get_text(strip=True).split(':')[-2] or 0) + float(cells[get_col_index(home_table, 'SÜ')].get_text(strip=True).split(':')[-1] or 0) / 60)
        item['Personal fouls'] = int(cells[get_col_index(home_table, 'FA', False)].get_text(strip=True) or 0)
        item['Points'] = int(cells[get_col_index(home_table, 'SY')].get_text(strip=True) or 0)
        item['Steals'] = int(cells[get_col_index(home_table, 'TÇ')].get_text(strip=True) or 0)
        item['Turnovers'] = int(cells[get_col_index(home_table, 'TK')].get_text(strip=True) or 0)

        stat['items'] = item
        info['stats'].append(stat)

    stat = {}
    stat['team'] = info['homeTeam']['extid']
    stat['player_extid'] = 'team'
    stat['player_firstname'] = ''
    stat['player_lastname'] = '- TEAM -'
    stat['player_name'] = '- TEAM -'

    item = {}
    cells = home_table.find('tbody').find_all('tr')[-2].find_all('td')
    
    item['Defensive rebounds'] = int(cells[get_col_index(home_table, 'SR')].get_text(strip=True) or 0)
    item['Offensive rebounds'] = int(cells[get_col_index(home_table, 'HR')].get_text(strip=True) or 0)
    item['Total rebounds'] = int(cells[get_col_index(home_table, 'TR')].get_text(strip=True) or 0)
    item['Turnovers'] = int(cells[get_col_index(home_table, 'TK')].get_text(strip=True) or 0)
    item['Personal fouls'] = int(cells[get_col_index(home_table, 'FA', False)].get_text(strip=True) or 0)

    stat['items'] = item
    info['stats'].append(stat)

    away_table = soup.find('table', id='FilterPlayer3')
    away_players = away_table.find('tbody').find_all('tr')[:-2]

    for player in away_players:
        cells = player.find_all('td')

        stat = {}
        stat['team'] = info['visitorTeam']['extid']

        stat['player_name'] = cells[get_col_index(away_table, 'Basketbolcu')].get_text(strip=True)
        stat['player_extid'] = cells[get_col_index(away_table, 'Basketbolcu')].find('a').get('href').split('/')[-1]

        item = {}
        item['2pts Attempts'] = int(cells[get_col_index(away_table, '2S')].next_element.get_text(strip=True).split('/')[-1] or 0)
        item['2pts Made'] = int(cells[get_col_index(away_table, '2S')].next_element.get_text(strip=True).split('/')[0] or 0)
        item['3pts Attempts'] = int(cells[get_col_index(away_table, '3S')].next_element.get_text(strip=True).split('/')[-1] or 0)
        item['3pts Made'] = int(cells[get_col_index(away_table, '3S')].next_element.get_text(strip=True).split('/')[0] or 0)
        item['Assists'] = int(cells[get_col_index(away_table, 'AS')].get_text(strip=True) or 0)
        item['Block Shots'] = int(cells[get_col_index(away_table, 'BL')].get_text(strip=True) or 0)
        item['Defensive rebounds'] = int(cells[get_col_index(away_table, 'SR')].get_text(strip=True) or 0)
        item['Offensive rebounds'] = int(cells[get_col_index(away_table, 'HR')].get_text(strip=True) or 0)
        item['Total rebounds'] = int(cells[get_col_index(away_table, 'TR')].get_text(strip=True) or 0)
        item['FT Attempts'] = int(cells[get_col_index(away_table, 'SA')].next_element.get_text(strip=True).split('/')[-1] or 0)
        item['FT Made'] = int(cells[get_col_index(away_table, 'SA')].next_element.get_text(strip=True).split('/')[0] or 0)
        item['Minutes played'] = round(int(cells[get_col_index(away_table, 'SÜ')].get_text(strip=True).split(':')[-2] or 0) + float(cells[get_col_index(away_table, 'SÜ')].get_text(strip=True).split(':')[-1] or 0) / 60)
        item['Personal fouls'] = int(cells[get_col_index(away_table, 'FA', False)].get_text(strip=True) or 0)
        item['Points'] = int(cells[get_col_index(away_table, 'SY')].get_text(strip=True) or 0)
        item['Steals'] = int(cells[get_col_index(away_table, 'TÇ')].get_text(strip=True) or 0)
        item['Turnovers'] = int(cells[get_col_index(away_table, 'TK')].get_text(strip=True) or 0)

        stat['items'] = item
        info['stats'].append(stat)

    stat = {}
    stat['team'] = info['visitorTeam']['extid']
    stat['player_extid'] = 'team'
    stat['player_firstname'] = ''
    stat['player_lastname'] = '- TEAM -'
    stat['player_name'] = '- TEAM -'

    item = {}
    cells = away_table.find('tbody').find_all('tr')[-2].find_all('td')
    
    item['Defensive rebounds'] = int(cells[get_col_index(away_table, 'SR')].get_text(strip=True) or 0)
    item['Offensive rebounds'] = int(cells[get_col_index(away_table, 'HR')].get_text(strip=True) or 0)
    item['Total rebounds'] = int(cells[get_col_index(away_table, 'TR')].get_text(strip=True) or 0)
    item['Turnovers'] = int(cells[get_col_index(away_table, 'TK')].get_text(strip=True) or 0)
    item['Personal fouls'] = int(cells[get_col_index(away_table, 'FA', False)].get_text(strip=True) or 0)

    stat['items'] = item
    info['stats'].append(stat)

    return info
    
def get_player(extid):
    info = {}

    url = f'https://www.tbf.org.tr/ligler/bsl-2024-2025/basketbolcu-detay/{extid}'

    page_content = get_page_content(url)
    soup = BeautifulSoup(page_content, 'html.parser')

    info['name'] = soup.find('h1').get_text()
    info['extid'] = extid
    info['source'] = url

    icons = soup.find('h4').find_all('i')

    for icon in icons:
        if 'fa-birthday-cake' in icon.get('class'):
            info['dateOfBirth'] = datetime.strptime(icon.next_sibling.get_text(strip=True), '%d.%m.%Y').strftime('%Y-%m-%d')

        if 'fa-flag' in icon.get('class'):
            info['nationality'] = icon.next_sibling.get_text(strip=True)

        if 'fa-arrows-v' in icon.get('class'):
            info['height'] = int(icon.next_sibling.get_text(strip=True).replace('cm', '').strip())

    return info
    
def func_bsl(args):
    if args['f'] == 'schedule':
        games = []
        schedule = get_schedule()
        games.extend(schedule)
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'])
    elif args['f'] == 'player':
        return get_player(args['extid'])
    