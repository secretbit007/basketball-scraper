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
            elif match_type == 'mc':
                game['type'] = "Men's Cup"
            elif match_type == 'msc':
                game['type'] = "Men's Super Cup"

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

        if game_type == 'mc':
            info['type'] = "Men's Cup"
        elif game_type == 'main':
            info['type'] = 'Main Round'
        elif game_type == 'msc':
            info['type'] = "Men's Super Cup"
        elif game_type == 'pof':
            info['type'] == "Play-off"

        match_time = main.find('span', class_='text-white/80').text
        info['playDate'] = datetime.strptime(match_time, '%d.%m.%Y / %H:%M').strftime('%Y-%m-%d')

        container = main.find('div', class_='container')
        teams = list(list(container.children)[0].children)

        # Home
        # home_elem = teams[0]
        # home_name = home_elem.find('h2').text

        # info['homeTeam'] = {
        #     'name': home_name
        # }

        # print(info)

        return info

def func_plk(args):
    if args['f'] == 'schedule':
        games = []
        main = get_schedule(args['lpar'], args['spar'], 'main')
        pof = get_schedule(args['lpar'], args['spar'], 'pof')
        mc = get_schedule(args['lpar'], args['spar'], 'mc')
        msc = get_schedule(args['lpar'], args['spar'], 'msc')

        games.extend(main)
        games.extend(pof)
        games.extend(mc)
        games.extend(msc)
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'], args['spar'])
    