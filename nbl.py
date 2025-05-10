from library import *

def get_schedule(year):
    games = []
    
    url_season = 'https://prod.services.nbl.com.au/api_cache/nbl/genius?route=leagues/7/competitions&filter[competitionName]=NBL&fields=season,competitionId&filter%5Btenant%5D=nbl'
    resp_season = requests.get(url_season)
    
    for season in resp_season.json():
        if season['season'] == year:
            comp_id = season['competitionId']
    
    url_matches = f'https://prod.services.nbl.com.au/api_cache/nbl/genius?route=competitions/{comp_id}/matches&fields=matchType,matchId,matchStatus,matchTimeUTC,competitors,roundNumber,venue,ticketURL,liveapidata&filter[matchStatus]=!DRAFT&filter%5Btenant%5D=nbl'
    resp_matches = requests.get(url_matches)

    for match in resp_matches.json():
        game = {}
        game['competition'] = 'NBL'
        game['playDate'] = match['matchTimeUTC'].split(' ')[0]
        game['round'] = match['roundNumber']
        game['state'] = match['matchStatus']
        game['type'] = match['matchType']
        
        game['homeTeam'] = {
            'extid': match['competitors'][0]['teamId'],
            'name': match['competitors'][0]['teamNameInternational']
        }
        game['homeScores'] = {
            'final': 0
        }
        
        if match['competitors'][0]['scoreString'] != '':
            game['homeScores']['final'] = match['competitors'][0]['scoreString']
        
        game['visitorTeam'] = {
            'extid': match['competitors'][1]['teamId'],
            'name': match['competitors'][1]['teamNameInternational']
        }
        game['visitorScores'] = {
            'final': 0
        }
        
        if match['competitors'][1]['scoreString'] != '':
            game['visitorScores']['final'] = match['competitors'][1]['scoreString']

        game['extid'] = match['matchId']
        game['source'] = f'https://nbl.com.au/games/{game["extid"]}'
        games.append(game)
        
    return games

def get_boxscore(extid):
    url = f'https://fibalivestats.dcd.shared.geniussports.com/u/NBL/{extid}/'

    resp = requests.get(url)
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        match_details = soup.find_all('div', class_='matchDetail')

        for match_detail in match_details:
            title = match_detail.h6.text
            
            if title == 'Game Details':
                url_detail = f'https://fibalivestats.dcd.shared.geniussports.com/data/{extid}/data.json'
                resp_detail = requests.get(url_detail)
                json_detail = resp_detail.json()
                
                info = {}
                info['extid'] = extid
                info['playDate'] = datetime.strptime(match_detail.p.text.split(' ')[-1], '%d/%m/%y').strftime('%Y-%m-%d')
                info['source'] = url
                info['type'] = json_detail['periodType']
                
                if json_detail['tm']['1']['nameInternational'] != '':
                    info['homeTeam'] = {
                        'name': json_detail['tm']['1']['nameInternational']
                    }
                else:
                    info['homeTeam'] = {
                        'name': json_detail['tm']['1']['name']
                    }
                
                info['homeTeam']['extid'] = f"nbl_{json_detail['tm']['1']['code']}"

                if json_detail['tm']['2']['nameInternational'] != '':
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['nameInternational']
                    }
                else:
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['name']
                    }
                
                info['visitorTeam']['extid'] = f"nbl_{json_detail['tm']['2']['code']}"

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

                info['homeScores']['final'] = json_detail['tm']['1']['full_score']

                info['homeScores']['QT1'] = json_detail['tm']['1']['p1_score']
                info['homeScores']['QT2'] = json_detail['tm']['1']['p2_score']
                info['homeScores']['QT3'] = json_detail['tm']['1']['p3_score']
                info['homeScores']['QT4'] = json_detail['tm']['1']['p4_score']
                
                try:
                    info['homeScores']['extra'] = json_detail['tm']['1']['ot_score']
                except:
                    pass
                    
                info['visitorScores']['final'] = json_detail['tm']['2']['full_score']

                info['visitorScores']['QT1'] = json_detail['tm']['2']['p1_score']
                info['visitorScores']['QT2'] = json_detail['tm']['2']['p2_score']
                info['visitorScores']['QT3'] = json_detail['tm']['2']['p3_score']
                info['visitorScores']['QT4'] = json_detail['tm']['2']['p4_score']
                
                try:
                    info['visitorScores']['extra'] = json_detail['tm']['2']['ot_score']
                except:
                    pass

                # home
                pl_keys = json_detail['tm']['1']['pl'].keys()

                for pl_key in pl_keys:
                    player = json_detail['tm']['1']['pl'][pl_key]
                    
                    stat = {}
                    stat['team'] = info['homeTeam']['extid']

                    stat['player_firstname'] = player['firstName']
                    stat['player_lastname'] = player['familyName']
                    stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"
                    stat['player_extid'] = slugify(stat['player_name'], allow_unicode=True)

                    item = {}
                    item['2pts Attempts'] = player['sTwoPointersAttempted']
                    item['2pts Made'] = player['sTwoPointersMade']
                    item['3pts Attempts'] = player['sThreePointersAttempted']
                    item['3pts Made'] = player['sThreePointersMade']
                    item['Assists'] = player['sAssists']
                    item['Block Shots'] = player['sBlocks']
                    item['Defensive rebounds'] = player['sReboundsDefensive']
                    item['FT Attempts'] = player['sFreeThrowsAttempted']
                    item['FT Made'] = player['sFreeThrowsMade']
                    item['Minutes played'] = round(int(player['sMinutes'].split(':')[0]) + float(player['sMinutes'].split(':')[1]) / 60)
                    item['Offensive rebounds'] = player['sReboundsOffensive']
                    item['Personal fouls'] = player['sFoulsPersonal']
                    item['Points'] = player['sPoints']
                    item['Steals'] = player['sSteals']
                    item['Total rebounds'] = player['sReboundsTotal']
                    item['Turnovers'] = player['sTurnovers']

                    stat['items'] = item
                    info['stats'].append(stat)

                stat = {}
                stat['team'] = info['homeTeam']['extid']
                stat['player_extid'] = 'team'
                stat['player_firstname'] = ''
                stat['player_lastname'] = '- TEAM -'
                stat['player_name'] = '- TEAM -'

                item = {}
                item['Defensive rebounds'] = json_detail['tm']['1']['tot_sReboundsTeamDefensive']
                item['Offensive rebounds'] = json_detail['tm']['1']['tot_sReboundsTeamOffensive']
                item['Total rebounds'] = json_detail['tm']['1']['tot_sReboundsTeam']
                item['Turnovers'] = json_detail['tm']['1']['tot_sTurnoversTeam']
                item['Personal fouls'] = json_detail['tm']['1']['tot_sFoulsTeam']

                stat['items'] = item
                info['stats'].append(stat)

                # away
                pl_keys = json_detail['tm']['2']['pl'].keys()

                for pl_key in pl_keys:
                    player = json_detail['tm']['2']['pl'][pl_key]
                    
                    stat = {}
                    stat['team'] = info['visitorTeam']['extid']

                    stat['player_firstname'] = player['firstName']
                    stat['player_lastname'] = player['familyName']
                    stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"
                    stat['player_extid'] = slugify(stat['player_name'], allow_unicode=True)

                    item = {}
                    item['2pts Attempts'] = player['sTwoPointersAttempted']
                    item['2pts Made'] = player['sTwoPointersMade']
                    item['3pts Attempts'] = player['sThreePointersAttempted']
                    item['3pts Made'] = player['sThreePointersMade']
                    item['Assists'] = player['sAssists']
                    item['Block Shots'] = player['sBlocks']
                    item['Defensive rebounds'] = player['sReboundsDefensive']
                    item['FT Attempts'] = player['sFreeThrowsAttempted']
                    item['FT Made'] = player['sFreeThrowsMade']
                    item['Minutes played'] = round(int(player['sMinutes'].split(':')[0]) + float(player['sMinutes'].split(':')[1]) / 60)
                    item['Offensive rebounds'] = player['sReboundsOffensive']
                    item['Personal fouls'] = player['sFoulsPersonal']
                    item['Points'] = player['sPoints']
                    item['Steals'] = player['sSteals']
                    item['Total rebounds'] = player['sReboundsTotal']
                    item['Turnovers'] = player['sTurnovers']

                    stat['items'] = item
                    info['stats'].append(stat)

                stat = {}
                stat['team'] = info['visitorTeam']['extid']
                stat['player_extid'] = 'team'
                stat['player_firstname'] = ''
                stat['player_lastname'] = '- TEAM -'
                stat['player_name'] = '- TEAM -'

                item = {}
                item['Defensive rebounds'] = json_detail['tm']['2']['tot_sReboundsTeamDefensive']
                item['Offensive rebounds'] = json_detail['tm']['2']['tot_sReboundsTeamOffensive']
                item['Total rebounds'] = json_detail['tm']['2']['tot_sReboundsTeam']
                item['Turnovers'] = json_detail['tm']['2']['tot_sTurnoversTeam']
                item['Personal fouls'] = json_detail['tm']['2']['tot_sFoulsTeam']

                stat['items'] = item
                info['stats'].append(stat)
                
                return info
    else:
        return {'error': 'Something went wrong!'}

def func_nbl(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        year = f"{args['season']}-{int(args['season']) + 1}"
        
        games = get_schedule(year)

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(extid)
    elif args['f'] == 'player':
        return {'error': 'No player data existed!'}
