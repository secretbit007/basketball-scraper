from library import *

def get_schedule_by_date(params: list):
    games = []
    spar = params[0]
    day = params[2]
    month = params[1]
    year = params[3]

    api = f"https://basketball.realgm.com/{spar}/schedules/{datetime(year, month, day).strftime('%Y-%m-%d')}"
    resp = requests.get(api)

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', class_='table')
    matches = table.find('tbody').find_all('tr')

    for match in matches:
        game = {}
        game['competition'] = soup.find('option', attrs={'selected': 'selected'}).get_text()
        game['playDate'] = datetime(year, month, day).strftime('%Y-%m-%d')
        game['round'] = '-'
        
        game['state'] = 'Completed'
            
        game['type'] = 'Regular'
        
        home_team = match.find('td', attrs={'data-th': 'Home Team'})
        
        game['homeTeam'] = {
            'extid': home_team.find('a', recursive=False).get('href').split('/')[-3],
            'name': home_team.find('a', recursive=False).get_text()
        }

        visitor_team = match.find('td', attrs={'data-th': 'Away Team'})
        game['visitorTeam'] = {
            'extid': visitor_team.find('a', recursive=False).get('href').split('/')[-3],
            'name': visitor_team.find('a', recursive=False).get_text()
        }

        result = match.find('td', attrs={'data-th': 'Result'})

        if '-' not in result.get_text():
            continue

        game['homeScores'] = {
            'final': result.get_text().split('-')[-1]
        }
        
        game['visitorScores'] = {
            'final': result.get_text().split('-')[0]
        }
        
        try:
            game['extid'] = result.find('a').get('href')
        except:
            continue

        game['source'] = 'https://basketball.realgm.com' + result.find('a').get('href')

        games.append(game)

    return games

def get_schedule(spar: str):
    games = []

    api = f"https://basketball.realgm.com/ajax/schedules.phtml?league=International&leagueid={spar.split('/')[-2]}"
    resp = requests.get(api)
    dates = resp.json()
    params = [[spar].extend(date) for date in dates]

    with ThreadPoolExecutor(max_workers=50) as worker:
        results = worker.map(get_schedule_by_date, params)
        
        for result in results:
            games.extend(result)

    return games

def get_col_index(table: Tag, col: str):
    thead = table.find('thead')
    cells = thead.find_all('th')

    for cell in cells:
        if cell.get_text() == col:
            return cells.index(cell)
        
    return 0

def get_boxscore(extid):
    url = f'https://basketball.realgm.com{extid}/'

    resp = requests.get(url)
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        info = {}
        info['extid'] = extid
        info['playDate'] = extid.split('/')[-3]
        info['source'] = url
        info['type'] = 'Regular'
        
        info['homeTeam'] = {
            'name': soup.find_all('a', attrs={'style': 'text-decoration: none;'})[-1].get_text(),
            'extid': soup.find_all('a', attrs={'style': 'text-decoration: none;'})[-1].get('href').split('/')[-2],
        }

        info['visitorTeam'] = {
            'name': soup.find_all('a', attrs={'style': 'text-decoration: none;'})[0].get_text(),
            'extid': soup.find_all('a', attrs={'style': 'text-decoration: none;'})[0].get('href').split('/')[-2],
        }

        score_table = soup.find('table', class_='table table-striped table-hover table-bordered table-compact table-nowrap')

        info['homeScores'] = {
            'QT1': int(score_table.find('tbody').find_all('tr')[-1].find_all('td')[1].get_text()),
            'QT2': int(score_table.find('tbody').find_all('tr')[-1].find_all('td')[2].get_text()),
            'QT3': int(score_table.find('tbody').find_all('tr')[-1].find_all('td')[3].get_text()),
            'QT4': int(score_table.find('tbody').find_all('tr')[-1].find_all('td')[4].get_text()),
            'extra': 0,
            'final': int(score_table.find('tbody').find_all('tr')[-1].find_all('td')[-1].get_text())
        }
        info['homeScores']['extra'] = info['homeScores']['final'] - info['homeScores']['QT1'] - info['homeScores']['QT2'] - info['homeScores']['QT3'] - info['homeScores']['QT4']

        info['visitorScores'] = {
            'QT1': int(score_table.find('tbody').find_all('tr')[0].find_all('td')[1].get_text()),
            'QT2': int(score_table.find('tbody').find_all('tr')[0].find_all('td')[2].get_text()),
            'QT3': int(score_table.find('tbody').find_all('tr')[0].find_all('td')[3].get_text()),
            'QT4': int(score_table.find('tbody').find_all('tr')[0].find_all('td')[4].get_text()),
            'extra': 0,
            'final': int(score_table.find('tbody').find_all('tr')[0].find_all('td')[-1].get_text())
        }
        info['visitorScores']['extra'] = info['visitorScores']['final'] - info['visitorScores']['QT1'] - info['visitorScores']['QT2'] - info['visitorScores']['QT3'] - info['visitorScores']['QT4']

        info['stats'] = []

        boxscore_tables = soup.find_all('table', class_='table table-striped table-centered table-hover table-bordered table-compact table-nowrap')

        # home
        players = boxscore_tables[-1].find('tbody').find_all('tr')

        for player in players:
            cells = player.find_all('td')

            stat = {}
            stat['team'] = info['homeTeam']['extid']

            stat['player_firstname'] = cells[get_col_index(boxscore_tables[-1], 'Player')].get_text().split(' ')[0]
            stat['player_lastname'] = cells[get_col_index(boxscore_tables[-1], 'Player')].get_text().split(' ')[-1]
            stat['player_name'] = cells[get_col_index(boxscore_tables[-1], 'Player')].get_text()
            stat['player_extid'] = cells[get_col_index(boxscore_tables[-1], 'Player')].find('a').get('href')

            item = {}
            item['2pts Attempts'] = int(cells[get_col_index(boxscore_tables[-1], 'FGM-A')].get_text().split('-')[-1]) - int(cells[get_col_index(boxscore_tables[-1], '3PM-A')].get_text().split('-')[-1])
            item['2pts Made'] = int(cells[get_col_index(boxscore_tables[-1], 'FGM-A')].get_text().split('-')[0]) - int(cells[get_col_index(boxscore_tables[-1], '3PM-A')].get_text().split('-')[0])
            item['3pts Attempts'] = int(cells[get_col_index(boxscore_tables[-1], '3PM-A')].get_text().split('-')[-1])
            item['3pts Made'] = int(cells[get_col_index(boxscore_tables[-1], '3PM-A')].get_text().split('-')[0])
            item['Assists'] = int(cells[get_col_index(boxscore_tables[-1], 'Ast')].get_text())
            item['Block Shots'] = int(cells[get_col_index(boxscore_tables[-1], 'BLK')].get_text())
            item['Defensive rebounds'] = int(cells[get_col_index(boxscore_tables[-1], 'Def')].get_text())
            item['FT Attempts'] = int(cells[get_col_index(boxscore_tables[-1], 'FTM-A')].get_text().split('-')[-1])
            item['FT Made'] = int(cells[get_col_index(boxscore_tables[-1], 'FTM-A')].get_text().split('-')[0])
            item['Minutes played'] = round(int(cells[get_col_index(boxscore_tables[-1], 'Min')].get_text().split(':')[0]) + float(cells[get_col_index(boxscore_tables[-1], 'Min')].get_text().split(':')[1]) / 60)
            item['Offensive rebounds'] = int(cells[get_col_index(boxscore_tables[-1], 'Off')].get_text())
            item['Personal fouls'] = int(cells[get_col_index(boxscore_tables[-1], 'PF')].get_text())
            item['Points'] = int(cells[get_col_index(boxscore_tables[-1], 'PTS')].get_text())
            item['Steals'] = int(cells[get_col_index(boxscore_tables[-1], 'STL')].get_text())
            item['Total rebounds'] = int(cells[get_col_index(boxscore_tables[-1], 'Reb')].get_text())
            item['Turnovers'] = int(cells[get_col_index(boxscore_tables[-1], 'TO')].get_text())

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['homeTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        item = {}
        team = boxscore_tables[-1].find('tfoot').find_all('tr')[1].find_all('th')
        item['Defensive rebounds'] = int(team[get_col_index(boxscore_tables[-1], 'Def')].get_text())
        item['Offensive rebounds'] = int(team[get_col_index(boxscore_tables[-1], 'Off')].get_text())
        item['Total rebounds'] = int(team[get_col_index(boxscore_tables[-1], 'Reb')].get_text())
        item['Turnovers'] = int(team[get_col_index(boxscore_tables[-1], 'TO')].get_text())
        item['Personal fouls'] = int(team[get_col_index(boxscore_tables[-1], 'PF')].get_text())

        stat['items'] = item
        info['stats'].append(stat)

        # away
        players = boxscore_tables[0].find('tbody').find_all('tr')

        for player in players:
            cells = player.find_all('td')

            stat = {}
            stat['team'] = info['visitorTeam']['extid']

            stat['player_firstname'] = cells[get_col_index(boxscore_tables[0], 'Player')].get_text().split(' ')[0]
            stat['player_lastname'] = cells[get_col_index(boxscore_tables[0], 'Player')].get_text().split(' ')[-1]
            stat['player_name'] = cells[get_col_index(boxscore_tables[0], 'Player')].get_text()
            stat['player_extid'] = cells[get_col_index(boxscore_tables[0], 'Player')].find('a').get('href')

            item = {}
            item['2pts Attempts'] = int(cells[get_col_index(boxscore_tables[0], 'FGM-A')].get_text().split('-')[-1]) - int(cells[get_col_index(boxscore_tables[-1], '3PM-A')].get_text().split('-')[-1])
            item['2pts Made'] = int(cells[get_col_index(boxscore_tables[0], 'FGM-A')].get_text().split('-')[0]) - int(cells[get_col_index(boxscore_tables[-1], '3PM-A')].get_text().split('-')[0])
            item['3pts Attempts'] = int(cells[get_col_index(boxscore_tables[0], '3PM-A')].get_text().split('-')[-1])
            item['3pts Made'] = int(cells[get_col_index(boxscore_tables[0], '3PM-A')].get_text().split('-')[0])
            item['Assists'] = int(cells[get_col_index(boxscore_tables[0], 'Ast')].get_text())
            item['Block Shots'] = int(cells[get_col_index(boxscore_tables[0], 'BLK')].get_text())
            item['Defensive rebounds'] = int(cells[get_col_index(boxscore_tables[0], 'Def')].get_text())
            item['FT Attempts'] = int(cells[get_col_index(boxscore_tables[0], 'FTM-A')].get_text().split('-')[-1])
            item['FT Made'] = int(cells[get_col_index(boxscore_tables[0], 'FTM-A')].get_text().split('-')[0])
            item['Minutes played'] = round(int(cells[get_col_index(boxscore_tables[0], 'Min')].get_text().split(':')[0]) + float(cells[get_col_index(boxscore_tables[-1], 'Min')].get_text().split(':')[1]) / 60)
            item['Offensive rebounds'] = int(cells[get_col_index(boxscore_tables[0], 'Off')].get_text())
            item['Personal fouls'] = int(cells[get_col_index(boxscore_tables[0], 'PF')].get_text())
            item['Points'] = int(cells[get_col_index(boxscore_tables[0], 'PTS')].get_text())
            item['Steals'] = int(cells[get_col_index(boxscore_tables[0], 'STL')].get_text())
            item['Total rebounds'] = int(cells[get_col_index(boxscore_tables[0], 'Reb')].get_text())
            item['Turnovers'] = int(cells[get_col_index(boxscore_tables[0], 'TO')].get_text())

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['visitorTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        item = {}
        team = boxscore_tables[-1].find('tfoot').find_all('tr')[1].find_all('th')
        item['Defensive rebounds'] = int(team[get_col_index(boxscore_tables[0], 'Def')].get_text())
        item['Offensive rebounds'] = int(team[get_col_index(boxscore_tables[0], 'Off')].get_text())
        item['Total rebounds'] = int(team[get_col_index(boxscore_tables[0], 'Reb')].get_text())
        item['Turnovers'] = int(team[get_col_index(boxscore_tables[0], 'TO')].get_text())
        item['Personal fouls'] = int(team[get_col_index(boxscore_tables[0], 'PF')].get_text())

        stat['items'] = item
        info['stats'].append(stat)
        
        return info
    else:
        return {'error': 'Something went wrong!'}
    
def get_player(extid):
    url = f'https://basketball.realgm.com{extid}'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    profile_box = soup.find('div', class_='profile-box')
    profile = profile_box.find('div', attrs={'style': 'float: left;'})
    
    info = {}
    info['name'] = profile.find('h2').get_text(';').split(';')[0].strip()
    info['firstname'] = info['name'].split(' ')[0]
    info['lastname'] = info['name'].split(' ')[-1]
    info['extid'] = extid
    info['source'] = url

    try:
        info['shirtNumber'] = profile.find('h2').get_text(';').split(';')[3].strip().replace('#', '')
    except:
        pass

    info['position'] = profile.find('h2').get_text(';').split(';')[1].strip()
    info['team'] = soup.find_all('div', class_='portal widget')[-1].find('a').get_text()

    items = profile.find_all('strong')

    for item in items:
        if item.get_text() == 'Height:':
            info['height'] =  re.search(r'(\d+)cm', item.next_sibling.get_text()).group(1)
        
        if item.get_text() == 'Weight:':
            info['weight'] = re.search(r'(\d+)kg', item.next_sibling.get_text()).group(1)

        if item.get_text() == 'Born:':
            info['dateOfBirth'] = datetime.strptime(item.find_next_sibling('a').get_text().strip().split('(')[0].strip(), '%b %d, %Y').strftime('%Y-%m-%d')

        if item.get_text() == 'Nationality:':
            info['nationality'] = item.find_next_sibling('a').get_text().strip()

    return info

def func_rgm(args):
    if args['f'] == 'schedule':
        games = get_schedule()

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(extid)
    elif args['f'] == 'player':
        extid = request.args.get('extid')

        return get_player(extid)
