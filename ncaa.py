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
                daylist = [minDate + timedelta(days=delta) for delta in range((maxDate - minDate).days + 1)]

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
                                
                                teamObj = rows[3].find_all('td')[0]
                                
                                if teamObj:
                                    try:
                                        game['homeTeam']['extid'] = teamObj.find('img').get('src').split('/')[-1].split('.')[0]
                                    except:
                                        continue
                                else:
                                    # game['homeTeam']['extid'] = '-'
                                    continue

                                game['visitorTeam'] = {
                                    'name': rows[2].find_all('td')[1].text.strip()
                                }
                                
                                game['visitorTeam']['name'] = game['visitorTeam']['name'].split('(')[0].strip()
                                
                                if game['visitorTeam']['name'][0] == '#':
                                    game['visitorTeam']['name'] = ' '.join(game['visitorTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[2].find_all('td')[0]
                                
                                if teamObj:
                                    try:
                                        game['visitorTeam']['extid'] = teamObj.find('img').get('src').split('/')[-1].split('.')[0]
                                    except:
                                        continue
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
                                            'final': rows[3].find('td', class_='totalcol').text.strip()
                                        }
                                        game['visitorScores'] = {
                                            'final': rows[2].find('td', class_='totalcol').text.strip()
                                        }
                                    except:
                                        game['state'] = 'Canceled'
                                        continue
                                else:
                                    continue
                            else:
                                game['homeTeam'] = {
                                    'name': rows[2].find_all('td')[1].text.strip()
                                }
                                
                                game['homeTeam']['name'] = game['homeTeam']['name'].split('(')[0].strip()
                                
                                if game['homeTeam']['name'][0] == '#':
                                    game['homeTeam']['name'] = ' '.join(game['homeTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[2].find_all('td')[0]
                                
                                if teamObj:
                                    try:
                                        game['homeTeam']['extid'] = teamObj.find('img').get('src').split('/')[-1].split('.')[0]
                                    except:
                                        continue
                                else:
                                    # game['homeTeam']['extid'] = '-'
                                    continue

                                game['visitorTeam'] = {
                                    'name': rows[1].find_all('td')[1].text.strip()
                                }
                                
                                game['visitorTeam']['name'] = game['visitorTeam']['name'].split('(')[0].strip()
                                
                                if game['visitorTeam']['name'][0] == '#':
                                    game['visitorTeam']['name'] = ' '.join(game['visitorTeam']['name'].split(' ')[1:])
                                
                                teamObj = rows[1].find_all('td')[0]
                                
                                if teamObj:
                                    try:
                                        game['visitorTeam']['extid'] = teamObj.find('img').get('src').split('/')[-1].split('.')[0]
                                    except:
                                        continue
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

def get_column_index(table: Tag, column: str) -> int | None:
    thead = table.find('thead')
    ths = thead.find_all('th')

    for th in ths:
        if th.text == column:
            return ths.index(th)

def get_boxscore(extid):
    proxies = {
        'http': 'http://p.webshare.io:9999',
        'https': 'http://p.webshare.io:9999'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    while True:
        try:
            response = requests.get(f'https://stats.ncaa.org/contests/{extid}/individual_stats', headers=headers, proxies=proxies)
            response.raise_for_status()
            break
        except:
            continue
    
    info = {}

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tables: List[Tag] = soup.find_all('table')

        info['extid'] = extid
        info['playDate'] = datetime.strptime(tables[1].find_all('tr')[3].text.split(' ')[0].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
        info['source'] = f'https://stats.ncaa.org/contests/{extid}/individual_stats'
        info['type'] = 'Regular Season'
        info['stats'] = []

        homeTeam = tables[-1]
        visitorTeam = tables[-2]

        info['homeTeam'] = {
            'name': tables[0].tr.td.find_next_siblings('td')[5].find('a').text.strip()
        }
        
        teamLinkObj = tables[0].tr.td.find_next_siblings('td')[4]
        
        if teamLinkObj:
            try:
                info['homeTeam']['extid'] = teamLinkObj.find('img').get('src').split('/')[-1].split('.')[0]
            except:
                info['homeTeam']['extid'] = '-'
        else:
            info['homeTeam']['extid'] = '-'
            
        info['homeScores'] = {
            'final': tables[1].find_all('tr')[2].find_all('td')[-1].text
        }

        players = homeTeam.find('tbody').find_all('tr', recursive=False)[:-2]

        for player in players:
            cells = player.find_all('td')
            
            stat = {}
            stat['team'] = info['homeTeam']['extid']
            stat['player_extid'] = f"{cells[get_column_index(homeTeam, 'Name')].text.strip()}_{stat['team']}"
            stat['player_name'] = cells[get_column_index(homeTeam, 'Name')].text.strip()
            stat['player_firstname'] = cells[get_column_index(homeTeam, 'Name')].text.split(' ')[0].strip()
            stat['player_lastname'] = cells[get_column_index(homeTeam, 'Name')].text.split(' ')[1].strip()

            item = {}
            item['3pts Attempts'] = cells[get_column_index(homeTeam, '3FGA')].text
            item['3pts Made'] = cells[get_column_index(homeTeam, '3FG')].text
            item['2pts Attempts'] = int(cells[get_column_index(homeTeam, 'FGA')].text) - int(cells[get_column_index(homeTeam, '3FGA')].text)
            item['2pts Made'] = int(cells[get_column_index(homeTeam, 'FGM')].text) - int(cells[get_column_index(homeTeam, '3FG')].text)
            item['Assists'] = cells[get_column_index(homeTeam, 'AST')].text
            item['Block Shots'] = cells[get_column_index(homeTeam, 'BLK')].text
            item['Defensive rebounds'] = cells[get_column_index(homeTeam, 'DRebs')].text
            item['FT Attempts'] = cells[get_column_index(homeTeam, 'FTA')].text
            item['FT Made'] = cells[get_column_index(homeTeam, 'FT')].text
            
            try:
                item['Minutes played'] = round((datetime.strptime(cells[get_column_index(homeTeam, 'MP')].text, '%M:%S').minute * 60 + datetime.strptime(cells[get_column_index(homeTeam, 'MP')].text, '%M:%S').second) / 60)
            except:
                item['Minutes played'] = 0
                
            item['Offensive rebounds'] = cells[get_column_index(homeTeam, 'ORebs')].text
            item['Personal fouls'] = cells[get_column_index(homeTeam, 'Fouls')].text
            item['Points'] = cells[get_column_index(homeTeam, 'PTS')].text
            item['Steals'] = cells[get_column_index(homeTeam, 'STL')].text
            item['Total rebounds'] = cells[get_column_index(homeTeam, 'TotReb')].text
            item['Turnovers'] = cells[get_column_index(homeTeam, 'TO')].text

            stat['items'] = item
            info['stats'].append(stat)

        stat = {}
        stat['team'] = info['homeTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'
        
        teamCells = homeTeam.find('tbody').find_all('tr', recursive=False)[-2].find_all('td')
        item = {}
        item['Total rebounds'] = teamCells[get_column_index(homeTeam, 'TotReb')].text
        item['Defensive rebounds'] = teamCells[get_column_index(homeTeam, 'DRebs')].text
        item['Offensive rebounds'] = teamCells[get_column_index(homeTeam, 'ORebs')].text
        item['Steals'] = teamCells[get_column_index(homeTeam, 'STL')].text
        item['Turnovers'] = teamCells[get_column_index(homeTeam, 'TO')].text

        stat['items'] = item
        info['stats'].append(stat)
        
        info['visitorTeam'] = {
            'name': tables[0].tr.td.find_next_siblings('td')[0].find('a').text.strip()
        }
        
        teamLinkObj = tables[0].tr.td
        
        if teamLinkObj:
            try:
                info['visitorTeam']['extid'] = teamLinkObj.find('img').get('src').split('/')[-1].split('.')[0]
            except:
                info['visitorTeam']['extid'] = '-'
        else:
            info['visitorTeam']['extid'] = '-'
            
        info['visitorScores'] = {
            'final': tables[1].find_all('tr')[1].find_all('td')[-1].text
        }

        players = visitorTeam.find('tbody').find_all('tr', recursive=False)[:-2]

        for player in players:
            cells = player.find_all('td')
            
            stat = {}
            stat['team'] = info['visitorTeam']['extid']
            stat['player_extid'] = f"{cells[get_column_index(visitorTeam, 'Name')].text.strip()}_{stat['team']}"
            stat['player_name'] = cells[get_column_index(visitorTeam, 'Name')].text.strip()
            stat['player_firstname'] = cells[get_column_index(visitorTeam, 'Name')].text.split(' ')[0].strip()
            stat['player_lastname'] = cells[get_column_index(visitorTeam, 'Name')].text.split(' ')[1].strip()

            item = {}
            item['3pts Attempts'] = cells[get_column_index(visitorTeam, '3FGA')].text
            item['3pts Made'] = cells[get_column_index(visitorTeam, '3FG')].text
            item['2pts Attempts'] = int(cells[get_column_index(visitorTeam, 'FGA')].text) - int(cells[get_column_index(homeTeam, '3FGA')].text)
            item['2pts Made'] = int(cells[get_column_index(visitorTeam, 'FGM')].text) - int(cells[get_column_index(homeTeam, '3FG')].text)
            item['Assists'] = cells[get_column_index(visitorTeam, 'AST')].text
            item['Block Shots'] = cells[get_column_index(visitorTeam, 'BLK')].text
            item['Defensive rebounds'] = cells[get_column_index(visitorTeam, 'DRebs')].text
            item['FT Attempts'] = cells[get_column_index(visitorTeam, 'FTA')].text
            item['FT Made'] = cells[get_column_index(visitorTeam, 'FT')].text
            
            try:
                item['Minutes played'] = round((datetime.strptime(cells[get_column_index(visitorTeam, 'MP')].text, '%M:%S').minute * 60 + datetime.strptime(cells[get_column_index(visitorTeam, 'MP')].text, '%M:%S').second) / 60)
            except:
                item['Minutes played'] = 0
                
            item['Offensive rebounds'] = cells[get_column_index(visitorTeam, 'ORebs')].text
            item['Personal fouls'] = cells[get_column_index(visitorTeam, 'Fouls')].text
            item['Points'] = cells[get_column_index(visitorTeam, 'PTS')].text
            item['Steals'] = cells[get_column_index(visitorTeam, 'STL')].text
            item['Total rebounds'] = cells[get_column_index(visitorTeam, 'TotReb')].text
            item['Turnovers'] = cells[get_column_index(visitorTeam, 'TO')].text

            stat['items'] = item
            info['stats'].append(stat)
        
        stat = {}
        stat['team'] = info['visitorTeam']['extid']
        stat['player_extid'] = 'team'
        stat['player_firstname'] = ''
        stat['player_lastname'] = '- TEAM -'
        stat['player_name'] = '- TEAM -'

        teamCells = visitorTeam.find('tbody').find_all('tr', recursive=False)[-2].find_all('td')
        item = {}
        item['Total rebounds'] = teamCells[get_column_index(visitorTeam, 'TotReb')].text
        item['Defensive rebounds'] = teamCells[get_column_index(visitorTeam, 'DRebs')].text
        item['Offensive rebounds'] = teamCells[get_column_index(visitorTeam, 'ORebs')].text
        item['Steals'] = teamCells[get_column_index(visitorTeam, 'STL')].text
        item['Turnovers'] = teamCells[get_column_index(visitorTeam, 'TO')].text

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

def func_ncaa(args, seasonDivisionID):
    if args['f'] == 'schedule':
        season = f"{args['season']}-{str(int(args['season'])+1)[-2:]}"
        sportCode = 'MBB'

        return get_schedule(season, seasonDivisionID, sportCode)
        
    elif args['f'] == 'game':
        return get_boxscore(args['extid'])
    elif args['f'] == 'player':
        proxies = {
            'http': 'http://p.webshare.io:9999',
            'https': 'http://p.webshare.io:9999'
        }

        name, team = args['extid'].split('_')
        
        info = {}
        info['extid'] = args['extid']
        info['source'] = f'https://stats.ncaa.org/teams/{team}/roster'
        info['name'] = name
        info['firstname'] = name.split(' ')[0]
        info['lastname'] = name.split(' ')[1]
        
        for _ in range(5):
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
            }
            response = requests.get(f'https://stats.ncaa.org/teams/{team}/roster', headers=headers, proxies=proxies)

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

                break

        return info
