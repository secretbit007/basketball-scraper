from library import *

def get_schedule(spar):
    games = []
    locale.setlocale(locale.LC_ALL, 'pt_PT.utf8')
    
    today = datetime.today().date()
    delta = timedelta(days=29)
    
    to_date = today
    from_date = today - delta
    
    # Results
    while True:
        url_results = f"https://www.fpb.pt/wp-admin/admin-ajax.php?action=get_results&competicao[]={spar}&period[time_option]=loadmore&period[from_date]={from_date.strftime('%Y/%m/%d')}&period[to_date]={to_date.strftime('%Y/%m/%d')}"
        resp_results = requests.get(url_results)
        results = resp_results.json()['result']
        
        if type(results) == str:
            soup_result = BeautifulSoup(results, 'html.parser')
            if soup_result.text.strip() == 'SEM RESULTADOS':
                break
            
        for result in results:
            soup_result = BeautifulSoup(result, 'html.parser')
            match_date = datetime.strptime(soup_result.find('h3', class_='date').text.strip(), '%d %b %Y')
            
            matches = soup_result.find_all('a', class_='game-wrapper-a')
            
            for match in matches:
                if match.find('h3', class_='results_text').text.strip() == '':
                    continue
                
                game = {}
                game['competition'] = 'FPB'
                game['playDate'] = match_date.strftime('%Y-%m-%d')
                game['round'] = '-'
                game['state'] = 'Finished'
                game['type'] = 'Regular'
                
                teams = match.find_all('div', class_='team-container')
                scores = match.find_all('h3', class_='results_text')
                
                game['homeTeam'] = {
                    'extid': slugify(teams[0].find('span', class_='fullName').text.strip(), allow_unicode=True),
                    'name': teams[0].find('span', class_='fullName').text.strip()
                }
                game['homeScores'] = {
                    'final': int(scores[0].text.strip())
                }
                
                game['visitorTeam'] = {
                    'extid': slugify(teams[1].find('span', class_='fullName').text.strip(), allow_unicode=True),
                    'name': teams[1].find('span', class_='fullName').text.strip()
                }
                game['visitorScores'] = {
                    'final': int(scores[1].text.strip())
                }

                game['extid'] = parse_qs(urlparse(match['href']).query)['internalID'][0]
                game['source'] = f"https://www.fpb.pt{match['href']}"
                games.append(game)
        
        to_date = from_date - timedelta(days=1)
        from_date = to_date - delta
        
    from_date = today
    to_date = today + delta
    
    # Schedule
    while True:
        url_schedule = f"https://www.fpb.pt/wp-admin/admin-ajax.php?action=get_more_days&competicao[]=9861&period[time_option]=loadmore&period[from_date]={from_date}&period[to_date]={to_date}"
        resp_schedule = requests.get(url_schedule)
        results = resp_schedule.json()['result']
        
        if type(results) == str:
            soup_result = BeautifulSoup(results, 'html.parser')
            if soup_result.text.strip() == 'SEM RESULTADOS':
                break
            
        for result in results:
            soup_result = BeautifulSoup(result, 'html.parser')
            match_date = datetime.strptime(soup_result.find('h3', class_='date').text.strip(), '%d %b %Y')
            
            matches = soup_result.find_all('a', class_='game-wrapper-a')
            
            for match in matches:
                game = {}
                game['competition'] = 'FPB'
                game['playDate'] = match_date.strftime('%Y-%m-%d')
                game['round'] = '-'
                game['state'] = 'Scheduled'
                game['type'] = 'Regular'
                
                teams = match.find_all('div', class_='team-container')
                
                game['homeTeam'] = {
                    'extid': slugify(teams[0].find('span', class_='fullName').text.strip(), allow_unicode=True),
                    'name': teams[0].find('span', class_='fullName').text.strip()
                }
                game['homeScores'] = {
                    'final': 0
                }
                
                game['visitorTeam'] = {
                    'extid': slugify(teams[1].find('span', class_='fullName').text.strip(), allow_unicode=True),
                    'name': teams[1].find('span', class_='fullName').text.strip()
                }
                game['visitorScores'] = {
                    'final': 0
                }

                game['extid'] = parse_qs(urlparse(match['href']).query)['internalID'][0]
                game['source'] = f"https://www.fpb.pt{match['href']}"
                games.append(game)
        
        from_date = to_date + timedelta(days=1)
        to_date = from_date + delta
        
    locale.setlocale(locale.LC_ALL, '')
    return games

def get_boxscore(extid):
    locale.setlocale(locale.LC_ALL, 'pt_PT.utf8')
    suffices = ['ii', 'iii', 'iv', 'v', 'jr']
    
    url = f'https://www.fpb.pt/ficha-de-jogo/?internalID={extid}'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    info = {}
    info['extid'] = extid
    info['playDate'] = datetime.strptime(soup.find('p', class_='date').text, '%d %b %Y').strftime('%Y-%m-%d')
    info['source'] = f'https://www.fpb.pt/ficha-de-jogo/?internalID={extid}'
    info['type'] = soup.find('p', class_='phase').text
    
    info['homeTeam'] = {
        'extid': slugify(soup.find('div', class_='home').find('p', class_='bigName').text.strip(), allow_unicode=True),
        'name': soup.find('div', class_='home').find('p', class_='bigName').text.strip()
    }
    
    info['visitorTeam'] = {
        'extid': slugify(soup.find('div', class_='away').find('p', class_='bigName').text.strip(), allow_unicode=True),
        'name': soup.find('div', class_='away').find('p', class_='bigName').text.strip()
    }

    info['homeScores'] = {
        'QT1': 0,
        'QT2': 0,
        'QT3': 0,
        'QT4': 0,
        'extra': 0,
        'final': 0
    }
    info['visitorScores'] = {
        'QT1': 0,
        'QT2': 0,
        'QT3': 0,
        'QT4': 0,
        'extra': 0,
        'final': 0
    }

    info['stats'] = []
    
    if soup.find('div', class_='points').find('div', class_='dash'):
        scores = soup.find('div', class_='points').find_all('span')
        periods = soup.find_all('div', class_='match-period')[:4]
        
        info['homeScores']['final'] = int(scores[0].text)
        info['homeScores']['QT1'] = int(periods[0].find_all('span')[0].text)
        info['homeScores']['QT2'] = int(periods[1].find_all('span')[0].text)
        info['homeScores']['QT3'] = int(periods[2].find_all('span')[0].text)
        info['homeScores']['QT4'] = int(periods[3].find_all('span')[0].text)
        info['homeScores']['extra'] = info['homeScores']['final'] - (info['homeScores']['QT1'] + info['homeScores']['QT2'] + info['homeScores']['QT3'] + info['homeScores']['QT4'])
            
        info['visitorScores']['final'] = int(scores[1].text)
        info['visitorScores']['QT1'] = int(periods[0].find_all('span')[1].text)
        info['visitorScores']['QT2'] = int(periods[1].find_all('span')[1].text)
        info['visitorScores']['QT3'] = int(periods[2].find_all('span')[1].text)
        info['visitorScores']['QT4'] = int(periods[3].find_all('span')[1].text)
        info['visitorScores']['extra'] = info['visitorScores']['final'] - (info['visitorScores']['QT1'] + info['visitorScores']['QT2'] + info['visitorScores']['QT3'] + info['visitorScores']['QT4'])

        stats = soup.find_all('div', class_='team-players-table-wrapper')
        
        # home
        tables = stats[0].find('div', class_='table-wrapper').find_all('table')
        players = tables[0].find_all('tr')[1:-1]
        values = tables[1].find_all('tr')[1:-1]

        for index in range(len(players[:-1])):
            player = players[index]
            value = values[index]
            cells = value.find_all('td')
            
            stat = {}
            stat['team'] = info['homeTeam']['extid']
            stat['player_name'] = player.find('td', class_='name').text.strip()
            
            suffix = '-'
            if stat['player_name'].split(' ')[-1].lower().replace('.', '') in suffices:
                suffix = stat['player_name'].split(' ')[-1]
                
            if len(stat['player_name'].replace(suffix, '').strip().split(' ')) == 1:
                stat['player_firstname'] = stat['player_name'].replace(suffix, '').strip()
                stat['player_lastname'] = '-'
            else:
                if suffix != '-':
                    stat['player_firstname'] = ' '.join(stat['player_name'].replace(suffix, '').strip().split(' ')[1:])
                    stat['player_lastname'] = stat['player_name'].replace(suffix, '').strip().split(' ')[0]
                else:
                    stat['player_firstname'] = ' '.join(stat['player_name'].replace(suffix, '').strip().split(' ')[:-1])
                    stat['player_lastname'] = stat['player_name'].replace(suffix, '').strip().split(' ')[-1]
            
            try:
                stat['player_extid'] = f"{player.find('td', class_='name').find('a')['href'].split('/')[-1]}_{stat['player_name']}"
            except:
                stat['player_extid'] = f'-_{stat["player_name"]}'

            item = {}
            item['2pts Attempts'] = int(cells[2].text.split('/')[1])
            item['2pts Made'] = int(cells[2].text.split('/')[0])
            item['3pts Attempts'] = int(cells[4].text.split('/')[1])
            item['3pts Made'] = int(cells[4].text.split('/')[0])
            item['Assists'] = int(cells[11].text)
            item['Block Shots'] = int(cells[14].text)
            item['Defensive rebounds'] = int(cells[9].text)
            item['Offensive rebounds'] = int(cells[8].text)
            item['Total rebounds'] = int(cells[10].text)
            item['FT Attempts'] = int(cells[6].text.split('/')[1])
            item['FT Made'] = int(cells[6].text.split('/')[0])
            item['Minutes played'] = round(int(cells[0].text.split(':')[0]) + int(cells[0].text.split(':')[1]) / 60)
            item['Personal fouls'] = int(cells[15].text)
            item['Points'] = int(cells[1].text)
            item['Steals'] = int(cells[12].text)
            item['Turnovers'] = int(cells[13].text)

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['homeTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'
        
        item = {}
        cells = values[-1].find_all('td')[1:-1]
        item['Defensive rebounds'] = int(cells[1].text.strip())
        item['Offensive rebounds'] = int(cells[0].text.strip())
        item['Total rebounds'] = int(cells[2].text.strip())
        item['Turnovers'] = int(cells[5].text.strip())
        item['Personal fouls'] = int(cells[7].text.strip())

        stat['items'] = item

        info['stats'].append(stat)

        # away
        tables = stats[1].find('div', class_='table-wrapper').find_all('table')
        players = tables[0].find_all('tr')[1:-1]
        values = tables[1].find_all('tr')[1:-1]

        for index in range(len(players[:-1])):
            player = players[index]
            value = values[index]
            cells = value.find_all('td')
            
            stat = {}
            stat['team'] = info['visitorTeam']['extid']
            stat['player_name'] = player.find('td', class_='name').text.strip()
            
            suffix = '-'
            if stat['player_name'].split(' ')[-1].lower().replace('.', '') in suffices:
                suffix = stat['player_name'].split(' ')[-1]
                
            if len(stat['player_name'].replace(suffix, '').strip().split(' ')) == 1:
                stat['player_firstname'] = stat['player_name'].replace(suffix, '').strip()
                stat['player_lastname'] = '-'
            else:
                if suffix != '-':
                    stat['player_firstname'] = ' '.join(stat['player_name'].replace(suffix, '').strip().split(' ')[1:])
                    stat['player_lastname'] = stat['player_name'].replace(suffix, '').strip().split(' ')[0]
                else:
                    stat['player_firstname'] = ' '.join(stat['player_name'].replace(suffix, '').strip().split(' ')[:-1])
                    stat['player_lastname'] = stat['player_name'].replace(suffix, '').strip().split(' ')[-1]
            
            try:
                stat['player_extid'] = f"{player.find('td', class_='name').find('a')['href'].split('/')[-1]}_{stat['player_name']}"
            except:
                stat['player_extid'] = f'-_{stat["player_name"]}'

            item = {}
            item['2pts Attempts'] = int(cells[2].text.split('/')[1])
            item['2pts Made'] = int(cells[2].text.split('/')[0])
            item['3pts Attempts'] = int(cells[4].text.split('/')[1])
            item['3pts Made'] = int(cells[4].text.split('/')[0])
            item['Assists'] = int(cells[11].text)
            item['Block Shots'] = int(cells[14].text)
            item['Defensive rebounds'] = int(cells[9].text)
            item['Offensive rebounds'] = int(cells[8].text)
            item['Total rebounds'] = int(cells[10].text)
            item['FT Attempts'] = int(cells[6].text.split('/')[1])
            item['FT Made'] = int(cells[6].text.split('/')[0])
            item['Minutes played'] = round(int(cells[0].text.split(':')[0]) + int(cells[0].text.split(':')[1]) / 60)
            item['Personal fouls'] = int(cells[15].text)
            item['Points'] = int(cells[1].text)
            item['Steals'] = int(cells[12].text)
            item['Turnovers'] = int(cells[13].text)

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['visitorTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'
        
        item = {}
        cells = values[-1].find_all('td')[1:-1]
        item['Defensive rebounds'] = int(cells[1].text.strip())
        item['Offensive rebounds'] = int(cells[0].text.strip())
        item['Total rebounds'] = int(cells[2].text.strip())
        item['Turnovers'] = int(cells[5].text.strip())
        item['Personal fouls'] = int(cells[7].text.strip())

        stat['items'] = item

        info['stats'].append(stat)
    
    locale.setlocale(locale.LC_ALL, '')
    return info

def get_player(param):
    extid, name = param.split('_')
    
    if extid != '-':
        url = f'https://www.fpb.pt/atletas/{extid}/'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        suffices = ['ii', 'iii', 'iv', 'v', 'jr']
        
        info = {}
        info['name'] = name
        info['suffix'] = '-'
        
        if info['name'].split(' ')[-1].replace('.', '').lower() in suffices:
            info['suffix'] = info['name'].split(' ')[-1]
        
        if len(info['name'].replace(info['suffix'], '').strip().split(' ')) == 1:
            info['firstname'] = info['name'].replace(info['suffix'], '').strip()
            info['lastname'] = '-'
        else:
            if info['suffix'] != '-':
                info['firstname'] = ' '.join(info['name'].replace(info['suffix'], '').strip().split(' ')[1:])
                info['lastname'] = info['name'].replace(info['suffix'], '').strip().split(' ')[0]
            else:
                info['firstname'] = ' '.join(info['name'].replace(info['suffix'], '').strip().split(' ')[:-1])
                info['lastname'] = info['name'].replace(info['suffix'], '').strip().split(' ')[-1]
            
        info['extid'] = extid
        info['source'] = f'https://www.fpb.pt/atletas/{extid}/'
        info['shirtNumber'] = soup.find('div', class_='number').text.strip()
        info['team'] = soup.find('div', class_='base').find('p').text.strip().split(',')[-1].strip()
        
        infos = soup.find('div', class_='biografia-resume').find_all('div')
        
        for item in infos:
            title = item.find('p').text.strip()
            
            if title == 'Data de Nascimento':
                info['dateOfBirth'] = datetime.strptime(item.find('span').text, '%d/%m/%Y').strftime('%Y-%m-%d')
                
            if title == 'Nacionalidade':
                info['nationality'] = item.find('span').text.strip()
                
            if title == 'Posição':
                info['position'] = item.find('span').text.strip()
                
            if title == 'Altura':
                info['height'] = item.find('span').text.strip().replace('CM', '')
                
            if title == 'PESO':
                info['weight'] = item.find('span').text.strip().replace('KG', '')

        return info
    else:
        return {'message': 'no data'}

def func_fpb(args):
    if args['f'] == 'schedule':
        games = get_schedule(args['spar'])
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'])
    elif args['f'] == 'player':
        return get_player(args['extid'])