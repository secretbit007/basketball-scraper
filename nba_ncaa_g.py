from library import *

def get_schedule(lpar, season):
    games = []

    startDate = None
    endDate = None

    # Get season end date
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    if lpar == 'NBA':
        response = requests.get('https://www.espn.com/nba/schedule?_xhr=pageContent', headers=headers)
    elif lpar == 'G':
        response = requests.get('https://www.espn.com/nba-g-league/schedule?_xhr=pageContent', headers=headers)
    elif lpar == 'NCAA':
        response = requests.get('https://www.espn.com/mens-college-basketball/schedule?_xhr=pageContent', headers=headers)

    if response.status_code == 200:
        data = response.json()
        startDate = datetime.strptime(data['seasonList'][season]['startDate'], '%Y-%m-%dT%H:%MZ')
        endDate = datetime.strptime(data['seasonList'][season]['endDate'], '%Y-%m-%dT%H:%MZ')
        daylist = [startDate + timedelta(days=delta) for delta in range((endDate - startDate).days)]

        def get_info(day: datetime):
            if lpar == 'NBA':
                response = requests.get(f'https://www.espn.com/nba/schedule/_/date/{day.strftime("%Y%m%d")}?_xhr=pageContent&original=date%3D{day.strftime("%Y%m%d")}&date={day.strftime("%Y%m%d")}', headers=headers)
            elif lpar == 'G':
                response = requests.get(f'https://www.espn.com/nba-g-league/schedule/_/date/{day.strftime("%Y%m%d")}?_xhr=pageContent&original=date%3D{day.strftime("%Y%m%d")}&date={day.strftime("%Y%m%d")}', headers=headers)
            elif lpar == 'NCAA':
                response = requests.get(f'https://www.espn.com/mens-college-basketball/schedule/_/date/{day.strftime("%Y%m%d")}/group/50?_xhr=pageContent&original=date%3D{day.strftime("%Y%m%d")}&date={day.strftime("%Y%m%d")}', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                season_type = data['currentSeason']['name']
                league = data['league']['name']
                events = data['events']

                for key in events.keys():
                    for event in events[key]:
                        if datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ').date() != day.date():
                            continue
                        
                        game = {}
                        game['competition'] = league
                        game['playDate'] = datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ').strftime('%Y-%m-%d')
                        game['round'] = ''

                        if lpar == 'NBA':
                            game['source'] = f'https://www.espn.com/nba/game?gameId={event["id"]}'
                        elif lpar == 'G':
                            game['source'] = f'https://www.espn.com/nba-g-league/game?gameId={event["id"]}'
                        elif lpar == 'NCAA':
                            game['source'] = f'https://www.espn.com/mens-college-basketball/game?gameId={event["id"]}'

                        if event['completed'] == True:
                            game['state'] = 'result'
                        else:
                            game['state'] = 'confirmed'

                        game['type'] = season_type
                        
                        for competitor in event['competitors']:
                            if competitor['isHome'] == True:
                                game['homeTeam'] = {
                                    'extid': competitor['id'],
                                    'name': competitor['name']
                                }

                                if game['state'] == 'result':
                                    game['homeScores'] = {
                                        'final': competitor['score']
                                    }
                            else:
                                game['visitorTeam'] = {
                                    'extid': competitor['id'],
                                    'name': competitor['name']
                                }

                                if game['state'] == 'result':
                                    game['visitorScores'] = {
                                        'final': competitor['score']
                                    }

                        game['extid'] = event['id']
                        games.append(game)
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(get_info, daylist)

        return json.dumps(games, indent=4)
    else:
        return {'error': 'Something went wrong!'}

def func_nba_ncaa_g(args):
# Get schedule
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        args['season'] = str(int(args['season']) + 1)

        return get_schedule(args['lpar'])
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')

        if args['lpar'] == 'NBA':
            response = requests.get(f'https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary?region=us&lang=en&contentorigin=espn&event={args["extid"]}&showAirings=buy%2Clive%2Creplay&showZipLookup=true&buyWindow=1m')
        elif args['lpar'] == 'G':
            response = requests.get(f'https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba-development/summary?region=us&lang=en&contentorigin=espn&event={args["extid"]}&showAirings=buy%2Clive%2Creplay&showZipLookup=true&buyWindow=1m')
        elif args['lpar'] == 'NCAA':
            response = requests.get(f'https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?region=us&lang=en&contentorigin=espn&event={args["extid"]}&showAirings=buy%2Clive%2Creplay&showZipLookup=true&buyWindow=1m')

        if response.status_code == 200:
            data = response.json()
            info = {}
            info['extid'] = args["extid"]

            if args['lpar'] == 'NBA':
                info['source'] = f'https://www.espn.com/nba/boxscore/_/gameId/{info["extid"]}'
            elif args['lpar'] == 'G':
                info['source'] = f'https://www.espn.com/nba-g-league/boxscore/_/gameId/{info["extid"]}'
            elif args['lpar'] == 'NCAA':
                info['source'] = f'https://www.espn.com/mens-college-basketball/boxscore/_/gameId/{info["extid"]}'

            info['playDate'] = data['header']['competitions'][0]['date'].split('T')[0]
            info['type'] = 'Regular Season'
            info['stats'] = []

            boxscoreAvailable = data['header']['competitions'][0]['boxscoreAvailable']
            for competitor in data['header']['competitions'][0]['competitors']:
                if competitor['homeAway'] == 'home':
                    info['homeTeam'] = {
                        'extid': competitor['team']['id'],
                        'name': competitor['team']['displayName']
                    }

                    info['homeScores'] = {
                        'QT1': 0,
                        'QT2': 0,
                        'QT3': 0,
                        'QT4': 0,
                        'extra': 0,
                        'final': 0
                    }

                    if boxscoreAvailable:
                        info['homeScores']['QT1'] += int(competitor['linescores'][0]['displayValue'])
                        info['homeScores']['QT2'] += int(competitor['linescores'][1]['displayValue'])

                        if args['lpar'] == 'NBA' or args['lpar'] == 'G':
                            info['homeScores']['QT3'] += int(competitor['linescores'][2]['displayValue'])
                            info['homeScores']['QT4'] += int(competitor['linescores'][3]['displayValue'])

                        for score in competitor['linescores'][4:]:
                            info['homeScores']['extra'] += int(score['displayValue'])

                        info['homeScores']['final'] += int(competitor['score'])
                else:
                    info['visitorTeam'] = {
                        'extid': competitor['team']['id'],
                        'name': competitor['team']['displayName']
                    }

                    info['visitorScores'] = {
                        'QT1': 0,
                        'QT2': 0,
                        'QT3': 0,
                        'QT4': 0,
                        'extra': 0,
                        'final': 0
                    }

                    if boxscoreAvailable:
                        info['visitorScores']['QT1'] += int(competitor['linescores'][0]['displayValue'])
                        info['visitorScores']['QT2'] += int(competitor['linescores'][1]['displayValue'])

                        if args['lpar'] == 'NBA' or args['lpar'] == 'G':
                            info['visitorScores']['QT3'] += int(competitor['linescores'][2]['displayValue'])
                            info['visitorScores']['QT4'] += int(competitor['linescores'][3]['displayValue'])

                        for score in competitor['linescores'][4:]:
                            info['visitorScores']['extra'] += int(score['displayValue'])

                        info['visitorScores']['final'] += int(competitor['score'])
            
            if boxscoreAvailable:
                boxscore = data['boxscore']

                for player in boxscore['players']:
                    for athlete in player['statistics'][0]['athletes']:
                        if athlete['didNotPlay'] == False:
                            stat = {}
                            stat['player_extid'] = athlete['athlete']['id']
                            stat['player_firstname'] = athlete['athlete']['displayName'].split(' ')[0]
                            stat['player_lastname'] = athlete['athlete']['displayName'].split(' ')[1]
                            stat['player_name'] = athlete['athlete']['displayName']
                            stat['team'] = player['team']['id']

                            item = {
                                '2pts Attempts': athlete['stats'][1].split('-')[1],
                                '2pts Made': athlete['stats'][1].split('-')[0],
                                '3pts Attempts': athlete['stats'][2].split('-')[1],
                                '3pts Made': athlete['stats'][2].split('-')[0],
                                'Assists': athlete['stats'][7],
                                'Block Shots': athlete['stats'][9],
                                'Defensive rebounds': athlete['stats'][5],
                                'FT Attempts': athlete['stats'][3].split('-')[1],
                                'FT Made': athlete['stats'][3].split('-')[0],
                                'Minutes played': athlete['stats'][0],
                                'Offensive rebounds': athlete['stats'][4],
                                'Personal fouls': athlete['stats'][11],
                                'Steals': athlete['stats'][8],
                                'Total rebounds': athlete['stats'][6],
                                'Turnovers': athlete['stats'][10]
                            }

                            if args['lpar'] == 'NBA' or args['lpar'] == 'G':
                                item['Points'] = athlete['stats'][13]
                            elif args['lpar'] == 'NCAA':
                                item['Points'] = athlete['stats'][12]

                            try:
                                item['2pts Attempts'] = int(item['2pts Attempts']) - int(item['3pts Attempts'])
                                item['2pts Made'] = int(item['2pts Made']) - int(item['3pts Made'])
                            except ValueError:
                                pass

                            stat['items'] = item

                            info['stats'].append(stat)

                    # stat = {}
                    # stat['player_extid'] = 'team'
                    # stat['player_firstname'] = ''
                    # stat['player_lastname'] = '- TEAM -'
                    # stat['player_name'] = '- TEAM -'
                    # stat['team'] = player['team']['id']

                    # item = {
                    #     '2pts Attempts': player['statistics'][0]['totals'][1].split('-')[1],
                    #     '2pts Made': player['statistics'][0]['totals'][1].split('-')[0],
                    #     '3pts Attempts': player['statistics'][0]['totals'][2].split('-')[1],
                    #     '3pts Made': player['statistics'][0]['totals'][2].split('-')[0],
                    #     'Assists': player['statistics'][0]['totals'][7],
                    #     'Block Shots': player['statistics'][0]['totals'][9],
                    #     'Defensive rebounds': player['statistics'][0]['totals'][5],
                    #     'FT Attempts': player['statistics'][0]['totals'][3].split('-')[1],
                    #     'FT Made': player['statistics'][0]['totals'][3].split('-')[0],
                    #     'Offensive rebounds': player['statistics'][0]['totals'][4],
                    #     'Personal fouls': player['statistics'][0]['totals'][11],
                    #     'Steals': player['statistics'][0]['totals'][8],
                    #     'Total rebounds': player['statistics'][0]['totals'][6],
                    #     'Turnovers': player['statistics'][0]['totals'][10]
                    # }

                    # if args['lpar'] == 'NBA' or args['lpar'] == 'G':
                    #     item['Points'] = player['statistics'][0]['totals'][13]
                    # elif args['lpar'] == 'NCAA':
                    #     item['Points'] = player['statistics'][0]['totals'][12]

                    # try:
                    #     item['2pts Attempts'] = int(item['2pts Attempts']) - int(item['3pts Attempts'])
                    #     item['2pts Made'] = int(item['2pts Made']) - int(item['3pts Made'])
                    # except ValueError:
                    #     pass

                    # stat['items'] = item

                    # info['stats'].append(stat)

            return info
        else:
            return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        args['extid'] = request.args.get('extid')

        if args['lpar'] == 'NBA':
            response = requests.get(f'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{args["extid"]}?region=us&lang=en&contentorigin=espn')
        elif args['lpar'] == 'G':
            response = requests.get(f'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{args["extid"]}?region=us&lang=en&contentorigin=espn')
        elif args['lpar'] == 'NCAA':
            response = requests.get(f'https://site.web.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{args["extid"]}?region=us&lang=en&contentorigin=espn')

        if response.status_code == 200:
            data = response.json()
            info = {}

            try:
                info['team'] = data['athlete']['team']['name']
            except KeyError:
                info['team'] = ''

            try:
                info['dateOfBirth'] = datetime.strptime(data['athlete']['displayDOB'], '%m/%d/%Y').strftime('%Y-%m-%d')
            except KeyError:
                info['dateOfBirth'] = ''

            info['extid'] = args["extid"]

            try:
                info['firstname'] = data['athlete']['firstName']
            except KeyError:
                info['firstname'] = ''

            try:
                info['lastname'] = data['athlete']['lastName']
            except KeyError:
                info['lastname'] = ''

            try:
                info['name'] = data['athlete']['fullName']
            except KeyError:
                info['name'] = ''

            try:
                info['nationality'] = data['athlete']['citizenship']
            except KeyError:
                info['nationality'] = ''
            
            try:
                info['college'] = data['athlete']['college']['name']
            except KeyError:
                info['college'] = ''

            try:
                info['hand'] = data['athlete']['hand']['displayValue']
            except KeyError:
                pass
            
            try:
                info['debutYear'] = data['athlete']['debutYear']
            except KeyError:
                pass

            try:
                info['height'] = data['athlete']['displayHeight']
                feet = float(info['height'].split("'")[0])
                inches = float(info['height'].split("'")[1].split("\"")[0])
                info['height'] = int(feet * 30.48 + inches * 2.54)
            except KeyError:
                info['height'] = ''

            try:
                info['age'] = data['athlete']['age']
            except KeyError:
                pass

            try:
                info['birthPlace'] = data['athlete']['displayBirthPlace']
            except KeyError:
                info['birthPlace'] = ''

            try:
                info['draft'] = data['athlete']['displayDraft']
            except KeyError:
                pass

            try:
                info['experience'] = data['athlete']['displayExperience']
            except KeyError:
                pass

            try:
                info['jersey'] = data['athlete']['jersey']
            except KeyError:
                pass

            try:
                info['weight'] = data['athlete']['displayWeight']
                info['weight'] = float(info['weight'].replace('lbs', '').strip())
                info['weight'] = int(info['weight'] * 0.45359237)
            except KeyError:
                pass

            try:
                info['position'] = data['athlete']['position']['name']
            except KeyError:
                info['position'] = ''

            try:
                info['active'] = data['athlete']['active']
            except KeyError:
                pass
            
            if args['lpar'] == 'NBA':
                info['source'] = f'https://www.espn.com/nba/player/_/id/{info["extid"]}/{info["firstname"].lower()}-{info["lastname"].lower()}'
            elif args['lpar'] == 'G':
                info['source'] = ''
            elif args['lpar'] == 'NCAA':
                info['source'] = f'https://www.espn.com/mens-college-basketball/player/_/id/{info["extid"]}/{info["firstname"].lower()}-{info["lastname"].lower()}'

            return info
        else:
            return {'error': 'Something went wrong!'}