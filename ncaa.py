from library import *

def get_schedule(season, seasonDivisionID, sportCode):
    games = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    proxies = {
        'http': 'http://p.webshare.io:9999',
        'https': 'http://p.webshare.io:9999'
    }
    
    while True:
        try:
            response = requests.get(f'https://stats.ncaa.org/contests/livestream_scoreboards?utf8=%E2%9C%93&sport_code={sportCode}&academic_year=&division=&game_date=&commit=Submit', headers=headers, proxies=proxies)

            if response.status_code == 200:            
                break
        except:
            pass

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        sportYearSelector = soup.find('select', id='game_sport_year_ctl_id_select')
        sportYearOptions: List[Tag] = sportYearSelector.find_all('option')
        
        for sportYearOption in sportYearOptions:
            sportYear = sportYearOption.text.strip()
            
            if sportYear == season:
                sportYearCode = sportYearOption['value']
        
        while True:
            try:
                response = requests.get(f'https://stats.ncaa.org/contests/livestream_scoreboards?utf8=%E2%9C%93&game_sport_year_ctl_id={sportYearCode}&conference_id=0&conference_id=0&tournament_id=&division=1&commit=Submit', headers=headers, proxies=proxies)

                if response.status_code == 200:
                    break
            except:
                continue
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            seasonDivisionSelector = soup.find('select', id='season_division_id_select')
            seasonDivisionOptions: List[Tag] = seasonDivisionSelector.find_all('option')
            
            for seasonDivisionOption in seasonDivisionOptions:
                seasonDivision = seasonDivisionOption.text.strip()
                
                if seasonDivision == seasonDivisionID:
                    seasonDivisionCode = seasonDivisionOption['value']

            while True:
                try:
                    response = requests.get(f'https://stats.ncaa.org/season_divisions/{seasonDivisionCode}/livestream_scoreboards?utf8=%E2%9C%93&season_division_id=&game_date=&conference_id=0&tournament_id=&commit=Submit', headers=headers, proxies=proxies)

                    if response.status_code == 200:
                        break
                except:
                    continue

            if response.status_code == 200:
                minDate = datetime.strptime(re.search(r'minDate: \'(.*)\'', response.text).group(1), '%m/%d/%Y')
                maxDate = datetime.strptime(re.search(r'maxDate: \'(.*)\'', response.text).group(1), '%m/%d/%Y')
                daylist = [minDate + timedelta(days=delta) for delta in range((maxDate - minDate).days)]

                def get_info(day: datetime):
                    results = []
                    # sleep(1)
                    while True:
                        try:
                            response = requests.get(f"https://stats.ncaa.org/season_divisions/{seasonDivisionCode}/livestream_scoreboards?utf8=%E2%9C%93&season_division_id=&game_date={day.strftime('%m/%d/%Y')}&conference_id=0&tournament_id=&commit=Submit", headers=headers, proxies=proxies)

                            if response.status_code == 200:
                                break
                        except:
                            continue

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        matches: List[Tag] = soup.find_all('div', class_='card-body')[1:]
                
                        for match in matches:
                            table = match.find('table')
                            rows = table.find_all('tr', recursive=False)
                            
                            game = {}
                            
                            if len(rows) > 4:
                                game['competition'] = rows[1].text.strip()
                            else:
                                game['competition'] = '-'
                                
                            game['playDate'] = datetime.strptime(rows[0].find('div', class_='col-6').text.strip().split(' ')[0], '%m/%d/%Y').strftime('%Y-%m-%d')
                            game['round'] = '-'
                            game['state'] = "Result"
                            
                            if len(rows) > 4:
                                game['homeTeam'] = {
                                    'name': rows[3].find_all('td')[1].text.strip()
                                }
                                
                                game['homeTeam']['name'] = game['homeTeam']['name'].split('(')[0].strip()
                                
                                if game['homeTeam']['name'][0] == '#':
                                    game['homeTeam']['name'] = ' '.join(game['homeTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[3].find_all('td')[1].find('a')
                                
                                if teamObj:
                                    game['homeTeam']['extid'] = teamObj.get('href').split('/')[-1]
                                else:
                                    # game['homeTeam']['extid'] = '-'
                                    continue

                                game['visitorTeam'] = {
                                    'name': rows[2].find_all('td')[1].text.strip()
                                }
                                
                                game['visitorTeam']['name'] = game['visitorTeam']['name'].split('(')[0].strip()
                                
                                if game['visitorTeam']['name'][0] == '#':
                                    game['visitorTeam']['name'] = ' '.join(game['visitorTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[2].find_all('td')[1].find('a')
                                
                                if teamObj:
                                    game['visitorTeam']['extid'] = teamObj.get('href').split('/')[-1]
                                else:
                                    # game['visitorTeam']['extid'] = '-'
                                    continue
                                
                                if game['state'] == "Result":
                                    boxScoreObj = rows[-1].find('a')
                                    
                                    if boxScoreObj:
                                        game['extid'] = boxScoreObj.get('href').split('/')[-2]
                                        game['source'] = f"https://stats.ncaa.org{boxScoreObj.get('href')}"
                                    else:
                                        continue
                                        
                                    game['homeScores'] = {
                                        'final': rows[3].find('td', class_='totalcol').text.strip()
                                    }
                                    game['visitorScores'] = {
                                        'final': rows[2].find('td', class_='totalcol').text.strip()
                                    }
                                else:
                                    continue
                            else:
                                game['homeTeam'] = {
                                    'name': rows[2].find_all('td')[1].text.strip()
                                }
                                
                                game['homeTeam']['name'] = game['homeTeam']['name'].split('(')[0].strip()
                                
                                if game['homeTeam']['name'][0] == '#':
                                    game['homeTeam']['name'] = ' '.join(game['homeTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[2].find_all('td')[1].find('a')
                                
                                if teamObj:
                                    game['homeTeam']['extid'] = teamObj.get('href').split('/')[-1]
                                else:
                                    # game['homeTeam']['extid'] = '-'
                                    continue

                                game['visitorTeam'] = {
                                    'name': rows[1].find_all('td')[1].text.strip()
                                }
                                
                                game['visitorTeam']['name'] = game['visitorTeam']['name'].split('(')[0].strip()
                                
                                if game['visitorTeam']['name'][0] == '#':
                                    game['visitorTeam']['name'] = ' '.join(game['visitorTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[1].find_all('td')[1].find('a')
                                
                                if teamObj:
                                    game['visitorTeam']['extid'] = teamObj.get('href').split('/')[-1]
                                else:
                                    # game['visitorTeam']['extid'] = '-'
                                    continue
                                
                                if game['state'] == "Result":
                                    boxScoreObj = rows[-1].find('a')
                                    
                                    if boxScoreObj:
                                        game['extid'] = boxScoreObj.get('href').split('/')[-2]
                                        game['source'] = f"https://stats.ncaa.org{boxScoreObj.get('href')}"
                                    else:
                                        continue
                                        
                                    try:
                                        game['homeScores'] = {
                                            'final': rows[2].find('td', class_='totalcol').text.strip()
                                        }
                                        game['visitorScores'] = {
                                            'final': rows[1].find('td', class_='totalcol').text.strip()
                                        }
                                    except:
                                        game['state'] = 'Canceled'
                                        continue
                                else:
                                    continue

                            game['type'] = 'Regular Season'
                            results.append(game)
                    
                    return results
                
                pool = ThreadPoolExecutor(max_workers=30)
                futures = [pool.submit(get_info, n) for n in daylist]
                for future in as_completed(futures):
                    if future.result():
                        games.extend(future.result())
            
    return json.dumps(games, indent=4)

def func_ncaa(args, seasonDivisionID):
    if args['f'] == 'schedule':
        season = f"{args['season']}-{str(int(args['season'])+1)[-2:]}"
        sportCode = 'MBB'

        return get_schedule(season, seasonDivisionID, sportCode)
        
    elif args['f'] == 'game':
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        response = requests.get(f'https://stats.ncaa.org/contests/{args["extid"]}/individual_stats', headers=headers)
        
        info = {}

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tables: List[Tag] = soup.find_all('table')

            info['extid'] = args['extid']
            info['playDate'] = datetime.strptime(tables[1].find_all('tr')[3].text.split(' ')[0].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
            info['source'] = f'https://stats.ncaa.org/contests/{args["extid"]}/individual_stats'
            info['type'] = 'Regular Season'
            info['stats'] = []

            homeTeam = tables[-1]
            visitorTeam = tables[-2]

            info['homeTeam'] = {
                'name': tables[0].tr.td.find_next_siblings('td')[5].span.text.strip()
            }
            
            teamLinkObj = tables[0].tr.td.find_next_siblings('td')[5].find('a')
            
            if teamLinkObj:
                info['homeTeam']['extid'] = teamLinkObj.get('href').split('/')[-1]
            else:
                info['homeTeam']['extid'] = '-'
                
            info['homeScores'] = {
                'final': tables[1].find_all('tr')[2].find_all('td')[-1].text
            }

            players = homeTeam.find('thead').find_next_siblings('tr')

            for player in players:
                cells = player.find_all('td')
                
                stat = {}
                stat['team'] = info['homeTeam']['extid']
                stat['player_extid'] = f"{cells[1].text.strip()}_{stat['team']}"
                stat['player_name'] = cells[1].text.strip()
                stat['player_firstname'] = cells[1].text.split(' ')[0].strip()
                stat['player_lastname'] = cells[1].text.split(' ')[1].strip()

                item = {}
                item['3pts Attempts'] = cells[7].text
                item['3pts Made'] = cells[6].text
                item['2pts Attempts'] = int(cells[5].text) - int(cells[7].text)
                item['2pts Made'] = int(cells[4].text) - int(cells[6].text)
                item['Assists'] = cells[14].text
                item['Block Shots'] = cells[17].text
                item['Defensive rebounds'] = cells[12].text
                item['FT Attempts'] = cells[9].text
                item['FT Made'] = cells[8].text
                
                try:
                    item['Minutes played'] = round((datetime.strptime(cells[3].text, '%M:%S').minute * 60 + datetime.strptime(cells[3].text, '%M:%S').second) / 60)
                except:
                    item['Minutes played'] = 0
                    
                item['Offensive rebounds'] = cells[11].text
                item['Personal fouls'] = cells[18].text
                item['Points'] = cells[10].text
                item['Steals'] = cells[16].text
                item['Total rebounds'] = cells[13].text
                item['Turnovers'] = cells[15].text

                stat['items'] = item
                info['stats'].append(stat)

            stat = {}
            stat['team'] = info['homeTeam']['extid']
            stat['player_extid'] = 'team'
            stat['player_firstname'] = ''
            stat['player_lastname'] = '- TEAM -'
            stat['player_name'] = '- TEAM -'
            
            teamCells = homeTeam.find('tfoot').find('tr').find_all('td')
            item = {}
            item['Total rebounds'] = teamCells[13].text
            item['Defensive rebounds'] = teamCells[12].text
            item['Offensive rebounds'] = teamCells[11].text
            item['Steals'] = teamCells[16].text
            item['Turnovers'] = teamCells[15].text

            stat['items'] = item
            info['stats'].append(stat)
            
            info['visitorTeam'] = {
                'name': tables[0].tr.td.find_next_siblings('td')[0].span.text.strip()
            }
            
            teamLinkObj = tables[0].tr.td.find_next_siblings('td')[0].find('a')
            
            if teamLinkObj:
                info['visitorTeam']['extid'] = teamLinkObj.get('href').split('/')[-1]
            else:
                info['visitorTeam']['extid'] = '-'
                
            info['visitorScores'] = {
                'final': tables[1].find_all('tr')[1].find_all('td')[-1].text
            }

            players = visitorTeam.find('thead').find_next_siblings('tr')

            for player in players:
                cells = player.find_all('td')
                
                stat = {}
                stat['team'] = info['visitorTeam']['extid']
                stat['player_extid'] = f"{cells[1].text.strip()}_{stat['team']}"
                stat['player_name'] = cells[1].text.strip()
                stat['player_firstname'] = cells[1].text.split(' ')[0].strip()
                stat['player_lastname'] = cells[1].text.split(' ')[1].strip()

                item = {}
                item['3pts Attempts'] = cells[7].text
                item['3pts Made'] = cells[6].text
                item['2pts Attempts'] = int(cells[5].text) - int(cells[7].text)
                item['2pts Made'] = int(cells[4].text) - int(cells[6].text)
                item['Assists'] = cells[14].text
                item['Block Shots'] = cells[17].text
                item['Defensive rebounds'] = cells[12].text
                item['FT Attempts'] = cells[9].text
                item['FT Made'] = cells[8].text
                
                try:
                    item['Minutes played'] = round((datetime.strptime(cells[3].text, '%M:%S').minute * 60 + datetime.strptime(cells[3].text, '%M:%S').second) / 60)
                except:
                    item['Minutes played'] = 0
                    
                item['Offensive rebounds'] = cells[11].text
                item['Personal fouls'] = cells[18].text
                item['Points'] = cells[10].text
                item['Steals'] = cells[16].text
                item['Total rebounds'] = cells[13].text
                item['Turnovers'] = cells[15].text

                stat['items'] = item
                info['stats'].append(stat)
            
            stat = {}
            stat['team'] = info['visitorTeam']['extid']
            stat['player_extid'] = 'team'
            stat['player_firstname'] = ''
            stat['player_lastname'] = '- TEAM -'
            stat['player_name'] = '- TEAM -'

            teamCells = visitorTeam.find('tfoot').find('tr').find_all('td')
            item = {}
            item['Total rebounds'] = teamCells[13].text
            item['Defensive rebounds'] = teamCells[12].text
            item['Offensive rebounds'] = teamCells[11].text
            item['Steals'] = teamCells[16].text
            item['Turnovers'] = teamCells[15].text

            stat['items'] = item
            info['stats'].append(stat)

            info['homeScores']['QT1'] = int(tables[1].find_all('tr')[2].find_all('td')[1].text)
            info['homeScores']['QT2'] = int(tables[1].find_all('tr')[2].find_all('td')[2].text)
            info['homeScores']['QT3'] = 0
            info['homeScores']['QT4'] = 0
            info['homeScores']['extra'] = int(info['homeScores']['final']) - info['homeScores']['QT1'] - info['homeScores']['QT2']

            info['visitorScores']['QT1'] = int(tables[1].find_all('tr')[1].find_all('td')[1].text)
            info['visitorScores']['QT2'] = int(tables[1].find_all('tr')[1].find_all('td')[2].text)
            info['visitorScores']['QT3'] = 0
            info['visitorScores']['QT4'] = 0
            info['visitorScores']['extra'] = int(info['visitorScores']['final']) - info['visitorScores']['QT1'] - info['visitorScores']['QT2']
                                    
        return info
    elif args['f'] == 'player':
        name, team = args['extid'].split('_')
        
        info = {}
        info['extid'] = args['extid']
        info['source'] = f'https://stats.ncaa.org/teams/{team}/roster'
        info['name'] = name
        info['firstname'] = name.split(' ')[0]
        info['lastname'] = name.split(' ')[1]
        
        response = requests.get(f'https://stats.ncaa.org/teams/{team}/roster', headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            playerTable = soup.find_all('table')[-1]
            playerRows = playerTable.tbody.find_all('tr')
            
            for playerRow in playerRows:
                playerCells = playerRow.find_all('td')
                
                if playerCells[3].text == name:
                    info['nationality'] = playerCells[7].text
                    info['height'] = playerCells[6].text
                    info['position'] = playerCells[5].text

        return info
