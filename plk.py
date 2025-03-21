from library import *

def get_schedule(lpar, spar, match_type):
    games = []
    
    if match_type == 'Main Round':
        url = f'https://plk.pl/archiwum/{spar}/terminarz'
    elif match_type == 'Play-off':
        url = f'https://plk.pl/archiwum/{spar}/terminarz/play-off'
    elif match_type == "Men's Cup":
        url = f'https://plk.pl/archiwum/{spar}/terminarz/puchar-polski-mezczyzn'
    elif match_type == "Men's Super Cup":
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
            home_extid = home_links[0].get('href').split('/')[-2]

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
            away_extid = away_links[0].get('href').split('/')[-2]

            game['visitorTeam'] = {
                'extid': away_extid,
                'name': away_name
            }
            game['visitorScores'] = {
                'final': away_score
            }

            game['state'] = 'Finished'
            game['competition'] = lpar
            game['type'] = match_type

            game_url = list(match_card.children)[-1].get('href')
            game['extid'] = game_url.split('/')[-2] + '_' + game_url.split('/')[-1]
            game['source'] = 'https://plk.pl' + game_url
            
    return games

def get_boxscore(extid):
    game_extid = extid.split('_')[0]
    game_slug = extid.split('_')[1]

    url = f'https://plk.pl/mecz/{game_extid}/{game_slug}/statystyki'
    resp = requests.get(url)
