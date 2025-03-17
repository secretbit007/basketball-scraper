from library import *

def value(r):
    if (r == 'I'):
        return 1
    if (r == 'V'):
        return 5
    if (r == 'X'):
        return 10
    if (r == 'L'):
        return 50
    if (r == 'C'):
        return 100
    if (r == 'D'):
        return 500
    if (r == 'M'):
        return 1000
    return -1
 
def romanToDecimal(str):
    res = 0
    i = 0
 
    while (i < len(str)):
 
        # Getting value of symbol s[i]
        s1 = value(str[i])
 
        if (i + 1 < len(str)):
 
            # Getting value of symbol s[i + 1]
            s2 = value(str[i + 1])
 
            # Comparing both values
            if (s1 >= s2):
 
                # Value of current symbol is greater
                # or equal to the next symbol
                res = res + s1
                i = i + 1
            else:
 
                # Value of current symbol is greater
                # or equal to the next symbol
                res = res + s2 - s1
                i = i + 2
        else:
            res = res + s1
            i = i + 1
 
    return res

def get_schedule():
    games = []
    
    url_rounds = 'https://www.basketbolli.com/Results?leagueId=62'
    resp_rounds = requests.get(url_rounds)
    soup_rounds = BeautifulSoup(resp_rounds.text, 'html.parser')
    rounds = soup_rounds.find_all('table', 'table-rez')

    for mround in rounds:
        matches = mround.tbody.find_all('tr')
        for match in matches:
            game = {}
            game['competition'] = 'KOS'
            
            if match.find('th').text.strip() == ':':
                game['playDate'] = datetime.strptime(mround.thead.find_all('th')[-1].text.split('/')[-1].strip(), '%d.%m.%Y').strftime('%Y-%m-%d')
                game['state'] = 'Scheduled'
                game['extid'] = '-'
                game['source'] = '-'
            else:
                url_detail = match.find('a')['href']
                resp_detail = requests.get(url_detail)
                soup_detail = BeautifulSoup(resp_detail.text, 'html.parser')
                match_details = soup_detail.find_all('div', class_='matchDetail')
                
                for match_detail in match_details:
                    title = match_detail.h6.text
                    
                    if title == 'Game Details':
                        game['playDate'] = datetime.strptime(match_detail.p.text.split(' ')[-1].strip(), '%d/%m/%y').strftime('%Y-%m-%d')
                        break
                    
                game['state'] = 'Completed'
                game['extid'] = url_detail.split('/')[-2]
                game['source'] = url_detail
                
            game['round'] = romanToDecimal(mround.thead.find_all('th')[0].text.split(' ')[-1])
            game['type'] = 'Regular'
            
            game['homeTeam'] = {
                'extid': slugify(match.find('a').text.split(':')[0].strip(), allow_unicode=True),
                'name': match.find('a').text.split(':')[0].strip()
            }
            game['homeScores'] = {
                'final': 0
            }
            
            if game['state'] == 'Completed':
                game['homeScores']['final'] = match.find('th').text.split(':')[0].strip()
            
            game['visitorTeam'] = {
                'extid': slugify(match.find('a').text.split(':')[1].strip(), allow_unicode=True),
                'name': match.find('a').text.split(':')[1].strip()
            }
            game['visitorScores'] = {
                'final': 0
            }
            
            if game['state'] == 'Completed':
                game['visitorScores']['final'] = match.find('th').text.split(':')[1].strip()

            games.append(game)
        
    return games

def get_boxscore(extid):
    url = f'https://fibalivestats.dcd.shared.geniussports.com/u/KOS/{extid}/'

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
                
                info['homeTeam']['extid'] = f"kos_{json_detail['tm']['1']['code']}"

                if json_detail['tm']['2']['nameInternational'] != '':
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['nameInternational']
                    }
                else:
                    info['visitorTeam'] = {
                        'name': json_detail['tm']['2']['name']
                    }
                
                info['visitorTeam']['extid'] = f"kos_{json_detail['tm']['2']['code']}"

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

def func_kos(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        
        games = get_schedule()

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extid = request.args.get('extid')
        
        return get_boxscore(extid)
