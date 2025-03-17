from library import *

def get_schedule(year):
    games = []
    
    url_seasons = 'https://www.sblherr.se/api/sports/season-series-game-types-filter'
    resp_seasons = requests.get(url_seasons)
    season_id = None
    game_type_id = None
    series_id = None
    
    for season in resp_seasons.json()['season']:
        if season['code'] == year:
            season_id = season['uuid']
            break
        
    for game_type in resp_seasons.json()['gameType']:
        if game_type['code'] == 'regular':
            game_type_id = game_type['uuid']
            break
        
    for serie in resp_seasons.json()['series']:
        if serie['code'] == 'SBL':
            series_id = serie['uuid']
            break
    
    url_matches = f'https://www.sblherr.se/api/sports/game-info?seasonUuid={season_id}&seriesUuid={series_id}&gameTypeUuid={game_type_id}&gamePlace=all&played=all'
    resp_matches = requests.get(url_matches)

    for match in resp_matches.json()['gameInfo']:
        game = {}
        game['competition'] = 'SBF'
        game['playDate'] = match['startDateTime'].split('T')[0]
        game['round'] = '-'
        
        game['state'] = match['state']
        game['type'] = 'Regular'
        
        game['homeTeam'] = {
            'extid': match['homeTeamInfo']['uuid'],
            'name': match['homeTeamInfo']['names']['full']
        }
        game['homeScores'] = {
            'final': 0
        }
        
        game['visitorTeam'] = {
            'extid': match['awayTeamInfo']['uuid'],
            'name': match['awayTeamInfo']['names']['full']
        }
        
        game['visitorScores'] = {
            'final': 0
        }
        
        if game['state'] == 'post-game':
            game['homeScores']['final'] = match['homeTeamInfo']['score']
            game['visitorScores']['final'] = match['awayTeamInfo']['score']
            
            url_detail = f"https://www.sblherr.se/api/articles/custom-newslist/list?page=0&pagesize=1&matchAllTags=game.{match['uuid']}.post"
            resp_detail = requests.get(url_detail)
            view_id = resp_detail.json()['data']['articleItems'][0]['id']
            
            url_view = f"https://www.sblherr.se/api/articles/{view_id}/view"
            resp_view = requests.get(url_view)
            
            game['source'] = re.search(r'https://fibalivestats.dcd.shared.geniussports.com/u/SBF/\d+(/bs.html)?', resp_view.json()['data']['body']).group(0)
                
            game['extid'] = game['source'].split('/')[-2]
        else:
            url_extid = f'https://www.sblherr.se/api/sports/process-url-templates?url=aHR0cHM6Ly9maWJhbGl2ZXN0YXRzLmRjZC5zaGFyZWQuZ2VuaXVzc3BvcnRzLmNvbS91L1NCRi97eyBnYW1lOmdlbml1cy1iYXNrZXRiYWxsOmV4dElkIH19&gameUuid={match["uuid"]}'
            resp_extid = requests.get(url_extid)
            
            game['source'] = resp_extid.json()['url']
            game['extid'] = game['source'].split('/')[-1]
            
        games.append(game)
        
    return games

def get_boxscore(extid):
    url = f'https://www.fibalivestats.com/webcast/SBF/{extid}/'

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
                
                if json_detail['tm']['1']['code'] != '':
                    info['homeTeam']['extid'] = f"sbf_{json_detail['tm']['1']['code']}"
                else:
                    info['homeTeam']['extid'] = f"sbf_{json_detail['tm']['1']['shortName']}"

                if json_detail['tm']['2']['nameInternational'] != '':
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['nameInternational']
                    }
                else:
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['name']
                    }
                
                if json_detail['tm']['2']['code'] != '':
                    info['visitorTeam']['extid'] = f"sbf_{json_detail['tm']['2']['code']}"
                else:
                    info['visitorTeam']['extid'] = f"sbf_{json_detail['tm']['2']['shortName']}"

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

def func_sbf(args):
    if args['f'] == 'schedule':
        season = request.args.get('season')
        games = get_schedule(season)

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(extid)
