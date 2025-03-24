from library import *

def get_schedule(season_alias):
    results = []
    feed = feedparser.parse(f'https://en.usports.ca/sports/mbkb/{season_alias}/schedule?print=rss')
    entries = feed.entries
    
    date_list = []

    for entry in entries:
        date_str = entry['updated'].split('T')[0]
        date_list.append(date_str)

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
    }
    response = requests.get(f'https://en.usports.ca/sports/mbkb/{season_alias}/schedule', headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='event-row')
        index = 0
        for item in items:
            game = {}
            game['competition'] = "Men's Basketball"
            game['playDate'] = date_list[index]
            game['round'] = ''
            game['state'] = 'confirmed'
            game['extid'] = ''
            game['source'] = ''
            
            links = item.find_all('a')

            for link in links:
                if link.text.strip() == 'Box Score':
                    game['state'] = 'result'
                    game['source'] = 'https://en.usports.ca' + link['href']

                    if season_alias[-1] == 'p':
                        game['extid'] = f"p-{link['href'].split('/')[-1].replace('.xml', '')}"
                    elif season_alias[-1] == 'c':
                        game['extid'] = f"c-{link['href'].split('/')[-1].replace('.xml', '')}"
                    else:
                        game['extid'] = f"o-{link['href'].split('/')[-1].replace('.xml', '')}"
                    break
            
            team_logos = item.find_all('img')
            game['visitorTeam'] = {
                'extid': team_logos[1].get('src').split('/')[-1].split('.')[0],
                'name': team_logos[1].get('alt').replace('team logo', '').strip()
            }

            game['homeTeam'] = {
                'extid': team_logos[0].get('src').split('/')[-1].split('.')[0],
                'name': team_logos[0].get('alt').replace('team logo', '').strip()
            }

            game['type'] = item.find('div', class_='col-12').find('div', class_='text-uppercase').text.strip()

            if game['state'] == 'result':
                team_rows = item.find_all('div', class_='row')
                game['visitorScores'] = {
                    'final': team_rows[1].find_all('div', class_='col-auto')[-1].text.strip()
                }
                game['homeScores'] = {
                    'final': team_rows[0].find_all('div', class_='col-auto')[-1].text.strip()
                }
                game['extid'] = f'{game["extid"]}-{game["type"]}'

            results.append(game)
            index += 1

    return results

def func_cancis(args):
    if args['f'] == 'schedule':
        games = []

        args['season'] = request.args.get('season')

        season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}'
        games.extend(get_schedule(season_alias))

        season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}p'
        games.extend(get_schedule(season_alias))

        season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}c'
        games.extend(get_schedule(season_alias))
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')
        args['season'] = request.args.get('season')

        if args['extid'][0] == 'p':
            season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}p'
        elif args['extid'][0] == 'c':
            season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}c'
        else:
            season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}'

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        response = requests.get(f'https://en.usports.ca/sports/mbkb/{season_alias}/boxscores/{args["extid"].split("-")[1]}.xml?view=boxscore', headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = args['extid']
            info['playDate'] = datetime.strftime(datetime.strptime(info['extid'].split('-')[1].split('_')[0], '%Y%m%d'), '%Y-%m-%d')
            info['source'] = response.url
            info['type'] = args['extid'].split('-')[2]

            linescore = soup.find('div', class_='linescore')
            rows = linescore.find_all('tr')

            info['visitorTeam'] = {
                'extid': parse_qs(urlparse(rows[1].th.a['href']).query)['id'][0],
                'name': rows[1].th.text.strip()
            }

            info['homeTeam'] = {
                'extid': parse_qs(urlparse(rows[2].th.a['href']).query)['id'][0],
                'name': rows[2].th.text.strip()
            }

            if args['extid'][0] == 'o':
                info['homeScores'] = {
                    'QT1': rows[2].find_all('td')[0].text,
                    'QT2': rows[2].find_all('td')[1].text,
                    'QT3': 0,
                    'QT4': 0,
                    'extra': 0,
                    'final': rows[2].find_all('td')[-1].text
                }

                extra_scores = rows[2].find_all('td')[2:-1]
            else:
                info['homeScores'] = {
                    'QT1': rows[2].find_all('td')[0].text,
                    'QT2': rows[2].find_all('td')[1].text,
                    'QT3': rows[2].find_all('td')[2].text,
                    'QT4': rows[2].find_all('td')[3].text,
                    'extra': 0,
                    'final': rows[2].find_all('td')[-1].text
                }

                extra_scores = rows[2].find_all('td')[4:-1]

            for score in extra_scores:
                info['homeScores']['extra'] += int(score.text)

            if args['extid'][0] == 'o':
                info['visitorScores'] = {
                    'QT1': rows[1].find_all('td')[0].text,
                    'QT2': rows[1].find_all('td')[1].text,
                    'QT3': 0,
                    'QT4': 0,
                    'extra': 0,
                    'final': rows[1].find_all('td')[-1].text
                }

                extra_scores = rows[1].find_all('td')[2:-1]
            else:
                info['visitorScores'] = {
                    'QT1': rows[1].find_all('td')[0].text,
                    'QT2': rows[1].find_all('td')[1].text,
                    'QT3': rows[1].find_all('td')[2].text,
                    'QT4': rows[1].find_all('td')[3].text,
                    'extra': 0,
                    'final': rows[1].find_all('td')[-1].text
                }

                extra_scores = rows[1].find_all('td')[4:-1]

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
                    if args['extid'][0] == 'p':
                        stat['player_extid'] = f"p-{parse_qs(urlparse(row.th.a['href']).query)['id'][0]}"
                    elif args['extid'][0] == 'c':
                        stat['player_extid'] = f"c-{parse_qs(urlparse(row.th.a['href']).query)['id'][0]}"
                    else:
                        stat['player_extid'] = f"o-{parse_qs(urlparse(row.th.a['href']).query)['id'][0]}"
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
                    if args['extid'][0] == 'p':
                        stat['player_extid'] = f"p-{parse_qs(urlparse(row.th.a['href']).query)['id'][0]}"
                    elif args['extid'][0] == 'c':
                        stat['player_extid'] = f"c-{parse_qs(urlparse(row.th.a['href']).query)['id'][0]}"
                    else:
                        stat['player_extid'] = f"o-{parse_qs(urlparse(row.th.a['href']).query)['id'][0]}"
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

        if args['extid'][0] == 'p':
            season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}p'
        elif args['extid'][0] == 'c':
            season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}c'
        else:
            season_alias = f'{args["season"]}-{str(int(args["season"]) + 1)[-2:]}'
        
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        response = requests.get(f'https://en.usports.ca/sports/mbkb/{season_alias}/players?id={args["extid"].split("-")[1]}', headers=headers)

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
