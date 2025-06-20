from library import *

def func_kzs(args):
    if args['f'] == 'schedule':
        args['season'] = int(request.args.get('season')[-2:]) + 1
        games = []
        respCount = requests.get(f'https://api.sistem.kzs.si/api/v1/public/matches/?requestType=COUNT&seasonId={args["season"]}&competitionIds={args["spar"]}')
        matchCount = respCount.json()['data']['count']
        pageCount = ceil(matchCount / 20)

        for pageIndex in range(pageCount):
            urlPage = f'https://api.sistem.kzs.si/api/v1/public/matches/?requestType=FETCH&limit=20&offset={pageIndex * 20}&seasonId={args["season"]}&competitionIds={args["spar"]}'
            respPage = requests.get(urlPage)
            items = respPage.json()['data']['items']

            for item in items:
                game = {}
                game['competition'] = item['competitions'][0]['competitionName']
                game['playDate'] = item['dateTime'].split('T')[0]
                game['round'] = item['round']

                if item['status'] == 'SCHEDULED':
                    game['state'] = 'confirmed'
                else:
                    game['state'] = 'result'

                game['type'] = 'Regular Season'
                game['extid'] = item['id']
                game['source'] = f'https://www.kzs.si/tekma/{game["extid"]}?tab=statistika'

                game['homeTeam'] = {
                    'extid': item['firstTeamTeamId'],
                    'name': item['firstTeamName']
                }

                game['visitorTeam'] = {
                    'extid': item['secondTeamTeamId'],
                    'name': item['secondTeamName']
                }

                if item['status'] == 'result':
                    game['homeScores'] = {
                        'final': item['firstTeamScore']
                    }
                    game['visitorScores'] = {
                        'final': item['secondTeamScore']
                    }

                games.append(game)
            
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')
        urlMatch = f'https://api.sistem.kzs.si/api/v1/public/matches/{args["extid"]}'
        respMatch = requests.get(urlMatch)
        dataMatch = respMatch.json()['data']

        info = {}
        info['extid'] = args['extid']
        info['playDate'] = dataMatch['dateTime'].split('T')[0]
        info['source'] = f'https://www.kzs.si/tekma/{info["extid"]}?tab=statistika'
        info['type'] = 'Regular Season'
        info['stats'] = []

        info['homeTeam'] = {
            'extid': dataMatch['firstTeam']['teamId'],
            'name': dataMatch['firstTeam']['name']
        }
        info['homeScores'] = {
            'final': dataMatch['firstTeamScore']
        }
        
        urlStats = f'https://api.sistem.kzs.si/api/v1/public/matches/{args["extid"]}/stats'
        respStats = requests.get(urlStats)
        dataStats = respStats.json()['data']
        players = dataStats['firstTeam']['playerStats']

        for player in players:
            stat = {}
            stat['team'] = info['homeTeam']['extid']
            stat['player_extid'] = player['playerId']
            stat['player_firstname'] = player['matchTeamPlayerFirstname']
            stat['player_lastname'] = player['matchTeamPlayerLastname']
            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"

            item = {}
            item['3pts Attempts'] = player['threePA']
            item['3pts Made'] = player['threePM']
            item['2pts Attempts'] = player['twoPA']
            item['2pts Made'] = player['twoPM']
            item['Assists'] = player['assists']
            item['Block Shots'] = player['blocksInFavor']
            item['Defensive rebounds'] = player['defensiveRebounds']
            item['FT Attempts'] = player['fTA']
            item['FT Made'] = player['fTM']
            item['Minutes played'] = round(player['minutes'])
            item['Offensive rebounds'] = player['offensiveRebounds']
            item['Personal fouls'] = player['foulCommited']
            item['Points'] = item['FT Made'] + item['2pts Made'] * 2 + item['3pts Made'] * 3
            item['Steals'] = player['steals']
            item['Total rebounds'] = item['Defensive rebounds'] + item['Offensive rebounds']
            item['Turnovers'] = player['turnovers']

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['homeTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        item = {}
        item['Total rebounds'] = dataStats['firstTeam']['teamStats']['reboundsTeam']
        item['Defensive rebounds'] = dataStats['firstTeam']['teamStats']['reboundsTeamDefensive']
        item['Offensive rebounds'] = dataStats['firstTeam']['teamStats']['reboundsTeamOffensive']
        item['Steals'] = dataStats['firstTeam']['teamStats']['steals']
        item['Turnovers'] = dataStats['firstTeam']['teamStats']['turnovers']

        stat['items'] = item
        info['stats'].append(stat)

        info['visitorTeam'] = {
            'extid': dataMatch['secondTeam']['teamId'],
            'name': dataMatch['secondTeam']['name']
        }
        info['visitorScores'] = {
            'final': dataMatch['secondTeamScore']
        }

        players = dataStats['secondTeam']['playerStats']

        for player in players:
            stat = {}
            stat['team'] = info['visitorTeam']['extid']
            stat['player_extid'] = player['playerId']
            stat['player_firstname'] = player['matchTeamPlayerFirstname']
            stat['player_lastname'] = player['matchTeamPlayerLastname']
            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"

            item = {}
            item['3pts Attempts'] = player['threePA']
            item['3pts Made'] = player['threePM']
            item['2pts Attempts'] = player['twoPA']
            item['2pts Made'] = player['twoPM']
            item['Assists'] = player['assists']
            item['Block Shots'] = player['blocksInFavor']
            item['Defensive rebounds'] = player['defensiveRebounds']
            item['FT Attempts'] = player['fTA']
            item['FT Made'] = player['fTM']
            item['Minutes played'] = round(player['minutes'])
            item['Offensive rebounds'] = player['offensiveRebounds']
            item['Personal fouls'] = player['foulCommited']
            item['Points'] = item['FT Made'] + item['2pts Made'] * 2 + item['3pts Made'] * 3
            item['Steals'] = player['steals']
            item['Total rebounds'] = item['Defensive rebounds'] + item['Offensive rebounds']
            item['Turnovers'] = player['turnovers']

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['visitorTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        item = {}
        item['Total rebounds'] = dataStats['secondTeam']['teamStats']['reboundsTeam']
        item['Defensive rebounds'] = dataStats['secondTeam']['teamStats']['reboundsTeamDefensive']
        item['Offensive rebounds'] = dataStats['secondTeam']['teamStats']['reboundsTeamOffensive']
        item['Steals'] = dataStats['secondTeam']['teamStats']['steals']
        item['Turnovers'] = dataStats['secondTeam']['teamStats']['turnovers']

        stat['items'] = item
        info['stats'].append(stat)

        info['homeScores']['QT1'] = dataMatch['scores'][0]['firstTeamScore']
        info['homeScores']['QT2'] = dataMatch['scores'][1]['firstTeamScore']
        info['homeScores']['QT3'] = dataMatch['scores'][2]['firstTeamScore']
        info['homeScores']['QT4'] = dataMatch['scores'][3]['firstTeamScore']
        info['homeScores']['extra'] = 0

        info['visitorScores']['QT1'] = dataMatch['scores'][0]['secondTeamScore']
        info['visitorScores']['QT2'] = dataMatch['scores'][1]['secondTeamScore']
        info['visitorScores']['QT3'] = dataMatch['scores'][2]['secondTeamScore']
        info['visitorScores']['QT4'] = dataMatch['scores'][3]['secondTeamScore']
        info['visitorScores']['extra'] = 0

        for score in dataMatch['scores'][4:]:
            info['homeScores']['extra'] += score['firstTeamScore']
            info['visitorScores']['extra'] += score['secondTeamScore']

        return info
    elif args['f'] == 'player':
        args['extid'] = request.args.get('extid')
        playerUrl = f'https://api.sistem.kzs.si/api/v1/public/players/{args["extid"]}'
        respPlayer = requests.get(playerUrl)
        dataPlayer = respPlayer.json()['data']

        info = {}
        info['extid'] = args['extid']
        info['source'] = f'https://www.kzs.si/igralec/{args["extid"]}'
        info['firstname'] = dataPlayer['person']['firstName']
        info['lastname'] = dataPlayer['person']['lastName']
        info['name'] = f"{info['firstname']} {info['lastname']}"

        try:
            info['dateOfBirth'] = dataPlayer['person']['yearOfBirth']
        except:
            info['dateOfBirth'] = dataPlayer['person']['dateOfBirth']


        info['age'] = datetime.now().year - int(str(info['dateOfBirth']).split('-')[0])
        info['nationality'] = dataPlayer['nationality']['engName']

        try:
            info['height'] = dataPlayer['person']['height']
        except:
            pass

        return info