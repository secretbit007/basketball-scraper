from library import *

def func_vtb(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        args['season'] = int(args['season']) + 1

        response = requests.get('https://org.infobasket.su/Comp/GetSeasonsForTag?tag=vtb')

        if response.status_code == 200:
            seasons = response.json()

            for season in seasons:
                if season['SeasonYear'] == args['season']:
                    season_id = season['CompID']
                    break

            response = requests.get(f'https://org.infobasket.su/Comp/GetCalendar/?comps={season_id}&format=json')

            if response.status_code == 200:
                items = response.json()
                games = []
                for item in items:
                    game = {}
                    game['competition'] = item['LeagueNameEn']
                    game['playDate'] = datetime.strptime(item['GameDate'], '%d.%m.%Y').strftime('%Y-%m-%d')
                    game['round'] = item['CompNameEn']
                    game['state'] = "result" if item['GameStatus'] else "confirmed"

                    game['homeTeam'] = {
                        'extid': item['TeamAid'],
                        'name': item['ShortTeamNameAen']
                    }

                    game['visitorTeam'] = {
                        'extid': item['TeamBid'],
                        'name': item['ShortTeamNameBen']
                    }
                    
                    if item['GameStatus']:
                        game['extid'] = item['GameID']
                        game['source'] = f'https://vtb-league.com/en/game/{item["GameID"]}'
                        game['homeScores'] = {
                            'final': item['ScoreA']
                        }
                        game['visitorScores'] = {
                            'final': item['ScoreB']
                        }
                    else:
                        game['extid'] = ''
                        game['source'] = ''

                    game['type'] = 'Regular Season'
                    games.append(game)
                
                return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')

        response = requests.get(f'https://org.infobasket.su/Widget/GetOnline/{args["extid"]}?format=json&lang=en')

        if response.status_code == 200:
            data = response.json()

            info = {}
            info['extid'] = args['extid']
            info['playDate'] = datetime.strptime(data['GameDate'], '%d.%m.%Y').strftime('%Y-%m-%d')
            info['source'] = f'https://vtb-league.com/en/game/{args["extid"]}'
            info['type'] = 'Regular Season'
            info['stats'] = []

            teams = data['GameTeams']  

            for team in teams:
                if team['TeamNumber'] == 1:
                    info['homeTeam'] = {
                        'extid': team['TeamID'],
                        'name': team['TeamName']['CompTeamNameEn']
                    }
                    info['homeScores'] = {
                        'final': team['Score']
                    }

                    players = team['Players']

                    for player in players:
                        stat = {}
                        stat['team'] = info['homeTeam']['extid']
                        stat['player_extid'] = f"{player['PersonID']}_{player['CountryNameEn']}"
                        stat['player_name'] = player['PersonNameEn']
                        stat['player_firstname'] = player['FirstNameEn']
                        stat['player_lastname'] = player['LastNameEn']

                        item = {}
                        item['3pts Attempts'] = player['Shot3'] if player['Shot3'] else 0
                        item['3pts Made'] = player['Goal3'] if player['Goal3'] else 0
                        item['2pts Attempts'] = player['Shot2'] if player['Shot2'] else 0
                        item['2pts Made'] = player['Goal2'] if player['Goal2'] else 0
                        item['Assists'] = player['Assist'] if player['Assist'] else 0
                        item['Block Shots'] = player['Blocks'] if player['Blocks'] else 0
                        item['Defensive rebounds'] = player['DefRebound'] if player['DefRebound'] else 0
                        item['FT Attempts'] = player['Shot1'] if player['Shot1'] else 0
                        item['FT Made'] = player['Goal1'] if player['Goal1'] else 0
                        item['Minutes played'] = round((datetime.strptime(player['PlayedTime'], '%M:%S').minute * 60 + datetime.strptime(player['PlayedTime'], '%M:%S').second) / 60)
                        item['Offensive rebounds'] = player['OffRebound'] if player['OffRebound'] else 0
                        item['Personal fouls'] = player['Foul'] if player['Foul'] else 0
                        item['Points'] = player['Points'] if player['Points'] else 0
                        item['Steals'] = player['Steal'] if player['Steal'] else 0
                        item['Total rebounds'] = player['Rebound'] if player['Rebound'] else 0
                        item['Turnovers'] = player['Turnover'] if player['Turnover'] else 0

                        stat['items'] = item
                        info['stats'].append(stat)

                    stat = {}
                    stat['team'] = info['homeTeam']['extid']
                    stat['player_extid'] = 'team'
                    stat['player_firstname'] = ''
                    stat['player_lastname'] = '- TEAM -'
                    stat['player_name'] = '- TEAM -'

                    item = {}
                    item['Total rebounds'] = team['TeamRebound'] if team['TeamRebound'] else 0
                    item['Defensive rebounds'] = team['TeamDefRebound'] if team['TeamDefRebound'] else 0
                    item['Offensive rebounds'] = team['TeamOffRebound'] if team['TeamOffRebound'] else 0
                    item['Steals'] = team['TeamSteal'] if team['TeamSteal'] else 0
                    item['Turnovers'] = team['TeamTurnover'] if team['TeamTurnover'] else 0

                    stat['items'] = item
                    info['stats'].append(stat)

                if team['TeamNumber'] == 2:
                    info['visitorTeam'] = {
                        'extid': team['TeamID'],
                        'name': team['TeamName']['CompTeamNameEn']
                    }
                    info['visitorScores'] = {
                        'final': team['Score']
                    }

                    players = team['Players']

                    for player in players:
                        stat = {}
                        stat['team'] = info['visitorTeam']['extid']
                        stat['player_extid'] = f"{player['PersonID']}_{player['CountryNameEn']}"
                        stat['player_name'] = player['PersonNameEn']
                        stat['player_firstname'] = player['FirstNameEn']
                        stat['player_lastname'] = player['LastNameEn']

                        item = {}
                        item['3pts Attempts'] = player['Shot3'] if player['Shot3'] else 0
                        item['3pts Made'] = player['Goal3'] if player['Goal3'] else 0
                        item['2pts Attempts'] = player['Shot2'] if player['Shot2'] else 0
                        item['2pts Made'] = player['Goal2'] if player['Goal2'] else 0
                        item['Assists'] = player['Assist'] if player['Assist'] else 0
                        item['Block Shots'] = player['Blocks'] if player['Blocks'] else 0
                        item['Defensive rebounds'] = player['DefRebound'] if player['DefRebound'] else 0
                        item['FT Attempts'] = player['Shot1'] if player['Shot1'] else 0
                        item['FT Made'] = player['Goal1'] if player['Goal1'] else 0
                        item['Minutes played'] = round((datetime.strptime(player['PlayedTime'], '%M:%S').minute * 60 + datetime.strptime(player['PlayedTime'], '%M:%S').second) / 60)
                        item['Offensive rebounds'] = player['OffRebound'] if player['OffRebound'] else 0
                        item['Personal fouls'] = player['Foul'] if player['Foul'] else 0
                        item['Points'] = player['Points'] if player['Points'] else 0
                        item['Steals'] = player['Steal'] if player['Steal'] else 0
                        item['Total rebounds'] = player['Rebound'] if player['Rebound'] else 0
                        item['Turnovers'] = player['Turnover'] if player['Turnover'] else 0

                        stat['items'] = item
                        info['stats'].append(stat)
                    
                    stat = {}
                    stat['team'] = info['visitorTeam']['extid']
                    stat['player_extid'] = 'team'
                    stat['player_firstname'] = ''
                    stat['player_lastname'] = '- TEAM -'
                    stat['player_name'] = '- TEAM -'

                    item = {}
                    item['Total rebounds'] = team['TeamRebound'] if team['TeamRebound'] else 0
                    item['Defensive rebounds'] = team['TeamDefRebound'] if team['TeamDefRebound'] else 0
                    item['Offensive rebounds'] = team['TeamOffRebound'] if team['TeamOffRebound'] else 0
                    item['Steals'] = team['TeamSteal'] if team['TeamSteal'] else 0
                    item['Turnovers'] = team['TeamTurnover'] if team['TeamTurnover'] else 0

                    stat['items'] = item
                    info['stats'].append(stat)

            info['homeScores']['QT1'] = 0
            info['homeScores']['QT2'] = 0
            info['homeScores']['QT3'] = 0
            info['homeScores']['QT4'] = 0
            info['homeScores']['extra'] = 0

            info['visitorScores']['QT1'] = 0
            info['visitorScores']['QT2'] = 0
            info['visitorScores']['QT3'] = 0
            info['visitorScores']['QT4'] = 0
            info['visitorScores']['extra'] = 0
            
            response = requests.get(f'https://org.infobasket.su/Widget/GetOnline/{args["extid"]}?format=json&lang=en')

            if response.status_code == 200:
                data = response.json()

                onlinePlays = data['OnlinePlays']
                onlineStarts = data['OnlineStarts']
                
                for onlinePlay in onlinePlays:
                    playTypeID = onlinePlay['PlayTypeID']
                    playPeriod = onlinePlay['PlayPeriod']
                    
                    if playTypeID == 1 or playTypeID == 2 or playTypeID == 3:
                        startID = onlinePlay['StartID']
                        
                        for onlineStart in onlineStarts:
                            if startID == onlineStart['StartID']:
                                teamNumber = onlineStart['TeamNumber']
                                
                                if teamNumber == 1:
                                    if playPeriod > 4:
                                        info['homeScores']['extra'] += playTypeID
                                    else:
                                        info['homeScores'][f'QT{playPeriod}'] += playTypeID
                                    
                                if teamNumber == 2:
                                    if playPeriod > 4:
                                        info['visitorScores']['extra'] += playTypeID
                                    else:
                                        info['visitorScores'][f'QT{playPeriod}'] += playTypeID
                                    
            return info
    elif args['f'] == 'player':
        extid, country = request.args.get('extid').split('_')

        response = requests.get(f'https://org.infobasket.su/Widget/PlayerPage/{extid}?format=json&tag=vtb')

        if response.status_code == 200:
            player = response.json()
            info = {}
            info['extid'] = args['extid']
            info['source'] = f'https://vtb-league.com/app/themes/mbt/rb/en/player.html?personId={extid}'
            info['name'] = player['PersonFullNameEn']
            info['firstname'] = player['PersonFirstNameEn']
            info['lastname'] = player['PersonLastNameEn']
            info['age'] = player['Age']
            info['nationality'] = country
            info['dateOfBirth'] = datetime.strptime(player['PersonBirth'], '%d.%m.%Y').strftime('%Y-%m-%d')
            info['height'] = player['PersonHeight']
            info['weight'] = player['PersonWeight']

            return info
