from library import *

def get_token():
    url = 'https://www.easycredit-bbl.de'
    resp = requests.get(url)

    if resp.status_code == 200:
        html = resp.text
        
        token = re.search(r'/_next/static/([\w\d]{21})/_buildManifest.js', html).group(1)
        
        return token

def get_schedule():
    games = []

    headers = {
        'x-api-key': 'publicWebUser',
        'x-api-secret': '04d7c56c6ce6a91055bdd1bd0861a85650cb815ec7965c8411c71a4c4b32e862'
    }
    
    url_finished = 'https://api.basketball-bundesliga.de/games?currentPage=1&pageSize=9&gameType=finished'
    resp_finished = requests.get(url_finished, headers=headers)
    total_page_finished = resp_finished.json()['totalPages']
    
    for page_finished in range(1, total_page_finished + 1):
        url_page_finished = f'https://api.basketball-bundesliga.de/games?currentPage={page_finished}&pageSize=9&gameType=finished'
        resp_page_finished = requests.get(url_page_finished, headers=headers)
        
        for match in resp_page_finished.json()['items']:
            game = {}
            
            if match['competition'] != 'BBL':
                continue
            
            game['competition'] = match['competition']
            game['playDate'] = match['scheduledTime'].split('T')[0]
            game['round'] = match['stage']
            game['state'] = 'Finished'
            game['type'] = 'Regular'
            
            game['homeTeam'] = {
                'extid': match['homeTeam']['teamId'],
                'name': match['homeTeam']['name']
            }
            game['homeScores'] = {
                'final': match['result']['homeTeamFinalScore']
            }
            
            game['visitorTeam'] = {
                'extid': match['guestTeam']['teamId'],
                'name': match['guestTeam']['name']
            }
            game['visitorScores'] = {
                'final': match['result']['guestTeamFinalScore']
            }

            game['extid'] = match['id']
            game['source'] = f'https://www.easycredit-bbl.de/spiele/{match["id"]}'
            games.append(game)
    
    url_scheduled = 'https://api.basketball-bundesliga.de/games?currentPage=1&pageSize=9&gameType=scheduled'
    resp_scheduled = requests.get(url_scheduled, headers=headers)
    total_page_scheduled = resp_scheduled.json()['totalPages']
    
    for page_scheduled in range(1, total_page_scheduled + 1):
        url_page_scheduled = f'https://api.basketball-bundesliga.de/games?currentPage={page_scheduled}&pageSize=9&gameType=scheduled'
        resp_page_scheduled = requests.get(url_page_scheduled, headers=headers)
        
        for match in resp_page_scheduled.json()['items']:
            game = {}
            
            if match['competition'] != 'BBL':
                continue
            
            game['competition'] = match['competition']
            game['playDate'] = match['scheduledTime'].split('T')[0]
            game['round'] = match['stage']
            game['state'] = 'Scheduled'
            game['type'] = 'Regular'
            
            game['homeTeam'] = {
                'extid': match['homeTeam']['teamId'],
                'name': match['homeTeam']['name']
            }
            game['homeScores'] = {
                'final': 0
            }
            
            game['visitorTeam'] = {
                'extid': match['guestTeam']['teamId'],
                'name': match['guestTeam']['name']
            }
            game['visitorScores'] = {
                'final': 0
            }

            game['extid'] = match['id']
            game['source'] = f'https://www.easycredit-bbl.de/spiele/{match["id"]}'
            games.append(game)
            
    return games

def get_boxscore(extid):
    token = get_token()
    
    if not token:
        return
    
    url = f'https://www.easycredit-bbl.de/_next/data/{token}/de-DE/spiele/{extid}.json?id={extid}'
    resp = requests.get(url)
    data = resp.json()['pageProps']['initialGameData']
    
    info = {}
    info['extid'] = extid
    info['playDate'] = data['scheduledTime'].split('T')[0]
        
    info['source'] = f'https://www.easycredit-bbl.de/spiele/{extid}#boxscore'
    info['type'] = 'Regular'
    
    info['homeTeam'] = {
        'extid': data['homeTeam']['teamId'],
        'name': data['homeTeam']['name']
    }
    
    info['visitorTeam'] = {
        'extid': data['guestTeam']['teamId'],
        'name': data['guestTeam']['name']
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
    
    if data['result']:
        info['homeScores']['final'] = data['result']['homeTeamFinalScore']

        info['homeScores']['QT1'] = data['result']['homeTeamQ1Score']
        info['homeScores']['QT2'] = data['result']['homeTeamQ2Score']
        info['homeScores']['QT3'] = data['result']['homeTeamQ3Score']
        info['homeScores']['QT4'] = data['result']['homeTeamQ4Score']
        info['homeScores']['extra'] = info['homeScores']['final'] - (info['homeScores']['QT1'] + info['homeScores']['QT2'] + info['homeScores']['QT3'] + info['homeScores']['QT4'])
            
        info['visitorScores']['final'] = data['result']['guestTeamFinalScore']
        info['visitorScores']['QT1'] = data['result']['guestTeamQ1Score']
        info['visitorScores']['QT2'] = data['result']['guestTeamQ2Score']
        info['visitorScores']['QT3'] = data['result']['guestTeamQ3Score']
        info['visitorScores']['QT4'] = data['result']['guestTeamQ4Score']
        info['visitorScores']['extra'] = info['visitorScores']['final'] - (info['visitorScores']['QT1'] + info['visitorScores']['QT2'] + info['visitorScores']['QT3'] + info['visitorScores']['QT4'])

        stats = resp.json()['pageProps']['initialGameStats']
        
        # home
        players = stats['homeTeam']['playerStats']

        for player in players:
            stat = {}
            stat['team'] = player['seasonTeam']['teamId']

            stat['player_firstname'] = player['seasonPlayer']['firstName']
            stat['player_lastname'] = player['seasonPlayer']['lastName']
            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"
            stat['player_extid'] = player['seasonPlayer']['playerId']

            item = {}
            item['2pts Attempts'] = player['twoPointShotsAttempted']
            item['2pts Made'] = player['twoPointShotsMade']
            item['3pts Attempts'] = player['threePointShotsAttempted']
            item['3pts Made'] = player['threePointShotsMade']
            item['Assists'] = player['assists']
            item['Block Shots'] = player['blocks']
            item['Defensive rebounds'] = player['defensiveRebounds']
            item['FT Attempts'] = player['freeThrowsAttempted']
            item['FT Made'] = player['freeThrowsMade']
            item['Minutes played'] = round(player['secondsPlayed'] / 60)
            item['Offensive rebounds'] = player['offensiveRebounds']
            item['Personal fouls'] = player['foulsCommitted']
            item['Points'] = player['points']
            item['Steals'] = player['steals']
            item['Total rebounds'] = player['totalRebounds']
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
        item['Defensive rebounds'] = stats['homeTeam']['coachStat']['defensiveRebounds']
        item['Offensive rebounds'] = stats['homeTeam']['coachStat']['offensiveRebounds']
        item['Total rebounds'] = stats['homeTeam']['coachStat']['totalRebounds']
        item['Turnovers'] = stats['homeTeam']['coachStat']['turnovers']
        item['Personal fouls'] = stats['homeTeam']['coachStat']['foulsCommitted']

        stat['items'] = item
        info['stats'].append(stat)

        # away
        players = stats['guestTeam']['playerStats']

        for player in players:
            stat = {}
            stat['team'] = player['seasonTeam']['teamId']

            stat['player_firstname'] = player['seasonPlayer']['firstName']
            stat['player_lastname'] = player['seasonPlayer']['lastName']
            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"
            stat['player_extid'] = player['seasonPlayer']['playerId']

            item = {}
            item['2pts Attempts'] = player['twoPointShotsAttempted']
            item['2pts Made'] = player['twoPointShotsMade']
            item['3pts Attempts'] = player['threePointShotsAttempted']
            item['3pts Made'] = player['threePointShotsMade']
            item['Assists'] = player['assists']
            item['Block Shots'] = player['blocks']
            item['Defensive rebounds'] = player['defensiveRebounds']
            item['FT Attempts'] = player['freeThrowsAttempted']
            item['FT Made'] = player['freeThrowsMade']
            item['Minutes played'] = round(player['secondsPlayed'] / 60)
            item['Offensive rebounds'] = player['offensiveRebounds']
            item['Personal fouls'] = player['foulsCommitted']
            item['Points'] = player['points']
            item['Steals'] = player['steals']
            item['Total rebounds'] = player['totalRebounds']
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
        item['Defensive rebounds'] = stats['guestTeam']['coachStat']['defensiveRebounds']
        item['Offensive rebounds'] = stats['guestTeam']['coachStat']['offensiveRebounds']
        item['Total rebounds'] = stats['guestTeam']['coachStat']['totalRebounds']
        item['Turnovers'] = stats['guestTeam']['coachStat']['turnovers']
        item['Personal fouls'] = stats['guestTeam']['coachStat']['foulsCommitted']

        stat['items'] = item
        info['stats'].append(stat)
    
    return info

def get_player(extid):
    token = get_token()
    
    if not token:
        return
    
    url = f'https://www.easycredit-bbl.de/_next/data/{token}/de-DE/spieler/{extid}.json?id={extid}'
    resp = requests.get(url)
    player = resp.json()['pageProps']['player']
    
    info = {}
    info['name'] = f"{player['firstName']} {player['lastName']}"
    info['firstname'] = player['firstName']
    info['lastname'] = player['lastName']
    info['extid'] = extid
    info['source'] = f'https://www.easycredit-bbl.de/spieler/{extid}'
    info['shirtNumber'] = player['shirtNumber']
    info['position'] = player['position']
    info['team'] = player['team']['name']
    info['dateOfBirth'] = player['birthDate']
    info['height'] = player['height']
    info['nationality'] = player['nationalities'][0]

    return info

def func_ecbbl(args):
    if args['f'] == 'schedule':
        games = get_schedule()
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(extid)
    elif args['f'] == 'player':
        extid = request.args.get('extid')
        
        return get_player(extid)