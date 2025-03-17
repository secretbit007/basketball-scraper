from library import *

def get_schedule(lpar, spar):
    games = []
    spar_args = spar.split(';')
    url = f'https://widget.wh.geniussports.com/widget//?{spar_args[0]}'
    resp = requests.get(url)
    extracted = re.search('var html = "(.+)";\n', resp.text).group(1).replace("\\\"", '"').replace("\\/", "/")
    soup = BeautifulSoup(extracted, 'html.parser')
    matches = soup.find_all('li', class_='spls_lsmatch')
    
    for match in matches:
        game = {}
        game['competition'] = match.find('span', class_='spls_matchcomp').text
        
        if len(spar_args) == 2:
            if game['competition'].strip().lower() != spar_args[1].strip().lower():
                continue
        
        if lpar == 'ESAKE':
            game['playDate'] = datetime.strptime(match.find('span', class_='spls_datefield').text, '%b %d, %Y').strftime('%Y-%m-%d')
        else:
            game['playDate'] = datetime.strptime(match.find('span', class_='spls_datefield').text, '%d/%m/%Y').strftime('%Y-%m-%d')
        game['round'] = '-'
        game['state'] = match.find('span', class_='spls_matchstatus').text
        game['type'] = '-'
        
        teams = match.find_all('span', class_='spteam')
        
        game['homeTeam'] = {
            'extid': teams[0]['class'][-1],
            'name': teams[0].find('span', class_='teamname').text
        }
        game['homeScores'] = {
            'final': 0
        }
        
        if teams[0].find('span', class_='score').text != '':
            game['homeScores']['final'] = teams[0].find('span', class_='score').text
        
        game['visitorTeam'] = {
            'extid': teams[1]['class'][-1],
            'name': teams[1].find('span', class_='teamname').text
        }
        game['visitorScores'] = {
            'final': 0
        }
        
        if teams[1].find('span', class_='score').text != '':
            game['visitorScores']['final'] = teams[1].find('span', class_='score').text

        game['extid'] = match.a['href'].split('/')[-2]
        game['source'] = match.a['href']
        games.append(game)
        
    return games

def get_boxscore(lpar, ext):
    extid = ext.split('_')[0]
    
    if lpar == 'FUBB':
        url = f'https://fibalivestats.dcd.shared.geniussports.com/u/FUBB/{extid}/index_en_US.html'
    
    if lpar == 'BIH':
        url = f'https://fibalivestats.dcd.shared.geniussports.com/u/BIH/{extid}/index_en_AU.html'
        
    if lpar == 'ESAKE':
        url = f'https://fibalivestats.dcd.shared.geniussports.com/u/ESAKE/{extid}/index.html'

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
                
                if lpar == 'FUBB':
                    info['playDate'] = datetime.strptime(match_detail.p.text.split(' ')[-1], '%m/%d/%y').strftime('%Y-%m-%d')
                    
                if lpar == 'BIH':
                    info['playDate'] = datetime.strptime(match_detail.p.text.split(' ')[-1], '%d/%m/%y').strftime('%Y-%m-%d')
                    
                info['source'] = url
                info['type'] = '-'
                
                if json_detail['tm']['1']['nameInternational'] != '':
                    info['homeTeam'] = {
                        'name': json_detail['tm']['1']['nameInternational']
                    }
                else:
                    info['homeTeam'] = {
                        'name': json_detail['tm']['1']['name']
                    }
                
                if json_detail['tm']['1']['code'] != '':
                    info['homeTeam']['extid'] = f"{lpar.lower()}_{json_detail['tm']['1']['code']}"
                else:
                    info['homeTeam']['extid'] = f"{lpar.lower()}_{json_detail['tm']['1']['shortName']}"

                if json_detail['tm']['2']['nameInternational'] != '':
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['nameInternational']
                    }
                else:
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['name']
                    }
                
                if json_detail['tm']['2']['code'] != '':
                    info['visitorTeam']['extid'] = f"{lpar.lower()}_{json_detail['tm']['2']['code']}"
                else:
                    info['visitorTeam']['extid'] = f"{lpar.lower()}_{json_detail['tm']['2']['shortName']}"

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

                    stat['player_firstname'] = player['internationalFirstName']
                    stat['player_lastname'] = player['internationalFamilyName']
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

                    stat['player_firstname'] = player['internationalFirstName']
                    stat['player_lastname'] = player['internationalFamilyName']
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
        return {'error': 'Something went wrong!'}
    else:
        return {'error': 'Something went wrong!'}

def func_fiba(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        spar = request.args.get('spar')

        games = get_schedule(args['lpar'], spar)

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(args['lpar'], extid)