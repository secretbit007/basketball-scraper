from library import *

def func_leboro(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')

        response = requests.get(f'https://baloncestoenvivo.feb.es/calendario/ligaleboro/1/{args["season"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            tables = soup.find_all('div', class_='columna')
            games = []

            for table in tables:
                matches = table.find_all('tr')[1:]

                for match in matches:
                    game = {}
                    game['competition'] = 'LIGA LEB ORO'
                    game['playDate'] = datetime.strptime(table.h1.text.strip().split(' ')[2], '%d/%m/%Y').strftime('%Y-%m-%d')
                    game['round'] = table.h1.text.strip().split(' ')[1]

                    if match.find('td', class_='resultado'):
                        game['state'] = 'result'
                    else:
                        game['state'] = 'confirmed'

                    game['type'] = 'Single Regular League'
                    game['homeTeam'] = {
                        'extid': parse_qs(urlparse(match.find('td', class_='equipo local').a['href']).query)['i'][0],
                        'name': match.find('td', class_='equipo local').text.strip()
                    }
                    if game['state'] == 'result':
                        game['homeScores'] = {
                            'final': match.find('td', class_='resultado').text.strip().split('-')[0]
                        }

                    game['visitorTeam'] = {
                        'extid': parse_qs(urlparse(match.find('td', class_='equipo visitante').a['href']).query)['i'][0],
                        'name': match.find('td', class_='equipo visitante').text.strip()
                    }
                    if game['state'] == 'result':
                        game['visitorScores'] = {
                            'final': match.find('td', class_='resultado').text.strip().split('-')[1]
                        }

                    if game['state'] == 'result':
                        game['extid'] = parse_qs(urlparse(match.find('td', class_='resultado').a['href']).query)['p'][0]
                        game['source'] = match.find('td', class_='resultado').a['href']
                    else:
                        game['extid'] = parse_qs(urlparse(match.find('td', class_='fecha').a['href']).query)['p'][0]
                        game['source'] = match.find('td', class_='fecha').a['href']

                    games.append(game)
            return json.dumps(games, indent=4)
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')

        response = requests.get(f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            headers = {
                'Authorization': f"Bearer {soup.find('input', id='_ctl0_token')['value']}",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
            }
        else:
            return {'error': 'Something went wrong!'}
        
        response = requests.get(f'https://intrafeb.feb.es/LiveStats.API/api/v1/BoxScore/{args["extid"]}', headers=headers)

        if response.status_code == 200:
            data = response.json()

            info = {}
            info['extid'] = args['extid']
            info['playDate'] = datetime.strptime(data['HEADER']['starttime'].split(' ')[0], '%d-%m-%Y').strftime('%Y-%m-%d')
            info['source'] = f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}'
            info['type'] = 'Single Regular League'
            info['homeTeam'] = {
                'extid': data['HEADER']['TEAM'][0]['id'],
                'name': data['HEADER']['TEAM'][0]['name']
            }
            info['homeScores'] = {
                'QT1': data['HEADER']['QUARTERS']['QUARTER'][0]['scoreA'],
                'QT2': data['HEADER']['QUARTERS']['QUARTER'][1]['scoreA'],
                'QT3': data['HEADER']['QUARTERS']['QUARTER'][2]['scoreA'],
                'QT4': data['HEADER']['QUARTERS']['QUARTER'][3]['scoreA'],
                'extra': 0,
                'final': data['HEADER']['TEAM'][0]['pts']
            }

            for quarter in data['HEADER']['QUARTERS']['QUARTER'][4:]:
                info['homeScores']['extra'] += int(quarter['scoreA'])
            
            info['visitorTeam'] = {
                'extid': data['HEADER']['TEAM'][1]['id'],
                'name': data['HEADER']['TEAM'][1]['name']
            }
            info['visitorScores'] = {
                'QT1': data['HEADER']['QUARTERS']['QUARTER'][0]['scoreB'],
                'QT2': data['HEADER']['QUARTERS']['QUARTER'][1]['scoreB'],
                'QT3': data['HEADER']['QUARTERS']['QUARTER'][2]['scoreB'],
                'QT4': data['HEADER']['QUARTERS']['QUARTER'][3]['scoreB'],
                'extra': 0,
                'final': data['HEADER']['TEAM'][1]['pts']
            }

            for quarter in data['HEADER']['QUARTERS']['QUARTER'][4:]:
                info['visitorScores']['extra'] += int(quarter['scoreB'])

            info['stats'] = []

            for team in data['BOXSCORE']['TEAM']:
                for player in team['PLAYER']:
                    stat = {}
                    stat['team'] = team['id']
                    stat['player_name'] = player['name']
                    stat['player_firstname'] = player['name'].split('.')[0].strip()
                    stat['player_lastname'] = f"{player['name'].split('.')[1].strip()}."
                    stat['player_extid'] = f"{player['id']}_{team['id']}"

                    item = {}
                    item['2pts Attempts'] = player['p2a']
                    item['2pts Made'] = player['p2m']
                    item['3pts Attempts'] = player['p3a']
                    item['3pts Made'] = player['p3m']
                    item['Assists'] = player['assist']
                    item['Block Shots'] = player['bs']
                    item['Defensive rebounds'] = player['rd']
                    item['FT Attempts'] = player['p1a']
                    item['FT Made'] = player['p1m']
                    item['Minutes played'] = round(int(player['min'])/60)
                    item['Offensive rebounds'] = player['ro']
                    item['Personal fouls'] = player['pf']
                    item['Points'] = player['pts']
                    item['Steals'] = player['st']
                    item['Total rebounds'] = player['rt']
                    item['Turnovers'] = player['to']

                    stat['items'] = item
                    info['stats'].append(stat)

                # stat = {}
                # stat['team'] = team['id']
                # stat['player_extid'] = 'team'
                # stat['player_firstname'] = ''
                # stat['player_lastname'] = '- TEAM -'
                # stat['player_name'] = '- TEAM -'

                # item = {}
                # item['2pts Attempts'] = team['TOTAL']['p2a']
                # item['2pts Made'] = team['TOTAL']['p2m']
                # item['3pts Attempts'] = team['TOTAL']['p3a']
                # item['3pts Made'] = team['TOTAL']['p3m']
                # item['Assists'] = team['TOTAL']['assist']
                # item['Block Shots'] = team['TOTAL']['bs']
                # item['Defensive rebounds'] = team['TOTAL']['rd']
                # item['FT Attempts'] = team['TOTAL']['p1a']
                # item['FT Made'] = team['TOTAL']['p1m']
                # item['Minutes played'] = round(int(team['TOTAL']['min'])/60)
                # item['Offensive rebounds'] = team['TOTAL']['ro']
                # item['Personal fouls'] = team['TOTAL']['pf']
                # item['Points'] = team['TOTAL']['pts']
                # item['Steals'] = team['TOTAL']['st']
                # item['Total rebounds'] = team['TOTAL']['rt']
                # item['Turnovers'] = team['TOTAL']['to']

                # stat['items'] = item
                # info['stats'].append(stat)
            return info
        elif response.status_code == 404:
            response = requests.get(f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}')

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                info = {}
                info['extid'] = args['extid']
                info['playDate'] = datetime.strptime(soup.find('div', class_='fecha').find('span', class_='txt').text.strip().split(' ')[0], '%d/%m/%Y').strftime('%Y-%m-%d')
                info['type'] = 'Single Regular League'
                info['source'] = f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}'
                info['homeTeam'] = {
                    'extid': parse_qs(urlparse(soup.find('div', class_='columna equipo local').find('a')['href']).query)['i'][0],
                    'name': soup.find('div', class_='columna equipo local').find('a').text.strip()
                }
                info['homeScores'] = {
                    'QT1': 0,
                    'QT2': 0,
                    'QT3': 0,
                    'QT4': 0,
                    'extra': 0,
                    'final': 0
                }
                info['visitorTeam'] = {
                    'extid': parse_qs(urlparse(soup.find('div', class_='columna equipo visitante').find('a')['href']).query)['i'][0],
                    'name': soup.find('div', class_='columna equipo visitante').find('a').text.strip()
                }
                info['visitorScores'] = {
                    'QT1': 0,
                    'QT2': 0,
                    'QT3': 0,
                    'QT4': 0,
                    'extra': 0,
                    'final': 0
                }

                return info
            return {'error': 'Something went wrong!'}
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        player_id, team_id = request.args.get('extid').split('_')

        response = requests.get(f'https://baloncestoenvivo.feb.es/jugador/{team_id}/{player_id}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = player_id
            info['dateOfBirth'] = datetime.strptime(soup.find_all('div', class_='nodo')[5].find('span', class_='string').text.strip().split(' ')[0].strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
            info['height'] = soup.find_all('div', class_='nodo')[3].find('span', class_='string').text.strip().replace('cm', '').strip()
            info['nationality'] = soup.find_all('div', class_='nodo')[6].find('span', class_='string').text.strip()
            info['position'] = soup.find_all('div', class_='nodo')[2].find('span', class_='string').text.strip()
            info['weight'] = soup.find_all('div', class_='nodo')[4].find('span', class_='string').text.strip().replace('Kg', '').strip()
            info['team'] = soup.find('div', class_='equipo').text.strip()

            try:
                info['shirtNumber'] = soup.find('div', class_='dorsal').text.strip()
            except AttributeError:
                info['shirtNumber'] = '0'

            info['firstname'] = soup.find('div', class_='nombre').text.split(',')[1].strip()
            info['lastname'] = soup.find('div', class_='nombre').text.split(',')[0].strip()
            info['name'] = soup.find('div', class_='nombre').text.strip()

            return info
        return {'error': 'Something went wrong!'}

def func_lebplata(args):
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')

        response = requests.get(f'https://baloncestoenvivo.feb.es/calendario/ligalebplata/2/{args["season"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            dropdown = soup.find('select', id='_ctl0_MainContentPlaceHolderMaster_gruposDropDownList')
            groups = dropdown.find_all('option')
            
            games = []

            for group in groups:
                if group.text.strip().lower() == 'liga regular "este"' or group.text.strip().lower() == 'liga regular "oeste"':
                    if not group.has_attr('selected'):
                        payload = {}
                        
                        inputs = soup.find_all('input')

                        for input in inputs:
                            payload[input['id']] = input['value']

                        payload['__EVENTTARGET'] = dropdown['name'].replace(':', '$')
                        payload['_ctl0:MainContentPlaceHolderMaster:temporadasDropDownList'] = args['season']
                        payload['_ctl0:MainContentPlaceHolderMaster:gruposDropDownList'] = group['value']

                        response = requests.post(response.url, data=payload)

                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')

                            tables = soup.find_all('div', class_='columna')

                            for table in tables:
                                matches = table.find_all('tr')[1:]

                                for match in matches:
                                    game = {}
                                    game['competition'] = 'LIGA LEB PLATA'
                                    game['playDate'] = datetime.strptime(table.h1.text.strip().split(' ')[2], '%d/%m/%Y').strftime('%Y-%m-%d')
                                    game['round'] = table.h1.text.strip().split(' ')[1]

                                    if match.find('td', class_='resultado'):
                                        game['state'] = 'result'
                                    else:
                                        game['state'] = 'confirmed'

                                    game['type'] = group.text.strip()
                                    game['homeTeam'] = {
                                        'extid': parse_qs(urlparse(match.find('td', class_='equipo local').a['href']).query)['i'][0],
                                        'name': match.find('td', class_='equipo local').text.strip()
                                    }
                                    if game['state'] == 'result':
                                        game['homeScores'] = {
                                            'final': match.find('td', class_='resultado').text.strip().split('-')[0]
                                        }

                                    game['visitorTeam'] = {
                                        'extid': parse_qs(urlparse(match.find('td', class_='equipo visitante').a['href']).query)['i'][0],
                                        'name': match.find('td', class_='equipo visitante').text.strip()
                                    }
                                    if game['state'] == 'result':
                                        game['visitorScores'] = {
                                            'final': match.find('td', class_='resultado').text.strip().split('-')[1]
                                        }

                                    if game['state'] == 'result':
                                        game['extid'] = parse_qs(urlparse(match.find('td', class_='resultado').a['href']).query)['p'][0]
                                        game['source'] = match.find('td', class_='resultado').a['href']
                                    else:
                                        game['extid'] = parse_qs(urlparse(match.find('td', class_='fecha').a['href']).query)['p'][0]
                                        game['source'] = match.find('td', class_='fecha').a['href']

                                    games.append(game)
                    else:
                        tables = soup.find_all('div', class_='columna')

                        for table in tables:
                            matches = table.find_all('tr')[1:]

                            for match in matches:
                                game = {}
                                game['competition'] = 'LIGA LEB PLATA'
                                game['playDate'] = datetime.strptime(table.h1.text.strip().split(' ')[2], '%d/%m/%Y').strftime('%Y-%m-%d')
                                game['round'] = table.h1.text.strip().split(' ')[1]

                                if match.find('td', class_='resultado'):
                                    game['state'] = 'result'
                                else:
                                    game['state'] = 'confirmed'

                                game['type'] = group.text.strip()
                                game['homeTeam'] = {
                                    'extid': parse_qs(urlparse(match.find('td', class_='equipo local').a['href']).query)['i'][0],
                                    'name': match.find('td', class_='equipo local').text.strip()
                                }
                                if game['state'] == 'result':
                                    game['homeScores'] = {
                                        'final': match.find('td', class_='resultado').text.strip().split('-')[0]
                                    }

                                game['visitorTeam'] = {
                                    'extid': parse_qs(urlparse(match.find('td', class_='equipo visitante').a['href']).query)['i'][0],
                                    'name': match.find('td', class_='equipo visitante').text.strip()
                                }
                                if game['state'] == 'result':
                                    game['visitorScores'] = {
                                        'final': match.find('td', class_='resultado').text.strip().split('-')[1]
                                    }

                                if game['state'] == 'result':
                                    game['extid'] = parse_qs(urlparse(match.find('td', class_='resultado').a['href']).query)['p'][0]
                                    game['source'] = match.find('td', class_='resultado').a['href']
                                else:
                                    game['extid'] = parse_qs(urlparse(match.find('td', class_='fecha').a['href']).query)['p'][0]
                                    game['source'] = match.find('td', class_='fecha').a['href']

                                games.append(game)
            return json.dumps(games, indent=4)
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'game':
        args['extid'] = request.args.get('extid')
        
        response = requests.get(f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            headers = {
                'Authorization': f"Bearer {soup.find('input', id='_ctl0_token')['value']}",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
            }
        else:
            return {'error': 'Something went wrong!'}
        
        response = requests.get(f'https://intrafeb.feb.es/LiveStats.API/api/v1/BoxScore/{args["extid"]}', headers=headers)

        if response.status_code == 200:
            data = response.json()

            info = {}
            info['extid'] = args['extid']
            info['playDate'] = datetime.strptime(data['HEADER']['starttime'].split(' ')[0], '%d-%m-%Y').strftime('%Y-%m-%d')
            info['source'] = f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}'
            info['type'] = 'Single Regular League'
            info['homeTeam'] = {
                'extid': data['HEADER']['TEAM'][0]['id'],
                'name': data['HEADER']['TEAM'][0]['name']
            }
            info['homeScores'] = {
                'QT1': data['HEADER']['QUARTERS']['QUARTER'][0]['scoreA'],
                'QT2': data['HEADER']['QUARTERS']['QUARTER'][1]['scoreA'],
                'QT3': data['HEADER']['QUARTERS']['QUARTER'][2]['scoreA'],
                'QT4': data['HEADER']['QUARTERS']['QUARTER'][3]['scoreA'],
                'extra': 0,
                'final': data['HEADER']['TEAM'][0]['pts']
            }

            for quarter in data['HEADER']['QUARTERS']['QUARTER'][4:]:
                info['homeScores']['extra'] += int(quarter['scoreA'])
            
            info['visitorTeam'] = {
                'extid': data['HEADER']['TEAM'][1]['id'],
                'name': data['HEADER']['TEAM'][1]['name']
            }
            info['visitorScores'] = {
                'QT1': data['HEADER']['QUARTERS']['QUARTER'][0]['scoreB'],
                'QT2': data['HEADER']['QUARTERS']['QUARTER'][1]['scoreB'],
                'QT3': data['HEADER']['QUARTERS']['QUARTER'][2]['scoreB'],
                'QT4': data['HEADER']['QUARTERS']['QUARTER'][3]['scoreB'],
                'extra': 0,
                'final': data['HEADER']['TEAM'][1]['pts']
            }

            for quarter in data['HEADER']['QUARTERS']['QUARTER'][4:]:
                info['visitorScores']['extra'] += int(quarter['scoreB'])

            info['stats'] = []

            for team in data['BOXSCORE']['TEAM']:
                for player in team['PLAYER']:
                    stat = {}
                    stat['team'] = team['id']
                    stat['player_name'] = player['name']
                    stat['player_firstname'] = player['name'].split('.')[0].strip()
                    stat['player_lastname'] = f"{player['name'].split('.')[1].strip()}."
                    stat['player_extid'] = f"{player['id']}_{team['id']}"

                    item = {}
                    item['2pts Attempts'] = player['p2a']
                    item['2pts Made'] = player['p2m']
                    item['3pts Attempts'] = player['p3a']
                    item['3pts Made'] = player['p3m']
                    item['Assists'] = player['assist']
                    item['Block Shots'] = player['bs']
                    item['Defensive rebounds'] = player['rd']
                    item['FT Attempts'] = player['p1a']
                    item['FT Made'] = player['p1m']
                    item['Minutes played'] = round(int(player['min'])/60)
                    item['Offensive rebounds'] = player['ro']
                    item['Personal fouls'] = player['pf']
                    item['Points'] = player['pts']
                    item['Steals'] = player['st']
                    item['Total rebounds'] = player['rt']
                    item['Turnovers'] = player['to']

                    stat['items'] = item
                    info['stats'].append(stat)

                # stat = {}
                # stat['team'] = team['id']
                # stat['player_extid'] = 'team'
                # stat['player_firstname'] = ''
                # stat['player_lastname'] = '- TEAM -'
                # stat['player_name'] = '- TEAM -'

                # item = {}
                # item['2pts Attempts'] = team['TOTAL']['p2a']
                # item['2pts Made'] = team['TOTAL']['p2m']
                # item['3pts Attempts'] = team['TOTAL']['p3a']
                # item['3pts Made'] = team['TOTAL']['p3m']
                # item['Assists'] = team['TOTAL']['assist']
                # item['Block Shots'] = team['TOTAL']['bs']
                # item['Defensive rebounds'] = team['TOTAL']['rd']
                # item['FT Attempts'] = team['TOTAL']['p1a']
                # item['FT Made'] = team['TOTAL']['p1m']
                # item['Minutes played'] = round(int(team['TOTAL']['min'])/60)
                # item['Offensive rebounds'] = team['TOTAL']['ro']
                # item['Personal fouls'] = team['TOTAL']['pf']
                # item['Points'] = team['TOTAL']['pts']
                # item['Steals'] = team['TOTAL']['st']
                # item['Total rebounds'] = team['TOTAL']['rt']
                # item['Turnovers'] = team['TOTAL']['to']

                # stat['items'] = item
                # info['stats'].append(stat)
            return info
        elif response.status_code == 404:
            response = requests.get(f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}')

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                info = {}
                info['extid'] = args['extid']
                info['playDate'] = datetime.strptime(soup.find('div', class_='fecha').find('span', class_='txt').text.strip().split(' ')[0], '%d/%m/%Y').strftime('%Y-%m-%d')
                info['type'] = 'Single Regular League'
                info['source'] = f'https://baloncestoenvivo.feb.es/partido/{args["extid"]}'
                info['homeTeam'] = {
                    'extid': parse_qs(urlparse(soup.find('div', class_='columna equipo local').find('a')['href']).query)['i'][0],
                    'name': soup.find('div', class_='columna equipo local').find('a').text.strip()
                }
                info['homeScores'] = {
                    'QT1': 0,
                    'QT2': 0,
                    'QT3': 0,
                    'QT4': 0,
                    'extra': 0,
                    'final': 0
                }
                info['visitorTeam'] = {
                    'extid': parse_qs(urlparse(soup.find('div', class_='columna equipo visitante').find('a')['href']).query)['i'][0],
                    'name': soup.find('div', class_='columna equipo visitante').find('a').text.strip()
                }
                info['visitorScores'] = {
                    'QT1': 0,
                    'QT2': 0,
                    'QT3': 0,
                    'QT4': 0,
                    'extra': 0,
                    'final': 0
                }

                return info
            return {'error': 'Something went wrong!'}
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        player_id, team_id = request.args.get('extid').split('_')

        response = requests.get(f'https://baloncestoenvivo.feb.es/jugador/{team_id}/{player_id}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = player_id
            info['dateOfBirth'] = datetime.strptime(soup.find_all('div', class_='nodo')[5].find('span', class_='string').text.strip().split(' ')[0].strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
            info['height'] = soup.find_all('div', class_='nodo')[3].find('span', class_='string').text.strip().replace('cm', '').strip()
            info['nationality'] = soup.find_all('div', class_='nodo')[6].find('span', class_='string').text.strip()
            info['position'] = soup.find_all('div', class_='nodo')[2].find('span', class_='string').text.strip()
            info['weight'] = soup.find_all('div', class_='nodo')[4].find('span', class_='string').text.strip().replace('Kg', '').strip()
            info['team'] = soup.find('div', class_='equipo').text.strip()

            try:
                info['shirtNumber'] = soup.find('div', class_='dorsal').text.strip()
            except AttributeError:
                info['shirtNumber'] = '0'

            info['firstname'] = soup.find('div', class_='nombre').text.split(',')[1].strip()
            info['lastname'] = soup.find('div', class_='nombre').text.split(',')[0].strip()
            info['name'] = soup.find('div', class_='nombre').text.strip()

            return info
        return {'error': 'Something went wrong!'}
