from library import *

def func_euroleague_eurocup(args):
    # Get schedule
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')

        response = requests.get(f'https://feeds.incrowdsports.com/provider/euroleague-feeds/v2/competitions/{args["lpar"]}/seasons/{args["lpar"]}{args["season"]}/rounds')

        if response.status_code == 200:
            # Get rounds
            data = response.json()['data']
            rounds = []

            for item in data:
                round = {
                    'seasonCode': item['seasonCode'],
                    'round': item['round'],
                    'phaseTypeCode': item['phaseTypeCode'],
                    'seasonCode': item['seasonCode']
                }

                rounds.append(round)

            # Get games per each round
            games = []
            for round in rounds:
                phaseTypeCode = round['phaseTypeCode']
                roundNumber = round['round']
                seasonCode = round['seasonCode']
                response = requests.get(f'https://feeds.incrowdsports.com/provider/euroleague-feeds/v2/competitions/{args["lpar"]}/seasons/{seasonCode}/games?teamCode=&phaseTypeCode={phaseTypeCode}&roundNumber={roundNumber}')

                if response.status_code == 200:
                    data = response.json()['data']

                    for item in data:
                        game = {
                            'competition': item['competition']['name'],
                            'playDate': item['date'].split('T')[0],
                            'round': item['round']['round'],
                            'state': item['status'],
                            'type': item['phaseType']['name'],
                            'homeTeam': {
                                'extid': item['home']['code'],
                                'name': item['home']['name']
                            },
                            'visitorTeam': {
                                'extid': item['away']['code'],
                                'name': item['away']['name']
                            }
                        }

                        code = str(item['code'])
                        season_alias = str(item['season']['alias'])
                        season_code = str(item['season']['code'])
                        game_id = f"{game['homeTeam']['name']} {game['visitorTeam']['name']}".lower().replace(' ', '-').strip()
                        game['extid'] = '_'.join([season_alias, game_id, season_code, code])

                        if args['lpar'] == 'E':
                            game['source'] = f'https://www.euroleaguebasketball.net/en/euroleague/game-center/{season_alias}/{game_id}/{season_code}/{code}/'
                        
                        if args['lpar'] == 'U':
                            game['source'] = f'https://www.euroleaguebasketball.net/en/eurocup/game-center/{season_alias}/{game_id}/{season_code}/{code}/'

                        if game['state'] == 'result':
                            game['homeScores'] = {
                                'final': item['home']['score']
                            }
                            game['visitorScores'] = {
                                'final': item['away']['score']
                            }

                        games.append(game)

            return json.dumps(games, indent=4)
        else:
            return {'error': 'Something went wrong!'}
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')
        season_alias, game_id, season_code, code = args['extid'].split('_')

        if args["lpar"] == 'E':
            session = requests.Session()
            response = session.get('https://www.euroleaguebasketball.net/en/euroleague/game-center/')
            token = re.search('<script src="/_next/static/([\w-]{21})/_buildManifest\.js" defer=""></script>', response.text).group(1)
            response = session.get(f'https://www.euroleaguebasketball.net/_next/data/{token}/en/euroleague/game-center/{season_alias}/{game_id}/{season_code}/{code}.json')
        
        if args["lpar"] == 'U':
            session = requests.Session()
            response = session.get('https://www.euroleaguebasketball.net/en/eurocup/game-center/')
            token = re.search('<script src="/_next/static/([\w-]{21})/_buildManifest\.js" defer=""></script>', response.text).group(1)
            response = session.get(f'https://www.euroleaguebasketball.net/_next/data/{token}/en/eurocup/game-center/{season_alias}/{game_id}/{season_code}/{code}.json')
            
        if response.status_code == 200:
            data = response.json()['pageProps']['mappedData']

            info = {}
            info['extid'] = args['extid']
            info['playDate'] = data['rawGameInfo']['date'].split('T')[0]
            
            if args['lpar'] == 'E':
                info['source'] = f'https://www.euroleaguebasketball.net/en/euroleague/game-center/{season_alias}/{game_id}/{season_code}/{code}/#boxscore'

            if args['lpar'] == 'U':
                info['source'] = f'https://www.euroleaguebasketball.net/en/eurocup/game-center/{season_alias}/{game_id}/{season_code}/{code}/#boxscore'

            info['type'] = data['rawGameInfo']['phaseType']['name']
            info['homeTeam'] = {
                'extid': data['rawGameInfo']['home']['code'],
                'name': data['rawGameInfo']['home']['name']
            }
            info['homeScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': data['rawGameInfo']['home']['score']
            }
            info['visitorTeam'] = {
                'extid': data['rawGameInfo']['away']['code'],
                'name': data['rawGameInfo']['away']['name']
            }
            info['visitorScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': data['rawGameInfo']['away']['score']
            }

            info['stats'] = []

            if data['status'] == "result":
                info['homeScores']['QT1'] = data['boxScores']['byQuarterInfo']['homeTeam']['q1']
                info['homeScores']['QT2'] = data['boxScores']['byQuarterInfo']['homeTeam']['q2']
                info['homeScores']['QT3'] = data['boxScores']['byQuarterInfo']['homeTeam']['q3']
                info['homeScores']['QT4'] = data['boxScores']['byQuarterInfo']['homeTeam']['q4']

                info['visitorScores']['QT1'] = data['boxScores']['byQuarterInfo']['awayteam']['q1']
                info['visitorScores']['QT2'] = data['boxScores']['byQuarterInfo']['awayteam']['q2']
                info['visitorScores']['QT3'] = data['boxScores']['byQuarterInfo']['awayteam']['q3']
                info['visitorScores']['QT4'] = data['boxScores']['byQuarterInfo']['awayteam']['q4']

                info['homeScores']['extra'] += data['boxScores']['byQuarterInfo']['homeTeam']['ot1']
                info['homeScores']['extra'] += data['boxScores']['byQuarterInfo']['homeTeam']['ot2']
                info['homeScores']['extra'] += data['boxScores']['byQuarterInfo']['homeTeam']['ot3']
                info['homeScores']['extra'] += data['boxScores']['byQuarterInfo']['homeTeam']['ot4']
                info['homeScores']['extra'] += data['boxScores']['byQuarterInfo']['homeTeam']['ot5']

                info['visitorScores']['extra'] += data['boxScores']['byQuarterInfo']['awayteam']['ot1']
                info['visitorScores']['extra'] += data['boxScores']['byQuarterInfo']['awayteam']['ot2']
                info['visitorScores']['extra'] += data['boxScores']['byQuarterInfo']['awayteam']['ot3']
                info['visitorScores']['extra'] += data['boxScores']['byQuarterInfo']['awayteam']['ot4']
                info['visitorScores']['extra'] += data['boxScores']['byQuarterInfo']['awayteam']['ot5']

                statsTable = data['boxScores']['statsTable']

                for table in statsTable:
                    if table['archValues']['teamName'] == info['homeTeam']['name']:
                        team = info['homeTeam']['extid']
                    if table['archValues']['teamName'] == info['visitorTeam']['name']:
                        team = info['visitorTeam']['extid']

                    groups = table['groups']

                    for group in groups:
                        if group['groupName'] == "Total" or group['groupName'] == "Head coach:":
                            continue

                        if group['groupName'] == "Team":
                            stat = {
                                'team': team,
                                'player_name': '- TEAM -',
                            }
                            stat['player_firstname'] = ''
                            stat['player_lastname'] = '- TEAM -'

                            stat['player_extid'] = 'team '
                        else:
                            stat = {
                                'team': team
                            }
                            stat['player_firstname'] = group['groupValues']['name'].split(',')[1].strip()
                            stat['player_lastname'] = group['groupValues']['name'].split(',')[0].strip()
                            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"

                            player_code = str(group['groupValues']['code'])
                            player_id = f"{stat['player_firstname']}-{stat['player_lastname']}".lower().strip()
                            stat['player_extid'] = '_'.join([player_id, player_code])

                        item = {}

                        for column in group['stats']:
                            name = column['name']

                            for value in column['value']:
                                statsHeading = value['statsHeading']
                                if group['groupName'] != "Team":
                                    if name == "":
                                        if statsHeading == "Min":
                                            minutes = int(value['stat'].split(':')[0])
                                            seconds = int(value['stat'].split(':')[1])
                                            if seconds >= 30:
                                                minutes += 1
                                            item['Minutes played'] = minutes
                                        if statsHeading == "PTS":
                                            item['Points'] = value['stat']
                                    if name == "2FG":
                                        if statsHeading == "M/A":
                                            item['2pts Made'] = value['stat'].split('/')[0]
                                            item['2pts Attempts'] = value['stat'].split('/')[1]
                                    if name == "3FG":
                                        if statsHeading == "M/A":
                                            item['3pts Made'] = value['stat'].split('/')[0]
                                            item['3pts Attempts'] = value['stat'].split('/')[1]
                                    if name == "FT":
                                        if statsHeading == "M/A":
                                            item['FT Made'] = value['stat'].split('/')[0]
                                            item['FT Attempts'] = value['stat'].split('/')[1]
                                if name == "Rebounds":
                                    if statsHeading == "O":
                                        item['Offensive rebounds'] = value['stat']
                                    if statsHeading == "D":
                                        item['Defensive rebounds'] = value['stat']
                                    if statsHeading == "T":
                                        item['Total rebounds'] = value['stat']
                                if name == "General":
                                    if statsHeading == "AST":
                                        item['Assists'] = value['stat']
                                    if statsHeading == "STL":
                                        item['Steals'] = value['stat']
                                    if statsHeading == "TO":
                                        item['Turnovers'] = value['stat']
                                if name == "Blocks":
                                    if statsHeading == "F":
                                        item['Block Shots'] = value['stat']
                                if name == "Fouls":
                                    if statsHeading == "C":
                                        item['Personal fouls'] = value['stat']
                        stat['items'] = item
                        info['stats'].append(stat)
            return info
        else:
            return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        args['extid'] = request.args.get('extid')
        player_id, player_code = args['extid'].split('_')

        if args["lpar"] == 'E':
            session = requests.Session()
            response = session.get('https://www.euroleaguebasketball.net/en/euroleague/game-center/')
            token = re.search('<script src="/_next/static/([\w-]{21})/_buildManifest\.js" defer=""></script>', response.text).group(1)
            response = session.get(f'https://www.euroleaguebasketball.net/_next/data/{token}/en/euroleague/players/{player_id}/{player_code}.json')

        if args["lpar"] == 'U':
            session = requests.Session()
            response = session.get('https://www.euroleaguebasketball.net/en/eurocup/game-center/')
            token = re.search('<script src="/_next/static/([\w-]{21})/_buildManifest\.js" defer=""></script>', response.text).group(1)
            response = session.get(f'https://www.euroleaguebasketball.net/_next/data/{token}/en/eurocup/players/{player_id}/{player_code}.json')

        if response.status_code == 200:
            data = response.json()['pageProps']['data']['hero']

            info = {}
            info['extid'] = args['extid']
            info['dateOfBirth'] = data['born'].split('T')[0]
            info['firstname'] = data['firstName']
            info['lastname'] = data['lastName']
            info['height'] = data['height']
            info['name'] = f"{info['firstname']} {info['lastname']}"
            info['nationality'] = data['nationality']
            info['club'] = data['clubName']
            info['position'] = data['position']

            if args['lpar'] == 'E':
                info['source'] = f'https://www.euroleaguebasketball.net/en/euroleague/players/{player_id}/{player_code}/'

            if args['lpar'] == 'U':
                info['source'] = f'https://www.euroleaguebasketball.net/en/eurocup/players/{player_id}/{player_code}/'

            info['facebook'] = data['facebook']
            info['instagram'] = data['instagram']
            info['shirtNumber'] = data['shirtNumber']
            info['twitter'] = data['twitter']

            return info
        else:
            return {'error': 'Something went wrong!'}
    else:
        return {'error': 'Something went wrong!'}