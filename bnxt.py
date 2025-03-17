from library import *

def get_schedule(year):
    games = []
    
    headers = {
        'X-Authorization': 'BWSyE7sgg9QAurh2JX9cpjzjGc652BWLuNUS',
        'X-Localization': 'en'
    }
    
    url_match = f'https://bnxt.sportpress.info/api/v1/schedule/club/{int(year) + 1}?clubs[0]=1&clubs[1]=2&month=-1'
    resp_match = requests.get(url_match, headers=headers)
    
    for match in resp_match.json()['data']:
        game = {}
        game['competition'] = match['competition']['name']
        game['playDate'] = match['game_time'].split(' ')[0]
        game['round'] = match['round']['name']
        game['state'] = match['status']
        game['type'] = match['phase']['name']
        
        game['homeTeam'] = {
            'extid': match['competitors'][0]['competition_team']['id'],
            'name': match['competitors'][0]['competition_team']['name']
        }
        game['homeScores'] = {
            'final': match['competitors'][0]['finalScore']
        }
        
        game['visitorTeam'] = {
            'extid': match['competitors'][1]['competition_team']['id'],
            'name': match['competitors'][1]['competition_team']['name']
        }
        game['visitorScores'] = {
            'final': match['competitors'][1]['finalScore']
        }

        game['extid'] = match['id']
        game['source'] = f'https://bnxtleague.com/en/game-report/{match["id"]}'
        games.append(game)
        
    return games

def get_boxscore(extid):
    headers = {
        'X-Authorization': 'BWSyE7sgg9QAurh2JX9cpjzjGc652BWLuNUS',
        'X-Localization': 'en'
    }
    url_comp = f'https://bnxt.sportpress.info/api/v1/schedule/find/{extid}'
    resp_comp = requests.get(url_comp, headers=headers)
    data_comp = resp_comp.json()['data']
    
    info = {}
    info['extid'] = extid
    info['playDate'] = data_comp['game_time'].split(' ')[0]
    info['source'] = f'https://bnxtleague.com/en/game-report/{extid}'
    info['type'] = data_comp['phase']['name']
    
    info['homeTeam'] = {
        'extid': data_comp['competitors'][0]['competition_team']['id'],
        'name': data_comp['competitors'][0]['competition_team']['name']
    }
    
    info['visitorTeam'] = {
        'extid': data_comp['competitors'][1]['competition_team']['id'],
        'name': data_comp['competitors'][1]['competition_team']['name']
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
    
    if data_comp['status'] == 'finished':
        info['homeScores']['final'] = data_comp['competitors'][0]['finalScore']
        info['homeScores']['QT1'] = data_comp['competitors'][0]['period_scores'][0]['score']
        info['homeScores']['QT2'] = data_comp['competitors'][0]['period_scores'][1]['score']
        info['homeScores']['QT3'] = data_comp['competitors'][0]['period_scores'][2]['score']
        info['homeScores']['QT4'] = data_comp['competitors'][0]['period_scores'][3]['score']
        info['homeScores']['extra'] = info['homeScores']['final'] - (info['homeScores']['QT1'] + info['homeScores']['QT2'] + info['homeScores']['QT3'] + info['homeScores']['QT4'])
            
        info['visitorScores']['final'] = data_comp['competitors'][1]['finalScore']
        info['visitorScores']['QT1'] = data_comp['competitors'][1]['period_scores'][0]['score']
        info['visitorScores']['QT2'] = data_comp['competitors'][1]['period_scores'][1]['score']
        info['visitorScores']['QT3'] = data_comp['competitors'][1]['period_scores'][2]['score']
        info['visitorScores']['QT4'] = data_comp['competitors'][1]['period_scores'][3]['score']
        info['visitorScores']['extra'] = info['visitorScores']['final'] - (info['visitorScores']['QT1'] + info['visitorScores']['QT2'] + info['visitorScores']['QT3'] + info['visitorScores']['QT4'])

        url_boxscore = f'https://bnxt.sportpress.info/api/v1/boxscore/game/{data_comp["competition"]["id"]}/{extid}'
        resp_boxscore = requests.get(url_boxscore, headers=headers)
        stats = resp_boxscore.json()['data']
        
        # home
        players = stats[0]['players']

        for player in players:
            stat = {}
            stat['team'] = player['competition_team_id']
            stat['player_firstname'] = player['player']['first_name']
            stat['player_lastname'] = player['player']['last_name']
            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"
            stat['player_extid'] = player['roster_id']

            item = {}
            item['2pts Attempts'] = player['two_point_all']
            item['2pts Made'] = player['two_point_made']
            item['3pts Attempts'] = player['three_point_all']
            item['3pts Made'] = player['three_point_made']
            item['Assists'] = player['assist']
            item['Block Shots'] = player['block']
            item['Defensive rebounds'] = player['defensive_rebound']
            item['FT Attempts'] = player['free_throw_all']
            item['FT Made'] = player['free_throw_made']
            item['Minutes played'] = player['minute']
            item['Offensive rebounds'] = player['offensive_rebound']
            item['Personal fouls'] = player['foul']
            item['Points'] = player['points']
            item['Steals'] = player['steal']
            item['Total rebounds'] = player['total_rebound']
            item['Turnovers'] = player['turnover']

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['homeTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        info['stats'].append(stat)

        # away
        players = stats[1]['players']

        for player in players:
            stat = {}
            stat['team'] = player['competition_team_id']
            stat['player_firstname'] = player['player']['first_name']
            stat['player_lastname'] = player['player']['last_name']
            stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"
            stat['player_extid'] = player['roster_id']

            item = {}
            item['2pts Attempts'] = player['two_point_all']
            item['2pts Made'] = player['two_point_made']
            item['3pts Attempts'] = player['three_point_all']
            item['3pts Made'] = player['three_point_made']
            item['Assists'] = player['assist']
            item['Block Shots'] = player['block']
            item['Defensive rebounds'] = player['defensive_rebound']
            item['FT Attempts'] = player['free_throw_all']
            item['FT Made'] = player['free_throw_made']
            item['Minutes played'] = player['minute']
            item['Offensive rebounds'] = player['offensive_rebound']
            item['Personal fouls'] = player['foul']
            item['Points'] = player['points']
            item['Steals'] = player['steal']
            item['Total rebounds'] = player['total_rebound']
            item['Turnovers'] = player['turnover']

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['visitorTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        info['stats'].append(stat)
    
    return info

def get_player(extid):
    headers = {
        'X-Authorization': 'BWSyE7sgg9QAurh2JX9cpjzjGc652BWLuNUS',
        'X-Localization': 'en'
    }
    url = f'https://bnxt.sportpress.info/api/v1/roster/find/{extid}'
    resp = requests.get(url, headers=headers)
    data = resp.json()['data']
    
    info = {}
    info['name'] = f"{data['player']['first_name']} {data['player']['last_name']}"
    info['firstname'] = data['player']['first_name']
    info['lastname'] = data['player']['last_name']
    info['extid'] = extid
    info['source'] = f'https://bnxtleague.com/en/player-statistics/?player_id={extid}&team_id={data["competition_team_id"]}'
    info['shirtNumber'] = data['lastGameStatistics']['jersey']
    info['position'] = data['player_position']['name']
    info['team'] = data['competition_team']['name']
    info['dateOfBirth'] = data['player']['birthdate']
    info['height'] = data['height']
    info['nationality'] = data['player']['nationality_code']
    info['weight'] = data['weight']

    return info

def func_bnxt(args):
    if args['f'] == 'schedule':
        season = request.args.get('season')
        games = get_schedule(season)
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(extid)
    elif args['f'] == 'player':
        extid = request.args.get('extid')
        
        return get_player(extid)