from library import *

def get_schedule(lpar, spar, match_type):
    games = []
    
    if match_type == 'main':
        url = f'https://plk.pl/archiwum/{spar}/terminarz'
    elif match_type == 'pof':
        url = f'https://plk.pl/archiwum/{spar}/terminarz/play-off'
    elif match_type == "mc":
        url = f'https://plk.pl/archiwum/{spar}/terminarz/puchar-polski-mezczyzn'
    elif match_type == "msc":
        url = f'https://plk.pl/archiwum/{spar}/terminarz/superpuchar-polski-mezczyzn'

    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        match_cards = soup.find_all('div', class_='shadow-card')

        for match_card in match_cards:
            game = {}

            round_elem = match_card.find('div', class_='uppercase')
            
            match_round = round_elem.find('span', class_='whitespace-pre').text.strip().split(' ')[0]
            match_time = round_elem.find('span', class_='text-support').text.strip()

            game['round'] = match_round
            game['playDate'] = datetime.strptime(match_time, '%d.%m.%Y / %H:%M').strftime('%Y-%m-%d')

            points = list(match_card.find('div', class_='items-start').children)

            # Home
            home_links = points[0].find_all('a')
            home_name = home_links[1].text.strip()
            home_score = home_links[2].text.strip()
            home_extid = home_links[0].get('href').split('/')[-2] + '_' + home_links[0].get('href').split('/')[-1]

            game['homeTeam'] = {
                'extid': home_extid,
                'name': home_name
            }
            game['homeScores'] = {
                'final': home_score
            }

            # Away
            away_links = points[1].find_all('a')
            away_name = away_links[1].text.strip()
            away_score = away_links[2].text.strip()
            away_extid = away_links[0].get('href').split('/')[-2] + '_' + away_links[0].get('href').split('/')[-1]

            game['visitorTeam'] = {
                'extid': away_extid,
                'name': away_name
            }
            game['visitorScores'] = {
                'final': away_score
            }

            game['state'] = 'Finished'
            game['competition'] = lpar

            if match_type == 'main':
                game['type'] = 'Main Round'
            elif match_type == 'pof':
                game['type'] = 'Play-off'

            game_url = list(match_card.children)[-1].get('href')
            game['extid'] = game_url.split('/')[-2] + '_' + game_url.split('/')[-1] + '_' + match_type
            game['source'] = 'https://plk.pl' + game_url

            games.append(game)
            
    return games

def get_boxscore(extid):
    game_extid = extid.split('_')[0]
    game_slug = extid.split('_')[1]
    game_type = extid.split('_')[2]

    url = f'https://plk.pl/mecz/{game_extid}/{game_slug}/statystyki'
    resp = requests.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        main = soup.find("main")

        info = {}
        info['extid'] = extid
        info['source'] = url

        if game_type == 'main':
            info['type'] = 'Main Round'
        elif game_type == 'pof':
            info['type'] = "Play-off"

        match_time = main.find('span', class_='text-white/80').text
        info['playDate'] = datetime.strptime(match_time, '%d.%m.%Y / %H:%M').strftime('%Y-%m-%d')

        container = main.find('div', class_='container', recursive=False)
        tables = container.find('div').find_all('div', recursive=False)

        scores = main.find('h1', recursive=False).find('div').find_all('div', recursive=False)[-1].find_all('div')

        # Home
        home_elem = tables[0]
        home_link = home_elem.find('a').get('href')
        home_name = home_elem.find('h2').text
        home_extid = home_link.split('/')[-2] + '_' + home_link.split('/')[-1]

        info['homeTeam'] = {
            'extid': home_extid,
            'name': home_name
        }
        info['homeScores'] = {
            'final': int(main.find('h1', recursive=False).find('div').find_all('div', recursive=False)[1].find_all('div', recursive=False)[0].find('span', recursive=False).text.strip())
        }

        try:
            info['homeScores']['QT1'] = int(scores[0].find_all('span')[0].text.strip())
        except:
            info['homeScores']['QT1'] = 0

        try:
            info['homeScores']['QT2'] = int(scores[1].find_all('span')[0].text.strip())
        except:
            info['homeScores']['QT2'] = 0

        try:
            info['homeScores']['QT3'] = int(scores[2].find_all('span')[0].text.strip())
        except:
            info['homeScores']['QT3'] = 0

        try:
            info['homeScores']['QT4'] = int(scores[3].find_all('span')[0].text.strip())
        except:
            info['homeScores']['QT4'] = 0

        info['homeScores']['extra'] = info['homeScores']['final'] - info['homeScores']['QT1'] - info['homeScores']['QT2'] - info['homeScores']['QT3'] - info['homeScores']['QT4']

        # Away
        away_elem = tables[1]
        away_link = away_elem.find('a').get('href')
        away_name = away_elem.find('h2').text
        away_extid = away_link.split('/')[-2] + '_' + away_link.split('/')[-1]

        info['visitorTeam'] = {
            'extid': away_extid,
            'name': away_name
        }
        info['visitorScores'] = {
            'final': int(main.find('h1', recursive=False).find('div').find_all('div', recursive=False)[1].find_all('div', recursive=False)[2].find('span', recursive=False).text.strip())
        }

        try:
            info['visitorScores']['QT1'] = int(scores[0].find_all('span')[1].text.strip())
        except:
            info['visitorScores']['QT1'] = 0

        try:
            info['visitorScores']['QT2'] = int(scores[1].find_all('span')[1].text.strip())
        except:
            info['visitorScores']['QT2'] = 0

        try:
            info['visitorScores']['QT3'] = int(scores[2].find_all('span')[1].text.strip())
        except:
            info['visitorScores']['QT3'] = 0

        try:
            info['visitorScores']['QT4'] = int(scores[3].find_all('span')[1].text.strip())
        except:
            info['visitorScores']['QT4'] = 0

        info['visitorScores']['extra'] = info['visitorScores']['final'] - info['visitorScores']['QT1'] - info['visitorScores']['QT2'] - info['visitorScores']['QT3'] - info['visitorScores']['QT4']

        # Stats
        info['stats'] = []
        scripts = soup.find_all('script')
        game = None

        for script in scripts:
            if 'self.__next_f.push([1,"d:' in script.text:
                data = script.text.replace('self.__next_f.push([1,"d:', '').strip()[0:-5].replace('\\"', '"').replace('\\\\"', "'")
                game = json.loads(data)[3]['children'][0][3]['gameData']['game']
                break

        if game:
            # Home
            home_data = game['homeTeam']
            home_players = home_data['players']

            for player in home_players:
                stat = {}
                stat['team'] = info['homeTeam']['extid']

                stat['player_name'] = f"{player['firstName']} {player['lastName']}"
                stat['player_firstname'] = player['firstName']
                stat['player_lastname'] = player['lastName']
                stat['player_extid'] = f"{player['id']}_{player['slug']}"

                item = {}
                home_player_stats = home_data['gameStatistics']['playersStatistics']

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
                        item['Minutes played'] = ceil(player_stat['playTimeSeconds'] / 60)
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

            # Away
            away_data = game['guestTeam']
            away_players = away_data['players']

            for player in away_players:
                stat = {}
                stat['team'] = info['visitorTeam']['extid']

                stat['player_name'] = f"{player['firstName']} {player['lastName']}"
                stat['player_firstname'] = player['firstName']
                stat['player_lastname'] = player['lastName']
                stat['player_extid'] = f"{player['id']}_{player['slug']}"

                item = {}
                away_player_stats = away_data['gameStatistics']['playersStatistics']

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
                        item['Minutes played'] = ceil(player_stat['playTimeSeconds'] / 60)
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
        main = get_schedule(args['lpar'], args['spar'], 'main')
        pof = get_schedule(args['lpar'], args['spar'], 'pof')

        games.extend(main)
        games.extend(pof)
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'])
    elif args['f'] == 'player':
        return get_player(args['extid'], args['spar'])
    