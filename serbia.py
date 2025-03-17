from library import *

def func_kls(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        year = f"s{args['season'][-2:]}{str(int(args['season']) + 1)[-2:]}"

        games = []

        urlSchedule = f'https://kss-live.com/{year}/ukkls/kalendar.php'
        urlResult = f'https://kss-live.com/{year}/ukkls/rezultati.php'
        
        respSchedule = requests.get(urlSchedule)
        respResult = requests.get(urlResult)

        soupSchedule = BeautifulSoup(respSchedule.text, 'html.parser')
        soupResult = BeautifulSoup(respResult.text, 'html.parser')

        tblSchedule = soupSchedule.find_all('table')
        tblResult = soupResult.find_all('table')
        extID = 1
        
        for tblIndex in range(len(tblSchedule)):
            rowsSchedule = tblSchedule[tblIndex].find_all('tr')
            rowsResult = tblResult[tblIndex].find_all('tr')

            for rowIndex in range(1, len(rowsSchedule)):
                game = {}
                game['competition'] = 'KLS'
                game['playDate'] = datetime.strptime(rowsSchedule[rowIndex].find_all('td')[-1].text.split(' ')[0], '%d.%m.%Y.').strftime('%Y-%m-%d')
                game['round'] = rowsSchedule[0].td.text.split('.')[0].strip()

                if rowsResult[rowIndex].find('img'):
                    game['state'] = 'result'
                else:
                    game['state'] = 'confirmed'

                game['type'] = 'Regular Season'
                
                game['homeTeam'] = {
                    'extid': parse_qs(urlparse(rowsSchedule[rowIndex].td.find_all('a')[0]['href']).query)['id'][0],
                    'name': rowsSchedule[rowIndex].td.find_all('a')[0].text
                }

                if game['state'] == 'result':
                    game['homeScores'] = {
                        'final': rowsResult[rowIndex].find_all('td')[1].text.split(':')[0]
                    }
                
                game['visitorTeam'] = {
                    'extid': parse_qs(urlparse(rowsSchedule[rowIndex].td.find_all('a')[1]['href']).query)['id'][0],
                    'name': rowsSchedule[rowIndex].td.find_all('a')[1].text
                }

                if game['state'] == 'result':
                    game['visitorScores'] = {
                        'final': rowsResult[rowIndex].find_all('td')[1].text.split(':')[1]
                    }

                game['extid'] = f"{extID}_{game['playDate']}_{game['state']}"
                game['source'] = f'https://kls.rs/utakmica/?id={extID}'
                games.append(game)

                extID += 1

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        extID, playDate, status = request.args.get('extid').split('_')
        args['season'] = request.args.get('season')
        year = f"s{args['season'][-2:]}{str(int(args['season']) + 1)[-2:]}"
        
        response = requests.get(f'https://kss-live.com/{year}/ukkls/box.php?id={extID}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = extID
            info['playDate'] = playDate
            info['source'] = f'https://kls.rs/utakmica/?id={extID}'
            info['type'] = 'Regular Season'
            

            info['homeTeam'] = {
                'extid': parse_qs(urlparse(soup.find('span', id='nthome').a['href']).query)['id'][0],
                'name': soup.find('span', id='nthome').text
            }

            info['visitorTeam'] = {
                'extid': parse_qs(urlparse(soup.find('span', id='ntaway').a['href']).query)['id'][0],
                'name': soup.find('span', id='ntaway').text
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

            if status == 'result':
                info['homeScores']['final'] = soup.find('span', id='rhome').text

                info['homeScores']['QT1'] = int(soup.find('span', id='q1h').text)
                info['homeScores']['QT2'] = int(soup.find('span', id='q2h').text)
                info['homeScores']['QT3'] = int(soup.find('span', id='q3h').text)
                info['homeScores']['QT4'] = int(soup.find('span', id='q4h').text)
                info['homeScores']['extra'] = int(0 if soup.find('span', id='q5h').text == '' else soup.find('span', id='q5h').text == '')
                    
                info['visitorScores']['final'] = int(soup.find('span', id='raway').text)

                info['visitorScores']['QT1'] = int(soup.find('span', id='q1a').text)
                info['visitorScores']['QT2'] = int(soup.find('span', id='q2a').text)
                info['visitorScores']['QT3'] = int(soup.find('span', id='q3a').text)
                info['visitorScores']['QT4'] = int(soup.find('span', id='q4a').text)
                info['visitorScores']['extra'] = int(0 if soup.find('span', id='q5a').text == '' else soup.find('span', id='q5a').text == '')

                # home
                players = soup.find('span', id='shome').find('tbody').find_all('tr')

                for player in players:
                    stat = {}
                    stat['team'] = info['homeTeam']['extid']

                    if 'okk' in slugify(info['homeTeam']['name']):
                        stat['player_extid'] = f"{player.find_all('td')[0].text.split(' ')[0]}_{slugify(info['homeTeam']['name'])}"
                    else:
                        stat['player_extid'] = f"{player.find_all('td')[0].text.split(' ')[0]}_kk-{slugify(info['homeTeam']['name'])}"

                    playerName = re.search('\s[\s\w]+$', player.find_all('td')[0].text).group(0).strip()
                    stat['player_firstname'] = playerName.split(' ')[-1]
                    stat['player_lastname'] = ' '.join(reversed(playerName.split(' ')[:-1]))
                    stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"

                    item = {}
                    item['2pts Attempts'] = player.find_all('td')[5].text.split('/')[1]
                    item['2pts Made'] = player.find_all('td')[5].text.split('/')[0]
                    item['3pts Attempts'] = player.find_all('td')[7].text.split('/')[1]
                    item['3pts Made'] = player.find_all('td')[7].text.split('/')[0]
                    item['Assists'] = player.find_all('td')[13].text
                    item['Block Shots'] = player.find_all('td')[14].text.split('/')[0]
                    item['Defensive rebounds'] = player.find_all('td')[11].text.split('/')[1]
                    item['FT Attempts'] = player.find_all('td')[3].text.split('/')[1]
                    item['FT Made'] = player.find_all('td')[3].text.split('/')[0]
                    item['Minutes played'] = player.find_all('td')[-1].text
                    item['Offensive rebounds'] = player.find_all('td')[11].text.split('/')[0]
                    item['Personal fouls'] = player.find_all('td')[15].text.split('/')[0]
                    item['Points'] = player.find_all('td')[2].text
                    item['Steals'] = player.find_all('td')[12].text.split('/')[0]
                    item['Total rebounds'] = int(item['Defensive rebounds']) + int(item['Offensive rebounds'])
                    item['Turnovers'] = player.find_all('td')[12].text.split('/')[1]

                    stat['items'] = item
                    info['stats'].append(stat)

                stat = {}
                stat['team'] = info['homeTeam']['extid']
                stat['player_extid'] = 'team'
                stat['player_firstname'] = ''
                stat['player_lastname'] = '- TEAM -'
                stat['player_name'] = '- TEAM -'

                item = {}
                item['Defensive rebounds'] = soup.find('span', id='shome').find('tfoot').find_all('td')[11].text.split('/')[1]
                item['Offensive rebounds'] = soup.find('span', id='shome').find('tfoot').find_all('td')[11].text.split('/')[0]
                item['Total rebounds'] = int(item['Defensive rebounds']) + int(item['Offensive rebounds'])
                item['Turnovers'] = soup.find('span', id='shome').find('tfoot').find_all('td')[12].text.split('/')[1]

                stat['items'] = item
                info['stats'].append(stat)

                # away
                players = soup.find('span', id='saway').find('tbody').find_all('tr')

                for player in players:
                    stat = {}
                    stat['team'] = info['visitorTeam']['extid']

                    if 'okk' in slugify(info['visitorTeam']['name']):
                        stat['player_extid'] = f"{player.find_all('td')[0].text.split(' ')[0]}_{slugify(info['visitorTeam']['name'])}"
                    else:
                        stat['player_extid'] = f"{player.find_all('td')[0].text.split(' ')[0]}_kk-{slugify(info['visitorTeam']['name'])}"

                    playerName = re.search('\s[\s\w]+$', player.find_all('td')[0].text).group(0).strip()
                    stat['player_firstname'] = playerName.split(' ')[-1]
                    stat['player_lastname'] = ' '.join(reversed(playerName.split(' ')[:-1]))
                    stat['player_name'] = f"{stat['player_firstname']} {stat['player_lastname']}"

                    item = {}
                    item['2pts Attempts'] = player.find_all('td')[5].text.split('/')[1]
                    item['2pts Made'] = player.find_all('td')[5].text.split('/')[0]
                    item['3pts Attempts'] = player.find_all('td')[7].text.split('/')[1]
                    item['3pts Made'] = player.find_all('td')[7].text.split('/')[0]
                    item['Assists'] = player.find_all('td')[13].text
                    item['Block Shots'] = player.find_all('td')[14].text.split('/')[0]
                    item['Defensive rebounds'] = player.find_all('td')[11].text.split('/')[1]
                    item['FT Attempts'] = player.find_all('td')[3].text.split('/')[1]
                    item['FT Made'] = player.find_all('td')[3].text.split('/')[0]
                    item['Minutes played'] = player.find_all('td')[-1].text
                    item['Offensive rebounds'] = player.find_all('td')[11].text.split('/')[0]
                    item['Personal fouls'] = player.find_all('td')[15].text.split('/')[0]
                    item['Points'] = player.find_all('td')[2].text
                    item['Steals'] = player.find_all('td')[12].text.split('/')[0]
                    item['Total rebounds'] = int(item['Defensive rebounds']) + int(item['Offensive rebounds'])
                    item['Turnovers'] = player.find_all('td')[12].text.split('/')[1]

                    stat['items'] = item
                    info['stats'].append(stat)

                stat = {}
                stat['team'] = info['visitorTeam']['extid']
                stat['player_extid'] = 'team'
                stat['player_firstname'] = ''
                stat['player_lastname'] = '- TEAM -'
                stat['player_name'] = '- TEAM -'

                item = {}
                item['Defensive rebounds'] = soup.find('span', id='saway').find('tfoot').find_all('td')[11].text.split('/')[1]
                item['Offensive rebounds'] = soup.find('span', id='saway').find('tfoot').find_all('td')[11].text.split('/')[0]
                item['Total rebounds'] = int(item['Defensive rebounds']) + int(item['Offensive rebounds'])
                item['Turnovers'] = soup.find('span', id='saway').find('tfoot').find_all('td')[12].text.split('/')[1]

                stat['items'] = item
                info['stats'].append(stat)

            return info
    elif args['f'] == 'player':
        number, team = request.args.get('extid').split('_')

        response = requests.get(f'https://kls.rs/{team}/')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            persons = soup.find_all('div', class_='fusion_builder_column_1_4')[1:]

            for person in persons:
                rowsInfo = person.find('div', class_='fusion-text').text.split('\n')
                isFound = False
                for row in rowsInfo:
                    if 'Broj:' in row:
                        if row.split(':')[-1].strip() == number:
                            isFound = True
                            break

                if isFound:
                    info = {}
                    name = person.find('div', class_='fusion-title').text.strip().split('\n')[0].strip()
                    info['firstname'] = name.split(' ')[-1]
                    info['lastname'] = ' '.join(reversed(name.split(' ')[:-1]))
                    info['name'] = f"{info['firstname']} {info['lastname']}"
                    info['extid'] = f"{number}_{team}"
                    info['source'] = f"https://kls.rs/{team}"
                    info['shirtNumber'] = int(number)
                    info['team'] = soup.find('h1', class_='entry-title').text
                    
                    for row in rowsInfo:
                        if 'Godište:' in row:
                            yearOfBirth = re.search('\d+', row.split(':')[1]).group(0)

                        if 'Visina:' in row:
                            info['height'] = int(re.search('\d+', row.split(':')[1]).group(0))

                        if 'Pozicija' in row:
                            info['position'] = row.split(':')[1].strip()

                    info['dateOfBirth'] = f'{yearOfBirth}-01-01'
                    info['age'] = datetime.now().year - int(yearOfBirth)

                    return info

                        
