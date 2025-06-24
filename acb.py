from library import *

def get_schedule_by_game(url: str):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    cabecera_partido = soup.find('div', class_='cabecera_partido')
    info_elem = soup.find('div', class_='info')

    info = {}
    info['round'] = cabecera_partido.find('h2').get_text(strip=True).split('-')[0].strip()
    info['playDate'] = datetime.strptime(soup.find('div', class_='datos_evento').find('span', class_='roboto_bold').get_text(strip=True), '%d/%m/%Y').strftime('%Y-%m-%d')
    
    info['homeTeam'] = {
        'extid': cabecera_partido.find_all('h4')[0].get_text(strip=True),
        'name': cabecera_partido.find_all('h4')[0].get_text(strip=True)
    }

    info['visitorTeam'] = {
        'extid': cabecera_partido.find_all('h4')[1].get_text(strip=True),
        'name': cabecera_partido.find_all('h4')[1].get_text(strip=True)
    }

    info['state'] = 'Finished'

    info['homeScores'] = {
        'final': int(info_elem.find_all('div', class_='resultado')[0].get_text(strip=True))
    }

    info['visitorScores'] = {
        'final': int(info_elem.find_all('div', class_='resultado')[1].get_text(strip=True))
    }

    info['competition'] = cabecera_partido.find('h2').get_text(strip=True).split('-')[-1].strip()

    info['extid'] = url.split('/')[-1]
    info['source'] = url

    return info

def get_schedule(args):
    games = []

    season = args['season']
    
    url = f'https://www.acb.com/calendario/index/temporada_id/{season}'

    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        game_aticles = soup.find_all('article', class_='partido')
        game_links = []
        
        for article in game_aticles:
            try:
                link = 'https://www.acb.com' + article.find('a', attrs={'title': 'estadísticas'}).get('href')
                game_links.append(link)
            except:
                continue

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(get_schedule_by_game, game_links)

            for result in results:
                games.append(result)
            
    return games

def get_boxscore(extid):
    info = {}
    url = f'https://www.acb.com/partido/estadisticas/id/{extid}'
    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        cabecera_partido = soup.find('div', class_='cabecera_partido')
        info_elem = soup.find('div', class_='info')
        
        info['extid'] = extid
        info['source'] = url
        info['playDate'] = datetime.strptime(soup.find('div', class_='datos_evento').find('span', class_='roboto_bold').get_text(strip=True), '%d/%m/%Y').strftime('%Y-%m-%d')

        info['homeTeam'] = {
            'extid': cabecera_partido.find_all('h4')[0].get_text(strip=True),
            'name': cabecera_partido.find_all('h4')[0].get_text(strip=True)
        }

        info['visitorTeam'] = {
            'extid': cabecera_partido.find_all('h4')[1].get_text(strip=True),
            'name': cabecera_partido.find_all('h4')[1].get_text(strip=True)
        }

        result_table = info_elem.find('table')

        info['homeScores'] = {
            'QT1': int(result_table.find('tbody').find_all('tr')[0].find_all('td')[get_col_index(result_table, '1')].get_text(strip=True)),
            'QT2': int(result_table.find('tbody').find_all('tr')[0].find_all('td')[get_col_index(result_table, '2')].get_text(strip=True)),
            'QT3': int(result_table.find('tbody').find_all('tr')[0].find_all('td')[get_col_index(result_table, '3')].get_text(strip=True)),
            'QT4': int(result_table.find('tbody').find_all('tr')[0].find_all('td')[get_col_index(result_table, '4')].get_text(strip=True)),
            'extra': 0,
            'final': int(info_elem.find_all('div', class_='resultado')[0].get_text(strip=True))
        }
        info['homeScores']['extra'] = info['homeScores']['final'] - info['homeScores']['QT1'] - info['homeScores']['QT2'] - info['homeScores']['QT3'] - info['homeScores']['QT4']

        info['visitorScores'] = {
            'QT1': int(result_table.find('tbody').find_all('tr')[1].find_all('td')[get_col_index(result_table, '1')].get_text(strip=True)),
            'QT2': int(result_table.find('tbody').find_all('tr')[1].find_all('td')[get_col_index(result_table, '2')].get_text(strip=True)),
            'QT3': int(result_table.find('tbody').find_all('tr')[1].find_all('td')[get_col_index(result_table, '3')].get_text(strip=True)),
            'QT4': int(result_table.find('tbody').find_all('tr')[1].find_all('td')[get_col_index(result_table, '4')].get_text(strip=True)),
            'extra': 0,
            'final': int(info_elem.find_all('div', class_='resultado')[1].get_text(strip=True))
        }
        info['visitorScores']['extra'] = info['visitorScores']['final'] - info['visitorScores']['QT1'] - info['visitorScores']['QT2'] - info['visitorScores']['QT3'] - info['visitorScores']['QT4']


        # Stats
        info['stats'] = []

        score_tables = soup.find_all('table', attrs={'data-toggle': 'table-estadisticas'})

        home_players = score_tables[0].find('tbody').find_all('tr')[:-4]

        for player in home_players:
            cells = player.find_all('td')

            stat = {}
            stat['team'] = info['homeTeam']['extid']

            player_link = 'https://www.acb.com' + cells[get_col_index(score_tables[0], 'Nombre')].find('a').get('href')
            player_resp = requests.get(player_link)
            player_soup = BeautifulSoup(player_resp.text, 'html.parser')

            stat['player_name'] = player_soup.find('h1').get_text(strip=True).strip()
            stat['player_extid'] = player_resp.url.split('/')[-1]

            item = {}
            item['2pts Attempts'] = int(cells[get_col_index(score_tables[0], 'T2')].get_text(strip=True).split('/')[-1] or 0)
            item['2pts Made'] = int(cells[get_col_index(score_tables[0], 'T2')].get_text(strip=True).split('/')[0] or 0)
            item['3pts Attempts'] = int(cells[get_col_index(score_tables[0], 'T3')].get_text(strip=True).split('/')[-1] or 0)
            item['3pts Made'] = int(cells[get_col_index(score_tables[0], 'T3')].get_text(strip=True).split('/')[0] or 0)
            item['Assists'] = int(cells[get_col_index(score_tables[0], 'A')].get_text(strip=True) or 0)
            item['Block Shots'] = int(cells[get_col_index(score_tables[0], 'F')].get_text(strip=True) or 0)
            item['Defensive rebounds'] = int(cells[get_col_index(score_tables[0], 'D+O')].get_text(strip=True).split('+')[0] or 0)
            item['Offensive rebounds'] = int(cells[get_col_index(score_tables[0], 'D+O')].get_text(strip=True).split('+')[-1] or 0)
            item['Total rebounds'] = int(cells[get_col_index(score_tables[0], 'T')].get_text(strip=True) or 0)
            item['FT Attempts'] = int(cells[get_col_index(score_tables[0], 'T1')].get_text(strip=True).split('/')[-1] or 0)
            item['FT Made'] = int(cells[get_col_index(score_tables[0], 'T1')].get_text(strip=True).split('/')[0] or 0)
            item['Minutes played'] = round(int(cells[get_col_index(score_tables[0], 'Min')].get_text(strip=True).split(':')[0] or 0) + float(cells[get_col_index(score_tables[0], 'Min')].get_text(strip=True).split(':')[-1] or 0) / 60)
            item['Personal fouls'] = int(cells[get_col_index(score_tables[0], 'F', False)].get_text(strip=True) or 0)
            item['Points'] = int(cells[get_col_index(score_tables[0], 'P')].get_text(strip=True) or 0)
            item['Steals'] = int(cells[get_col_index(score_tables[0], 'BR')].get_text(strip=True) or 0)
            item['Turnovers'] = int(cells[get_col_index(score_tables[0], 'BP')].get_text(strip=True) or 0)

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['homeTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        item = {}
        cells = score_tables[0].find('tbody').find('tr', class_='equipo').find_all('td')
        
        item['Defensive rebounds'] = int(cells[get_col_index(score_tables[0], 'D+O')].get_text(strip=True).split('+')[0] or 0)
        item['Offensive rebounds'] = int(cells[get_col_index(score_tables[0], 'D+O')].get_text(strip=True).split('+')[-1] or 0)
        item['Total rebounds'] = int(cells[get_col_index(score_tables[0], 'T')].get_text(strip=True) or 0)
        item['Turnovers'] = int(cells[get_col_index(score_tables[0], 'BP')].get_text(strip=True) or 0)
        item['Personal fouls'] = int(cells[get_col_index(score_tables[0], 'F', False)].get_text(strip=True) or 0)

        stat['items'] = item
        info['stats'].append(stat)

        away_players = score_tables[1].find('tbody').find_all('tr')[:-4]

        for player in away_players:
            cells = player.find_all('td')

            stat = {}
            stat['team'] = info['visitorTeam']['extid']

            player_link = 'https://www.acb.com' + cells[get_col_index(score_tables[1], 'Nombre')].find('a').get('href')
            player_resp = requests.get(player_link)
            player_soup = BeautifulSoup(player_resp.text, 'html.parser')

            stat['player_name'] = player_soup.find('div', class_='contenedora_datos_secundarios').find('div').find('span').get_text(strip=True)
            stat['player_extid'] = player_resp.url.split('/')[-1]

            item = {}
            item['2pts Attempts'] = int(cells[get_col_index(score_tables[1], 'T2')].get_text(strip=True).split('/')[-1] or 0)
            item['2pts Made'] = int(cells[get_col_index(score_tables[1], 'T2')].get_text(strip=True).split('/')[0] or 0)
            item['3pts Attempts'] = int(cells[get_col_index(score_tables[1], 'T3')].get_text(strip=True).split('/')[-1] or 0)
            item['3pts Made'] = int(cells[get_col_index(score_tables[1], 'T3')].get_text(strip=True).split('/')[0] or 0)
            item['Assists'] = int(cells[get_col_index(score_tables[1], 'A')].get_text(strip=True) or 0)
            item['Block Shots'] = int(cells[get_col_index(score_tables[1], 'F')].get_text(strip=True) or 0)
            item['Defensive rebounds'] = int(cells[get_col_index(score_tables[1], 'D+O')].get_text(strip=True).split('+')[0] or 0)
            item['Offensive rebounds'] = int(cells[get_col_index(score_tables[1], 'D+O')].get_text(strip=True).split('+')[-1] or 0)
            item['Total rebounds'] = int(cells[get_col_index(score_tables[1], 'T')].get_text(strip=True) or 0)
            item['FT Attempts'] = int(cells[get_col_index(score_tables[1], 'T1')].get_text(strip=True).split('/')[-1] or 0)
            item['FT Made'] = int(cells[get_col_index(score_tables[1], 'T1')].get_text(strip=True).split('/')[0] or 0)
            item['Minutes played'] = round(int(cells[get_col_index(score_tables[1], 'Min')].get_text(strip=True).split(':')[0] or 0) + float(cells[get_col_index(score_tables[1], 'Min')].get_text(strip=True).split(':')[-1] or 0) / 60)
            item['Personal fouls'] = int(cells[get_col_index(score_tables[1], 'F', False)].get_text(strip=True) or 0)
            item['Points'] = int(cells[get_col_index(score_tables[1], 'P')].get_text(strip=True) or 0)
            item['Steals'] = int(cells[get_col_index(score_tables[1], 'BR')].get_text(strip=True) or 0)
            item['Turnovers'] = int(cells[get_col_index(score_tables[1], 'BP')].get_text(strip=True) or 0)

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['visitorTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        item = {}
        cells = score_tables[1].find('tbody').find('tr', class_='equipo').find_all('td')
        item['Defensive rebounds'] = int(cells[get_col_index(score_tables[1], 'D+O')].get_text(strip=True).split('+')[0] or 0)
        item['Offensive rebounds'] = int(cells[get_col_index(score_tables[1], 'D+O')].get_text(strip=True).split('+')[-1] or 0)
        item['Total rebounds'] = int(cells[get_col_index(score_tables[1], 'T')].get_text(strip=True) or 0)
        item['Turnovers'] = int(cells[get_col_index(score_tables[1], 'BP')].get_text(strip=True) or 0)
        item['Personal fouls'] = int(cells[get_col_index(score_tables[1], 'F', False)].get_text(strip=True) or 0)

        stat['items'] = item
        info['stats'].append(stat)

    return info
    
def get_player(extid):
    info = {}

    url = f'https://www.acb.com/jugador/temporada-a-temporada/id/{extid}'
    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')

        info['name'] = soup.find('div', class_='contenedora_datos_secundarios').find('div').find('span').get_text(strip=True)
        info['extid'] = extid
        info['source'] = url
        info['position'] = soup.find('div', class_='posicion').find('span').get_text(strip=True)
        info['dateOfBirth'] = datetime.strptime(re.search(r'\d{2}/\d{2}/\d{4}', soup.find('div', class_='fecha_nacimiento').find('span', class_='roboto_condensed_bold').get_text(strip=True)).group(0), '%d/%m/%Y').strftime('%Y-%m-%d')
        info['placeOfBirth'] = soup.find('div', class_='lugar_nacimiento').find('span', class_='roboto_condensed_bold').get_text(strip=True)
        info['height'] = int(float(soup.find('div', class_='altura').find('span').get_text(strip=True).replace('m', '').replace(',', '.')) * 100)
        info['nationality'] = soup.find('div', class_='nacionalidad').find('span', class_='roboto_condensed_bold').get_text(strip=True)

    return info

def func_acb(args):
    if args['f'] == 'schedule':
        games = []
        schedule = get_schedule(args)
        games.extend(schedule)
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'])
    elif args['f'] == 'player':
        return get_player(args['extid'])
    