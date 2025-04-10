from library import *

def get_schedule(lpar):
    games = []
    
    url_dates = f'https://hosted.dcd.shared.geniussports.com/embednf/JBBLT/en/competition/{lpar}/schedule?_ht=1&_mf=1'
    
    resp_dates = requests.get(url_dates)
    dates = re.findall(r"SelectedDates\['([\d-]+)'\] = 1;", resp_dates.json()['html'])
    
    for date in dates:
        url = f'https://hosted.dcd.shared.geniussports.com/embednf/JBBLT/en/competition/{lpar}?poolNumber=-1&matchType=REGULAR&dateFilter={date}&'
        
        resp = requests.get(url)
        html = resp.json()['html']
        soup = BeautifulSoup(html, 'html.parser')
        matches = soup.find_all('div', class_='match-wrap')
        
        for match in matches:
            game = {}
            game['competition'] = lpar
            game['playDate'] = date
            game['round'] = lpar
            game['state'] = match['class'][1]
            game['type'] = 'Regular'
            game['extid'] = match['id'].replace('extfix_', '')
            
            game['homeTeam'] = {
                'extid': slugify(match.find('div', class_='home-team').find('span', class_='team-name-full').text),
                'name': match.find('div', class_='home-team').find('span', class_='team-name-full').text
            }
            game['homeScores'] = {
                'final': 0
            }
            
            game['visitorTeam'] = {
                'extid': slugify(match.find('div', class_='away-team').find('span', class_='team-name-full').text),
                'name': match.find('div', class_='away-team').find('span', class_='team-name-full').text
            }
            game['visitorScores'] = {
                'final': 0
            }
            
            if game['state'] == 'STATUS_COMPLETE':
                game['homeScores'] = {
                    'final': int(match.find('div', class_='home-team').find('div', class_='team-score').text.strip())
                }
                game['visitorScores'] = {
                    'final': int(match.find('div', class_='away-team').find('div', class_='team-score').text.strip())
                }

            game['source'] = unquote(match.find('div', class_='sched-link').find('a')['href'])
            games.append(game)
            
    return games

def get_boxscore(extid, lpar):
    url = f'https://hosted.dcd.shared.geniussports.com/embednf/JBBLT/en/competition/{lpar}/match/{extid}/boxscore?_ht=1&_mf=1'
    resp = requests.get(url)
    html = resp.json()['html']
    soup = BeautifulSoup(html, 'html.parser')
    
    info = {}
    info['extid'] = extid
    info['playDate'] = datetime.strptime(soup.find('div', class_='match-time').span.text, '%b %d, %Y, %I:%M %p').strftime('%Y-%m-%d')
        
    info['source'] = f'https://www.bleague.global/schedule?detail&WHurl=/competition/{lpar}/match/{extid}/boxscore?'
    info['type'] = 'Regular'
    
    info['homeTeam'] = {
        'extid': unquote(soup.find('div', class_='home-wrapper').find('span', class_='name').a['href']).split('/')[-1].replace('?', ''),
        'name': soup.find('div', class_='home-wrapper').find('span', class_='name').text
    }
    
    info['visitorTeam'] = {
        'extid': unquote(soup.find('div', class_='away-wrapper').find('span', class_='name').a['href']).split('/')[-1].replace('?', ''),
        'name': soup.find('div', class_='away-wrapper').find('span', class_='name').text
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
    
    if soup.find('div', class_='vs-label').find('span', class_='notlive').text.strip() != 'vs':
        info['homeScores']['final'] = int(soup.find('div', class_='home-wrapper').find('div', class_='score').text.strip())
        info['visitorScores']['final'] = int(soup.find('div', class_='away-wrapper').find('div', class_='score').text.strip())

        stats = soup.find_all('table', class_='footable')
        
        # home
        players = stats[0].tbody.find_all('tr')

        for player in players:
            cells = player.find_all('td')
            
            stat = {}
            stat['team'] = info['homeTeam']['extid']

            stat['player_name'] = cells[1].text.strip()
            stat['player_firstname'] = ' '.join(stat['player_name'].split(' ')[:-1])
            stat['player_lastname'] = stat['player_name'].split(' ')[-1]
            stat['player_extid'] = slugify(stat['player_name'])

            item = {}
            item['2pts Attempts'] = int(cells[5].text) - int(cells[8].text)
            item['2pts Made'] = int(cells[4].text) - int(cells[7].text)
            item['3pts Attempts'] = int(cells[8].text)
            item['3pts Made'] = int(cells[7].text)
            item['Assists'] = int(cells[16].text)
            item['Block Shots'] = int(cells[19].text)
            item['Defensive rebounds'] = int(cells[14].text)
            item['Offensive rebounds'] = int(cells[13].text)
            item['Total rebounds'] = int(cells[15].text)
            item['FT Attempts'] = int(cells[11].text)
            item['FT Made'] = int(cells[10].text)
            item['Minutes played'] = round(int(cells[2].text.split(':')[0]) + int(cells[2].text.split(':')[1]) / 60)
            item['Personal fouls'] = int(cells[21].text)
            item['Points'] = int(cells[3].text)
            item['Steals'] = int(cells[18].text)
            item['Turnovers'] = int(cells[17].text)

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
        players = stats[1].tbody.find_all('tr')

        for player in players:
            cells = player.find_all('td')
            
            stat = {}
            stat['team'] = info['visitorTeam']['extid']

            stat['player_name'] = cells[1].text.strip()
            stat['player_firstname'] = ' '.join(stat['player_name'].split(' ')[:-1])
            stat['player_lastname'] = stat['player_name'].split(' ')[-1]
            stat['player_extid'] = slugify(stat['player_name'])

            item = {}
            item['2pts Attempts'] = int(cells[5].text) - int(cells[8].text)
            item['2pts Made'] = int(cells[4].text) - int(cells[7].text)
            item['3pts Attempts'] = int(cells[8].text)
            item['3pts Made'] = int(cells[7].text)
            item['Assists'] = int(cells[16].text)
            item['Block Shots'] = int(cells[19].text)
            item['Defensive rebounds'] = int(cells[14].text)
            item['Offensive rebounds'] = int(cells[13].text)
            item['Total rebounds'] = int(cells[15].text)
            item['FT Attempts'] = int(cells[11].text)
            item['FT Made'] = int(cells[10].text)
            item['Minutes played'] = round(int(cells[2].text.split(':')[0]) + int(cells[2].text.split(':')[1]) / 60)
            item['Personal fouls'] = int(cells[21].text)
            item['Points'] = int(cells[3].text)
            item['Steals'] = int(cells[18].text)
            item['Turnovers'] = int(cells[17].text)

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
    return {'extid': extid}

def func_blg(args):
    if args['f'] == 'schedule':
        games = get_schedule(args['lpar'])
        
        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        return get_boxscore(args['extid'], args['lpar'])
    elif args['f'] == 'player':
        return get_player(args['extid'])