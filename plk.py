from library import *

def get_schedule(lpar, spar):
    results = []
    
    url = f'https://plk.pl/archiwum/{spar}/terminarz'

    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        scripts = soup.find_all('script')
        
        for script in scripts:
            if 'self.__next_f.push([1,"8:' in script.text:
                data = script.text.replace('self.__next_f.push([1,"8:', '').strip()[0:-5].replace('\\"', '"').replace('\\\\"', "'")
                schedules = json.loads(data)[3]['data']['schedule']

                for schedule in schedules:
                    queues = schedule['rounds'][0]['queues']

                    for queue in queues:
                        games = queue['games']

                        for game in games:
                            info = {}
                            info['round'] = game['round']['name']
                            info['playDate'] = datetime.fromisoformat(game['date'].strip('Z')).strftime('%Y-%m-%d')
                            
                            home_team = game['homeTeam']
                            info['homeTeam'] = {
                                'extid': f"{home_team['id']}_{home_team['slug']}",
                                'name': home_team['name']
                            }

                            visitor_team = game['guestTeam']
                            info['visitorTeam'] = {
                                'extid': f"{visitor_team['id']}_{visitor_team['slug']}",
                                'name': visitor_team['name']
                            }

                            if game['isFinished']:
                                info['state'] = 'Finished'

                                info['homeScores'] = {
                                    'final': game['resultHome']
                                }

                                info['visitorScores'] = {
                                    'final': game['resultGuest']
                                }
                            else:
                                info['state'] = 'Not Finished'

                            info['competition'] = lpar

                            info['extid'] = f"{game['id']}_{game['slug']}"
                            info['source'] = f"https://plk.pl/mecz/{game['id']}/{game['slug']}"

                            results.append(info)

                break
            
    return results

def get_boxscore(extid):
    game_extid = extid.split('_')[0]
    game_slug = extid.split('_')[1]

    url = f'https://plk.pl/mecz/{game_extid}/{game_slug}/statystyki'
    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        scripts = soup.find_all('script')

        for script in scripts:
            if 'self.__next_f.push([1,"d:' in script.text:
                data = script.text.replace('self.__next_f.push([1,"d:', '').strip()[0:-5].replace('\\"', '"').replace('\\\\"', "'")
                game = json.loads(data)[3]['children'][0][3]['gameData']['game']

                info = {}
                info['extid'] = extid
                info['source'] = url
                info['playDate'] = datetime.fromisoformat(game['date'].strip('Z')).strftime('%Y-%m-%d')

                home_team = game['homeTeam']
                info['homeTeam'] = {
                    'extid': f"{home_team['id']}_{game['slug'].split('-vs-')[0]}",
                    'name': home_team['name']
                }

                visitor_team = game['guestTeam']
                info['visitorTeam'] = {
                    'extid': f"{visitor_team['id']}_{game['slug'].split('-vs-')[0]}",
                    'name': visitor_team['name']
                }

                if game['isFinished']:
                    info['homeScores'] = {
                        'final': game['resultHome']
                    }

                    info['visitorScores'] = {
                        'final': game['resultGuest']
                    }

                    try:
                        info['homeScores']['extra'] = int(game['overtime'][0].split(':')[0])
                    except:
                        info['homeScores']['extra'] = 0

                    try:
                        info['visitorScores']['extra'] = int(game['overtime'][0].split(':')[1])
                    except:
                        info['visitorScores']['extra'] = 0

                    quarters = game['quarters']
                    qt_id = 0
                    for quarter in quarters:
                        qt_id += 1
                        try:
                            info['homeScores'][f'QT{qt_id}'] = int(quarters[0].split(':')[0])
                        except:
                            info['homeScores'][f'QT{qt_id}'] = 0

                        try:
                            info['visitorScores'][f'QT{qt_id}'] = int(quarters[0].split(':')[1])
                        except:
                            info['visitorScores'][f'QT{qt_id}'] = 0

                    # Stats
                    info['stats'] = []

                    home_players = home_team['players']

                    for player in home_players:
                        stat = {}
                        stat['team'] = info['homeTeam']['extid']

                        stat['player_name'] = f"{player['firstName']} {player['lastName']}"
                        stat['player_firstname'] = player['firstName']
                        stat['player_lastname'] = player['lastName']
                        stat['player_extid'] = f"{player['id']}_{player['slug']}"

                        item = {}
                        home_player_stats = home_team['gameStatistics']['playersStatistics']

                        for player_stat in home_player_stats:
                            if player_stat['playerId'] == player['id']:
                                item['2pts Attempts'] = player_stat['attemptTwoPts']
                                item['2pts Made'] = player_stat['madeTwoPts']
                                item['3pts Attempts'] = player_stat['attemptThreePts']
                                item['3pts Made'] = player_stat['madeThreePts']
                                item['Assists'] = player_stat['assists']
                                item['Block Shots'] = player_stat['blocks']
                                item['Defensive rebounds'] = player_stat['reboundsDefensive']
                                item['Offensive rebounds'] = player_stat['reboundsOffensive']
                                item['Total rebounds'] = player_stat['reboundsTotal']
                                item['FT Attempts'] = player_stat['attemptFreeThrowPts']
                                item['FT Made'] = player_stat['madeFreeThrowPts']
                                item['Minutes played'] = round(player_stat['playTimeSeconds'] / 60)
                                item['Personal fouls'] = player_stat['foulsPersonal']
                                item['Points'] = player_stat['points']
                                item['Steals'] = player_stat['steals']
                                item['Turnovers'] = player_stat['turnovers']

                                break

                        stat['items'] = item
                        info['stats'].append(stat)

                    stat = {}
                    stat['team'] = info['homeTeam']['extid']
                    stat['player_extid'] = 'team'
                    stat['player_firstname'] = ''
                    stat['player_lastname'] = '- TEAM -'
                    stat['player_name'] = '- TEAM -'

                    info['stats'].append(stat)

                    away_players = visitor_team['players']

                    for player in away_players:
                        stat = {}
                        stat['team'] = info['visitorTeam']['extid']

                        stat['player_name'] = f"{player['firstName']} {player['lastName']}"
                        stat['player_firstname'] = player['firstName']
                        stat['player_lastname'] = player['lastName']
                        stat['player_extid'] = f"{player['id']}_{player['slug']}"

                        item = {}
                        away_player_stats = visitor_team['gameStatistics']['playersStatistics']

                        for player_stat in away_player_stats:
                            if player_stat['playerId'] == player['id']:
                                item['2pts Attempts'] = player_stat['attemptTwoPts']
                                item['2pts Made'] = player_stat['madeTwoPts']
                                item['3pts Attempts'] = player_stat['attemptThreePts']
                                item['3pts Made'] = player_stat['madeThreePts']
                                item['Assists'] = player_stat['assists']
                                item['Block Shots'] = player_stat['blocks']
                                item['Defensive rebounds'] = player_stat['reboundsDefensive']
                                item['Offensive rebounds'] = player_stat['reboundsOffensive']
                                item['Total rebounds'] = player_stat['reboundsTotal']
                                item['FT Attempts'] = player_stat['attemptFreeThrowPts']
                                item['FT Made'] = player_stat['madeFreeThrowPts']
                                item['Minutes played'] = round(player_stat['playTimeSeconds'] / 60)
                                item['Personal fouls'] = player_stat['foulsPersonal']
                                item['Points'] = player_stat['points']
                                item['Steals'] = player_stat['steals']
                                item['Turnovers'] = player_stat['turnovers']

                                break

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
    
def get_player(extid, spar):
    player_id = extid.split('_')[0]
    player_slug = extid.split('_')[1]

    url = f'https://plk.pl/archiwum/{spar}/zawodnicy/{player_id}/{player_slug}'
    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        scripts = soup.find_all('script')

        player = None

        for script in scripts:
            if 'self.__next_f.push([1,"9:' in script.text:
                data = script.text.replace('self.__next_f.push([1,"9:', '').strip()[0:-5].replace('\\"', '"')
                
                player = json.loads(data)[3]['children'][0][3]['player']
                break

        if player:
            info = {}
            info['name'] = f"{player['firstName']} {player['lastName']}"
            info['firstname'] = player['firstName']
            info['lastname'] = player['lastName']
            info['extid'] = extid
            info['source'] = url
            info['shirtNumber'] = player['shirtNumber']
            info['position'] = player['positions'][0]
            info['team'] = player['team']['name']
            info['dateOfBirth'] = player['birthDate']
            info['height'] = player['height']
            info['nationality'] = player['passport']

            return info

def func_plk(args):
    if args['f'] == 'schedule':
        games = []
        schedule = get_schedule(args['lpar'], args['spar'])
        games.extend(schedule)
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'])
    elif args['f'] == 'player':
        return get_player(args['extid'], args['spar'])
    