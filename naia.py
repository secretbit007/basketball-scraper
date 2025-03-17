from library import *

def func_naia(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}'

        feed = feedparser.parse(f'https://naiastats.prestosports.com/sports/mbkb/{season_alias}/schedule?print=rss')
        entries = feed.entries
        
        date_list = []

        for entry in entries:
            date_str = entry['updated'].split('T')[0]

            if date_str not in date_list:
                date_list.append(date_str)

        games = []

        def get_info(date_str):
            response = requests.get(f'https://naiastats.prestosports.com/sports/mbkb/scoreboard?d={date_str}&ajax=true')

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('div', class_='event-box')

                for item in items:
                    game = {}
                    game['competition'] = "Men's Basketball"
                    game['playDate'] = date_str
                    game['round'] = ''
                    game['state'] = 'confirmed'
                    game['extid'] = ''
                    game['source'] = ''
                    
                    links = item.find('div', class_='links').find_all('a')

                    for link in links:
                        if link.text.strip() == 'Box Score':
                            game['state'] = 'result'
                            game['source'] = 'https://naiastats.prestosports.com' + link['href']
                            game['extid'] = link['href'].split('/')[-1].replace('.xml', '')
                            break

                    event_info = item.find('div', class_='event-info')
                    teams = event_info.find_all('div', class_='team')

                    game['visitorTeam'] = {
                        'name': teams[0].find('span', class_='team-name')['title'],
                    }

                    if '@' in game['visitorTeam']['name']:
                        game['visitorTeam']['name'] = re.search('(.+)@', game['visitorTeam']['name']).group(1).strip()

                    game['visitorTeam']['extid'] = game['visitorTeam']['name'].lower().replace(' ', '').replace('-', '').replace('.', '').replace(',', '').replace('(', '').replace(')', '')

                    game['homeTeam'] = {
                        'name': teams[1].find('span', class_='team-name')['title'],
                    }

                    if '@' in game['homeTeam']['name']:
                        game['homeTeam']['name'] = re.search('(.+)@', game['homeTeam']['name']).group(1).strip()

                    game['homeTeam']['extid'] = game['homeTeam']['name'].lower().replace(' ', '').replace('-', '').replace('.', '').replace(',', '').replace('(', '').replace(')', '')

                    game['type'] = ''

                    notation = teams[0].find('span', class_='notation')
                    if notation:
                        game['type'] = notation['title']

                    if game['state'] == 'result':
                        game['visitorScores'] = {
                            'final': teams[0].find('span', class_='result').text.strip()
                        }
                        game['homeScores'] = {
                            'final': teams[1].find('span', class_='result').text.strip()
                        }
                        game['extid'] = f'{game["extid"]}-{game["type"]}'

                    games.append(game)

        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(get_info, date_list)

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')
        args['season'] = request.args.get('season')
        season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}'

        response = requests.get(f'https://naiastats.prestosports.com/sports/mbkb/{season_alias}/boxscores/{args["extid"].split("-")[0]}.xml?view=boxscore')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = args['extid']
            info['playDate'] = datetime.strftime(datetime.strptime(info['extid'].split('-')[0].split('_')[0], '%Y%m%d'), '%Y-%m-%d')
            info['source'] = response.url
            info['type'] = args['extid'].split('-')[1]

            linescore = soup.find('div', class_='linescore')
            rows = linescore.find_all('tr')

            info['visitorTeam'] = {
                'name': rows[1].th.text.strip()
            }

            if '@' in info['visitorTeam']['name']:
                info['visitorTeam']['name'] = re.search('(.+)@', info['visitorTeam']['name']).group(1).strip()

            info['visitorTeam']['extid'] = info['visitorTeam']['name'].lower().replace(' ', '').replace('-', '').replace('.', '').replace(',', '').replace('(', '').replace(')', '')

            info['homeTeam'] = {
                'name': rows[2].th.text.strip(),
            }

            if '@' in info['homeTeam']['name']:
                info['homeTeam']['name'] = re.search('(.+)@', info['homeTeam']['name']).group(1).strip()

            info['homeTeam']['extid'] = info['homeTeam']['name'].lower().replace(' ', '').replace('-', '').replace('.', '').replace(',', '').replace('(', '').replace(')', '')

            info['homeScores'] = {
                'QT1': rows[2].find_all('td')[0].text,
                'QT2': rows[2].find_all('td')[1].text,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': rows[2].find_all('td')[-1].text
            }

            extra_scores = rows[2].find_all('td')[2:-1]

            for score in extra_scores:
                info['homeScores']['extra'] += int(score.text)

            info['visitorScores'] = {
                'QT1': rows[1].find_all('td')[0].text,
                'QT2': rows[1].find_all('td')[1].text,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': rows[1].find_all('td')[-1].text
            }

            extra_scores = rows[1].find_all('td')[2:-1]

            for score in extra_scores:
                info['visitorScores']['extra'] += int(score.text)

            info['stats'] = []
            # home
            table = soup.find('div', {'data-panel-for': 'team-label-boxscore-h'})
            rows = table.find_all('tr', {'class': None})

            for row in rows[1:-1]:
                stat = {}
                stat['team'] = info['homeTeam']['extid']

                try:                
                    stat['player_extid'] = parse_qs(urlparse(row.th.a['href']).query)['id'][0]
                except TypeError:
                    stat['player_extid'] = ''
                
                try:
                    stat['player_name'] = row.find(class_='player-name').text.strip()
                except AttributeError:
                    continue

                stat['player_firstname'] = stat['player_name'].split(' ')[0].strip()

                try:
                    stat['player_lastname'] = stat['player_name'].split(' ')[1].strip()
                except IndexError:
                    stat['player_lastname'] = ''

                item = {}
                item['3pts Attempts'] = row.find_all('td')[2].text.split('-')[1].strip()
                item['3pts Made'] = row.find_all('td')[2].text.split('-')[0].strip()
                item['2pts Attempts'] = int(row.find_all('td')[1].text.split('-')[1]) - int(item['3pts Attempts'])
                item['2pts Made'] = int(row.find_all('td')[1].text.split('-')[0]) - int(item['3pts Made'])
                item['Assists'] = row.find_all('td')[7].text.strip()
                item['Block Shots'] = row.find_all('td')[9].text.strip()
                item['Defensive rebounds'] = row.find_all('td')[5].text.strip()
                item['FT Attempts'] = row.find_all('td')[3].text.split('-')[1].strip()
                item['FT Made'] = row.find_all('td')[3].text.split('-')[0].strip()
                item['Minutes played'] = row.find_all('td')[0].text.strip()
                item['Offensive rebounds'] = row.find_all('td')[4].text.strip()
                item['Personal fouls'] = row.find_all('td')[11].text.strip()
                item['Points'] = row.find_all('td')[12].text.strip()
                item['Steals'] = row.find_all('td')[8].text.strip()
                item['Total rebounds'] = row.find_all('td')[6].text.strip()
                item['Turnovers'] = row.find_all('td')[10].text.strip()

                stat['items'] = item
                info['stats'].append(stat)

            stat = {}
            stat['team'] = info['homeTeam']['extid']
            stat['player_extid'] = 'team'
            stat['player_firstname'] = ''
            stat['player_lastname'] = '- TEAM -'
            stat['player_name'] = '- TEAM -'

            item = {}
            item['Total rebounds'] = rows[-1].find_all('td')[6].text.strip()
            item['Defensive rebounds'] = rows[-1].find_all('td')[5].text.strip()
            item['Offensive rebounds'] = rows[-1].find_all('td')[4].text.strip()
            item['Personal fouls'] = rows[-1].find_all('td')[11].text.strip()
            item['Turnovers'] = rows[-1].find_all('td')[10].text.strip()

            stat['items'] = item
            info['stats'].append(stat)

            # away
            table = soup.find('div', {'data-panel-for': 'team-label-boxscore-v'})
            rows = table.find_all('tr', {'class': None})

            for row in rows[1:-1]:
                stat = {}
                stat['team'] = info['visitorTeam']['extid']

                try:
                    stat['player_extid'] = parse_qs(urlparse(row.th.a['href']).query)['id'][0]
                except TypeError:
                    stat['player_extid'] = ''

                try:
                    stat['player_name'] = row.find(class_='player-name').text.strip()
                except AttributeError:
                    continue
                
                stat['player_firstname'] = stat['player_name'].split(' ')[0].strip()

                try:
                    stat['player_lastname'] = stat['player_name'].split(' ')[1].strip()
                except IndexError:
                    stat['player_lastname'] = ''

                item = {}
                item['3pts Attempts'] = row.find_all('td')[2].text.split('-')[1].strip()
                item['3pts Made'] = row.find_all('td')[2].text.split('-')[0].strip()
                item['2pts Attempts'] = int(row.find_all('td')[1].text.split('-')[1]) - int(item['3pts Attempts'])
                item['2pts Made'] = int(row.find_all('td')[1].text.split('-')[0]) - int(item['3pts Made'])
                item['Assists'] = row.find_all('td')[7].text.strip()
                item['Block Shots'] = row.find_all('td')[9].text.strip()
                item['Defensive rebounds'] = row.find_all('td')[5].text.strip()
                item['FT Attempts'] = row.find_all('td')[3].text.split('-')[1].strip()
                item['FT Made'] = row.find_all('td')[3].text.split('-')[0].strip()
                item['Minutes played'] = row.find_all('td')[0].text.strip()
                item['Offensive rebounds'] = row.find_all('td')[4].text.strip()
                item['Personal fouls'] = row.find_all('td')[11].text.strip()
                item['Points'] = row.find_all('td')[12].text.strip()
                item['Steals'] = row.find_all('td')[8].text.strip()
                item['Total rebounds'] = row.find_all('td')[6].text.strip()
                item['Turnovers'] = row.find_all('td')[10].text.strip()

                stat['items'] = item
                info['stats'].append(stat)

            stat = {}
            stat['team'] = info['visitorTeam']['extid']
            stat['player_extid'] = 'team'
            stat['player_firstname'] = ''
            stat['player_lastname'] = '- TEAM -'
            stat['player_name'] = '- TEAM -'

            item = {}
            item['Total rebounds'] = rows[-1].find_all('td')[6].text.strip()
            item['Defensive rebounds'] = rows[-1].find_all('td')[5].text.strip()
            item['Offensive rebounds'] = rows[-1].find_all('td')[4].text.strip()
            item['Personal fouls'] = rows[-1].find_all('td')[11].text.strip()
            item['Turnovers'] = rows[-1].find_all('td')[10].text.strip()

            stat['items'] = item
            info['stats'].append(stat)

            return info
    elif args['f'] == 'player':
        args['extid'] = request.args.get('extid')
        args['season'] = request.args.get('season')
        season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}'
        
        response = requests.get(f'https://naiastats.prestosports.com/sports/mbkb/{season_alias}/players?id={args["extid"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            info = {}
            info['name'] = soup.find('h2', class_='player-name').find_all('span')[0].text.strip()
            info['firstname'] = info['name'].split(' ')[0].strip()
            info['lastname'] = info['name'].split(' ')[1].strip()
            info['extid'] = args['extid']
            info['source'] = response.url
            info['shirtNumber'] = soup.find('h2', class_='player-name').find_all('span')[1].text.strip().replace('#', '')
            info['position'] = soup.find('h2', class_='player-name').find_all('span')[2].text.strip()
            info['team'] = soup.find('h2', class_='player-name').find('a').text.strip()

            return info
