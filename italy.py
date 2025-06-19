from library import *

def func_italy_a1(args):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }
    # Get schedule
    if args['f'] == 'schedule':
        games = []
        args['season'] = request.args.get('season')

        response = requests.get(f'https://www.legabasket.it/api/championships/get-championships?s={args["season"]}&cs_id=1&items=1000', headers=headers)

        if response.status_code == 200:
            data = response.json()

            for competition in data['competitions']:
                competition_name = competition['full_name']
                competition_id = competition['id']

                response = requests.get(f'https://www.legabasket.it/api/championships/get-championships-calendar-by-id?id={competition_id}', headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    for phase in data['filters']['phases']:
                        response = requests.get(f'https://www.legabasket.it/api/championships/get-championships-calendar-by-id?id={competition_id}&ph_id={phase["id"]}', headers=headers)

                        if response.status_code == 200:
                            matches = response.json()['matches']

                            if matches:
                                for match in matches:
                                    game = {}
                                    game['competition'] = competition_name
                                    game['playDate'] = match['match_datetime'].split('T')[0]
                                    game['round'] = match['day_name']
                                    
                                    if match['game_status'] == '2':
                                        game['state'] = 'result'
                                    elif match['game_status'] == '0':
                                        game['state'] = 'confirmed'

                                    game['type'] = competition['ctype_name']
                                    game['homeTeam'] = {
                                        'extid': match['h_team_id'],
                                        'name': match['h_team_name']
                                    }

                                    if game['state'] == 'result':
                                        game['homeScores'] = {
                                            'final': match['home_final_score']
                                        }

                                    game['visitorTeam'] = {
                                        'extid': match['v_team_id'],
                                        'name': match['v_team_name']
                                    }

                                    if game['state'] == 'result':
                                        game['visitorScores'] = {
                                            'final': match['visitor_final_score']
                                        }

                                    game['extid'] = match['id']
                                    game['source'] = f'https://www.legabasket.it/game/{match["id"]}/'

                                    games.append(game)

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        gameId = request.args.get('extid')

        response = requests.get(f'https://www.legabasket.it/api/championships/get-championships-matches-by-id?id={gameId}', headers=headers)

        if response.status_code == 200:
            data = response.json()
            info = {}
            info['extid'] = gameId
            info['playDate'] = data['match']['match_datetime'].split('T')[0]
            info['source'] = f'https://www.legabasket.it/game/{gameId}/'
            info['type'] = data['match']['competition_type']
            info['homeTeam'] = {
                'extid': data['match']['h_team_id'],
                'name': data['match']['h_team_name']
            }
            info['homeScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': data['match']['home_final_score']
            }
            info['visitorTeam'] = {
                'extid': data['match']['v_team_id'],
                'name': data['match']['v_team_name']
            }
            info['visitorScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': data['match']['visitor_final_score']
            }

            info['stats'] = []

            if data['match']['game_status'] == "2":
                info['homeScores']['QT1'] = data['match']['q1_hs']
                info['homeScores']['QT2'] = data['match']['q2_hs']
                info['homeScores']['QT3'] = data['match']['q3_hs']
                info['homeScores']['QT4'] = data['match']['q4_hs']

                info['visitorScores']['QT1'] = data['match']['q1_vs']
                info['visitorScores']['QT2'] = data['match']['q2_vs']
                info['visitorScores']['QT3'] = data['match']['q3_vs']
                info['visitorScores']['QT4'] = data['match']['q4_vs']

                info['homeScores']['extra'] += data['match']['ot_hs']
                info['visitorScores']['extra'] += data['match']['ot_vs']

                # Home
                for row in data['scores']['ht']['rows']:
                    stat = {}
                    stat['team'] = info['homeTeam']['extid']
                    
                    stat['player_firstname'] = row['player_name']
                    stat['player_lastname'] = row['player_surname']
                    stat['player_name'] = f'{stat["player_lastname"]} {stat["player_firstname"]}'
                    stat['player_extid'] = row['player_id']

                    item = {}
                    item['2pts Attempts'] = row['t2_t']
                    item['2pts Made'] = row['t2_r']
                    item['3pts Attempts'] = row['t3_t']
                    item['3pts Made'] = row['t3_r']
                    item['Assists'] = row['ass']
                    item['Block Shots'] = row['stoppate_dat']
                    item['Defensive rebounds'] = row['rimbalzi_d']
                    item['FT Attempts'] = row['tl_t']
                    item['FT Made'] = row['tl_r']
                    item['Minutes played'] = row['min']
                    item['Offensive rebounds'] = row['rimbalzi_o']
                    item['Personal fouls'] = row['falli_c']
                    item['Points'] = row['pun']
                    item['Steals'] = row['palle_r']
                    item['Total rebounds'] = row['rimbalzi_t']
                    item['Turnovers'] = row['palle_p']

                    stat['items'] = item
                    info['stats'].append(stat)
                    
                stat = {}
                stat['team'] = info['homeTeam']['extid']
                stat['player_extid'] = 'team'
                stat['player_firstname'] = ''
                stat['player_lastname'] = '- TEAM -'
                stat['player_name'] = '- TEAM -'

                item = {}
                item['Defensive rebounds'] = data['scores']['ht']['team']['rimbalzi_d']
                item['Offensive rebounds'] = data['scores']['ht']['team']['rimbalzi_o']
                item['Total rebounds'] = data['scores']['ht']['team']['rimbalzi_t']
                item['Turnovers'] = data['scores']['ht']['team']['palle_p']
                item['Personal fouls'] = data['scores']['ht']['team']['falli_c']

                stat['items'] = item
                info['stats'].append(stat)
                
                # Visitor
                for row in data['scores']['vt']['rows']:
                    stat = {}
                    stat['team'] = info['visitorTeam']['extid']
                    
                    stat['player_firstname'] = row['player_name']
                    stat['player_lastname'] = row['player_surname']
                    stat['player_name'] = f'{stat["player_lastname"]} {stat["player_firstname"]}'
                    stat['player_extid'] = row['player_id']

                    item = {}
                    item['2pts Attempts'] = row['t2_t']
                    item['2pts Made'] = row['t2_r']
                    item['3pts Attempts'] = row['t3_t']
                    item['3pts Made'] = row['t3_r']
                    item['Assists'] = row['ass']
                    item['Block Shots'] = row['stoppate_dat']
                    item['Defensive rebounds'] = row['rimbalzi_d']
                    item['FT Attempts'] = row['tl_t']
                    item['FT Made'] = row['tl_r']
                    item['Minutes played'] = row['min']
                    item['Offensive rebounds'] = row['rimbalzi_o']
                    item['Personal fouls'] = row['falli_c']
                    item['Points'] = row['pun']
                    item['Steals'] = row['palle_r']
                    item['Total rebounds'] = row['rimbalzi_t']
                    item['Turnovers'] = row['palle_p']

                    stat['items'] = item
                    info['stats'].append(stat)
                    
                stat = {}
                stat['team'] = info['visitorTeam']['extid']
                stat['player_extid'] = 'team'
                stat['player_firstname'] = ''
                stat['player_lastname'] = '- TEAM -'
                stat['player_name'] = '- TEAM -'

                item = {}
                item['Defensive rebounds'] = data['scores']['vt']['team']['rimbalzi_d']
                item['Offensive rebounds'] = data['scores']['vt']['team']['rimbalzi_o']
                item['Total rebounds'] = data['scores']['vt']['team']['rimbalzi_t']
                item['Turnovers'] = data['scores']['vt']['team']['palle_p']
                item['Personal fouls'] = data['scores']['vt']['team']['falli_c']

                stat['items'] = item
                info['stats'].append(stat)
            return info
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        playerId = request.args.get('extid')

        response = requests.get(f'https://www.legabasket.it/api/players/get-player-by-id?id={playerId}&stats=true', headers=headers)

        if response.status_code == 200:
            data = response.json()

            info = {}
            info['extid'] = playerId
            info['team'] = data['player']['team_name']
            info['dateOfBirth'] = data['player']['birth_date']
            info['shirtNumber'] = data['player']['player_number']
            info['firstname'] = data['player']['name']
            info['lastname'] = data['player']['surname']
            info['name'] = f'{info["firstname"]} {info["lastname"]}'
            info['height'] = data['player']['height']
            info['weight'] = data['player']['weight']
            info['nationality'] = data['player']['player_alpha3']
            info['birthPlace'] = data['player']['place_of_birth']
            info['position'] = data['player']['player_role_description']
            info['source'] = f'https://www.legabasket.it/protagonisti/giocatori/{playerId}/'
            
            return info
        return {'error': 'Something went wrong!'}
    else:
        return {'error': 'Something went wrong!'}

def func_italy_a2(args):
    a2_resp = requests.get('https://www.legapallacanestro.com/serie-a2')
    a2_soup = BeautifulSoup(a2_resp.text, 'html.parser')
    select_round = a2_soup.find('select', attrs={'name': 'round'})
    rounds = len(select_round.find_all('option'))

    # Get schedule
    if args['f'] == 'schedule':
        args['season'] = args.get('season')
        year = f"x{args['season'][-2:]}{str(int(args['season']) + 1)[-2:]}"
        
        games = []

        def get_schedule(league: str):
            round_index = 0
            while True:
                if 'ply' in league:
                    response = requests.get(f'https://lnpstat.domino.it/getstatisticsfiles?task=schedule&year={year}&league={league.split("_")[0]}&pl=ply&round=all')
                elif 'pli' in league:
                    response = requests.get(f'https://lnpstat.domino.it/getstatisticsfiles?task=schedule&year={year}&league={league.split("_")[0]}&pl=pli&round=all')
                elif 'plo' in league:
                    response = requests.get(f'https://lnpstat.domino.it/getstatisticsfiles?task=schedule&year={year}&league={league.split("_")[0]}&pl=plo&round=all')
                else:
                    round_index += 1
                    response = requests.get(f'https://lnpstat.domino.it/getstatisticsfiles?task=schedule&year={year}&league={league.split("_")[0]}&round={round_index}')

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        return

                    for item in data:
                        game = {}
                        game['competition'] = 'SEIRE A2'
                        game['playDate'] = datetime.strptime(item['date'], '%d/%m/%Y').strftime('%Y-%m-%d')
                        game['round'] = item['round']
                        
                        if item['game_status'] == 'finished':
                            game['state'] = 'result'
                        else:
                            game['state'] = 'confirmed'

                        if 'ply' in league:
                            game['type'] = 'Play Off'
                        elif 'pli' in league:
                            game['type'] = 'Play In'
                        elif 'plo' in league:
                            game['type'] = 'Play Out'
                        else:
                            game['type'] = 'Regular Season'
                            
                        game['homeTeam'] = {
                            'extid': item['teamid_home'],
                            'name': item['teamname_home']
                        }

                        if game['state'] == 'result':
                            game['homeScores'] = {
                                'final': item['score_home']
                            }

                        game['visitorTeam'] = {
                            'extid': item['teamid_away'],
                            'name': item['teamname_away']
                        }

                        if game['state'] == 'result':
                            game['visitorScores'] = {
                                'final': item['score_away']
                            }

                        game['extid'] = f'{item["gameid"]}-{game["homeTeam"]["extid"]}-{game["homeTeam"]["name"].replace("-", "_")}-{game["visitorTeam"]["extid"]}-{game["visitorTeam"]["name"].replace("-", "_")}-{game["playDate"].replace("-", "_")}-{league}'
                        game['source'] = f'https://www.legapallacanestro.com/wp/match/{item["gameid"]}/{league.split("_")[0]}/{year}'

                        games.append(game)

                if 'ply' in league or 'pli' in league or 'plo' in league:
                    break
                elif round_index > rounds:
                    break

        def get_clock_schedule(league: str):
            url = 'https://www.legapallacanestro.com/system/ajax'
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            }
            payload = f"competizione={year}-{league}&round=1&form_build_id=form-Adr2M1pVkN3L9VOk6moY9bigcSYsENe9midS6zBHuAU&form_id=lnp_risultati_archivio_storico_form&_triggering_element_name=competizione&ajax_html_ids%5B%5D=sliding-popup&ajax_html_ids%5B%5D=popup-text&ajax_html_ids%5B%5D=popup-buttons&ajax_html_ids%5B%5D=skip-link&ajax_html_ids%5B%5D=topbar&ajax_html_ids%5B%5D=block-lnp-social-links&ajax_html_ids%5B%5D=navbar&ajax_html_ids%5B%5D=block-lnp-login-logout&ajax_html_ids%5B%5D=menu-evo&ajax_html_ids%5B%5D=block-lnp-menu-principale&ajax_html_ids%5B%5D=mp-menu&ajax_html_ids%5B%5D=block-menu-block-6&ajax_html_ids%5B%5D=main-content&ajax_html_ids%5B%5D=block-system-main&ajax_html_ids%5B%5D=lnp-risultati-archivio-storico-form&ajax_html_ids%5B%5D=ajax-wrapper&ajax_html_ids%5B%5D=edit-tabella-filters--2&ajax_html_ids%5B%5D=edit-competizione--2&ajax_html_ids%5B%5D=edit-round--2&ajax_html_ids%5B%5D=block-bean-banner-collection-2&ajax_html_ids%5B%5D=block-bean-banner-old-wild-west&ajax_html_ids%5B%5D=block-bean-banner-myglass&ajax_html_ids%5B%5D=block-views-nodequeue-7-block&ajax_html_ids%5B%5D=block-bean-banner-collection-3&ajax_html_ids%5B%5D=block-bean-banner-partner-1&ajax_html_ids%5B%5D=block-bean-banner-partner-3&ajax_html_ids%5B%5D=block-bean-banner-partner-4&ajax_html_ids%5B%5D=block-menu-block-1&ajax_html_ids%5B%5D=block-menu-block-3&ajax_html_ids%5B%5D=block-block-3&ajax_html_ids%5B%5D=cboxOverlay&ajax_html_ids%5B%5D=goog-gt-tt&ajax_html_ids%5B%5D=goog-gt-vt&ajax_html_ids%5B%5D=goog-gt-original-text&ajax_html_ids%5B%5D=goog-gt-thumbUpButton&ajax_html_ids%5B%5D=goog-gt-thumbUpIcon&ajax_html_ids%5B%5D=goog-gt-thumbUpIconFilled&ajax_html_ids%5B%5D=goog-gt-thumbDownButton&ajax_html_ids%5B%5D=goog-gt-thumbDownIcon&ajax_html_ids%5B%5D=goog-gt-thumbDownIconFilled&ajax_html_ids%5B%5D=goog-gt-votingHiddenPane&ajax_html_ids%5B%5D=goog-gt-votingForm&ajax_html_ids%5B%5D=goog-gt-votingInputSrcLang&ajax_html_ids%5B%5D=goog-gt-votingInputTrgLang&ajax_html_ids%5B%5D=goog-gt-votingInputSrcText&ajax_html_ids%5B%5D=goog-gt-votingInputTrgText&ajax_html_ids%5B%5D=goog-gt-votingInputVote&ajax_html_ids%5B%5D=colorbox&ajax_html_ids%5B%5D=cboxWrapper&ajax_html_ids%5B%5D=cboxTopLeft&ajax_html_ids%5B%5D=cboxTopCenter&ajax_html_ids%5B%5D=cboxTopRight&ajax_html_ids%5B%5D=cboxMiddleLeft&ajax_html_ids%5B%5D=cboxContent&ajax_html_ids%5B%5D=cboxTitle&ajax_html_ids%5B%5D=cboxCurrent&ajax_html_ids%5B%5D=cboxPrevious&ajax_html_ids%5B%5D=cboxNext&ajax_html_ids%5B%5D=cboxSlideshow&ajax_html_ids%5B%5D=cboxLoadingOverlay&ajax_html_ids%5B%5D=cboxLoadingGraphic&ajax_html_ids%5B%5D=cboxMiddleRight&ajax_html_ids%5B%5D=cboxBottomLeft&ajax_html_ids%5B%5D=cboxBottomCenter&ajax_html_ids%5B%5D=cboxBottomRight&ajax_page_state%5Btheme%5D=lnp_2023_theme&ajax_page_state%5Btheme_token%5D=99jTnueihkeqiMS2KIp1joCUku_dtEHEtpjgzCjDCCM&ajax_page_state%5Bcss%5D%5B0%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fsystem%2Fsystem.base.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fdate%2Fdate_api%2Fdate.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fdate%2Fdate_popup%2Fthemes%2Fdatepicker.1.7.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Ffield%2Ftheme%2Ffield.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fyoutube%2Fcss%2Fyoutube.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fviews%2Fcss%2Fviews.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fckeditor%2Fcss%2Fckeditor.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcolorbox%2Fstyles%2Fdefault%2Fcolorbox_style.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fctools%2Fcss%2Fctools.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fauthcache%2Fmodules%2Fauthcache_debug%2Fauthcache_debug.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Ffield_collection%2Ffield_collection.theme.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Ffield_group%2Ffield_group.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Feu_cookie_compliance%2Fcss%2Feu_cookie_compliance.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Flib%2Fowlcarousel%2Fowl.carousel.min.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fcss%2Fstyle.css%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Flnp%2Fjs%2Flnp.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Feu_cookie_compliance%2Fjs%2Feu_cookie_compliance.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcontrib%2Fbootstrap%2Fjs%2Fbootstrap.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Freplace%2Fjquery%2F1.11%2Fjquery.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery.once.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fdrupal.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Freplace%2Fui%2Fexternal%2Fjquery.cookie.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Flibraries%2Fmoment%2Fmin%2Fmoment.min.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Flnp%2Fjs%2Flnp.gtm.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Freplace%2Fmisc%2Fjquery.form.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fajax.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Fjs%2Fjquery_update.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fadmin_menu%2Fadmin_devel%2Fadmin_devel.js%5D=1&ajax_page_state%5Bjs%5D%5Bpublic%3A%2F%2Flanguages%2Fit_YaPSpQuSuJMAWKrcfdlKy0YkSKBSJ2VhZD_TQTV_hFs.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fauthcache%2Fauthcache.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Flibraries%2Fcolorbox%2Fjquery.colorbox-min.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcolorbox%2Fjs%2Fcolorbox.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcolorbox%2Fstyles%2Fdefault%2Fcolorbox_style.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcolorbox%2Fjs%2Fcolorbox_load.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcontrib%2Fbootstrap%2Fjs%2Fmisc%2F_progress.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Flibraries%2Ftimeago%2Fjquery.timeago.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Ftimeago%2Ftimeago.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Ftableheader.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fauthcache%2Fmodules%2Fauthcache_debug%2Fauthcache_debug.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Ffield_group%2Ffield_group.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Faffix.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Falert.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fbutton.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fcarousel.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fcollapse.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fdropdown.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fmodal.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Ftooltip.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fpopover.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Fscrollspy.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Ftab.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fbootstrap%2Fjs%2Ftransition.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Flib%2Fowlcarousel%2Fowl.carousel.min.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Flib%2Fscrollmagic%2Fscrollmagic.min.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcustom%2Flnp_2023_theme%2Fjs%2Flnp_theme.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcontrib%2Fbootstrap%2Fjs%2Fmisc%2Fajax.js%5D=1&ajax_page_state%5Bjquery_version%5D=1.11"
            resp = requests.post(url, headers=headers, data=payload)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except:
                    return
                
                html = data[1]['data']
                soup = BeautifulSoup(html, 'html.parser')
                table = soup.find('table', class_='table')
                tbody = table.find('tbody')
                rows: List[Tag] = tbody.find_all('tr')

                for row in rows:
                    game = {}

                    cells: List[Tag] = row.find_all('td')

                    game['competition'] = 'SEIRE A2'
                    game['playDate'] = datetime.strptime(cells[0].text, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d')
                    game['round'] = 1
                    game['state'] = 'result'
                    game['type'] = 'Clock Phase'
                    game['homeTeam'] = {
                        'extid': cells[1].text.replace('.', '').replace(' ', '-').strip().lower(),
                        'name': cells[1].text
                    }
                    game['visitorTeam'] = {
                        'extid': cells[2].text.replace('.', '').replace(' ', '-').strip().lower(),
                        'name': cells[2].text
                    }

                    scores = cells[3].text.split('-')
                    game['homeScores'] = {
                        'final': int(scores[0].strip())
                    }
                    game['visitorScores'] = {
                        'final': int(scores[1].strip())
                    }

                    gameid = cells[3].find('a').get('href').split('/')[3]
                    game['extid'] = f'{gameid}-{game["homeTeam"]["extid"].replace("-", "_")}-{game["homeTeam"]["name"].replace("-", "_")}-{game["visitorTeam"]["extid"].replace("-", "_")}-{game["visitorTeam"]["name"].replace("-", "_")}-{game["playDate"].replace("-", "_")}-{league}'
                    game['source'] = 'https://www.legapallacanestro.com' + cells[3].find('a').get('href')

                    games.append(game)

        # get_clock_schedule('ita2_clock')
        get_schedule('ita2')
        get_schedule('ita2_ply')
        get_schedule('ita2_pli')
        get_schedule('ita2_plo')

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        args['extid'], args['homeTeamId'], args['homeTeamName'], args['visitorTeamId'], args['visitorTeamName'], args['playDate'], args['league'] = request.args.get('extid').split('-')
        args['season'] = request.args.get('season')
        year = f"x{args['season'][-2:]}{str(int(args['season']) + 1)[-2:]}"
        
        response = requests.get(f'https://www.legapallacanestro.com/wp/match/{args["extid"]}/{args["league"].split("_")[0]}/{year}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = args['extid']

            target = soup.find('section', id="block-system-main").text.strip()

            args['state'] = 'result'

            if target == 'I dati di questa partita non sono ancora disponibili.':
                args['state'] = 'confirmed'

            if args['state'] == 'result':
                info['playDate'] = datetime.strptime(soup.find('div', class_='match-date-value').text.split(' ')[0], '%d/%m/%Y').strftime('%Y-%m-%d')
            else:
                info['playDate'] = args['playDate'].replace('_', '-')
                
            info['source'] = response.url

            if 'pli' in args['league']:
                info['type'] = 'Play In'
            elif 'ply' in args['league']:
                info['type'] = 'Play Off'
            elif 'plo' in args['league']:
                info['type'] = 'Play Out'
            else:
                info['type'] = 'Regular Season'
                
            info['homeTeam'] = {
                'extid': args['homeTeamId'],
                'name': args['homeTeamName'].replace('_', '-')
            }
            info['homeScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': 0
            }

            if args['state'] == 'result':
                info['homeScores']['final'] = soup.find('div', class_='match-result-score').find_all('span')[0].text.strip()

            info['visitorTeam'] = {
                'extid': args['visitorTeamId'],
                'name': args['visitorTeamName'].replace('_', '-')
            }
            info['visitorScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': 0
            }

            if args['state'] == 'result':
                info['visitorScores']['final'] = soup.find('div', class_='match-result-score').find_all('span')[1].text.strip()

            info['stats'] = []

            if args['state'] == 'result':
                info['homeScores']['QT1'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[1].find_all('td')[0].text
                info['homeScores']['QT2'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[2].find_all('td')[0].text
                info['homeScores']['QT3'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[3].find_all('td')[0].text
                info['homeScores']['QT4'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[4].find_all('td')[0].text

                info['visitorScores']['QT1'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[1].find_all('td')[1].text
                info['visitorScores']['QT2'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[2].find_all('td')[1].text
                info['visitorScores']['QT3'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[3].find_all('td')[1].text
                info['visitorScores']['QT4'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[4].find_all('td')[1].text

                homeExtraScores = soup.find('div', class_='match-result-periods').find_all('tr')[0].find_all('td')[5:]

                for score in homeExtraScores:
                    info['homeScores']['extra'] += int(score.text)

                visitorExtraScores = soup.find('div', class_='match-result-periods').find_all('tr')[1].find_all('td')[5:]

                for score in visitorExtraScores:
                    info['visitorScores']['extra'] += int(score.text)

                form = soup.find('form', id='lnp-boxscore-form')
                payload = {
                    'form_build_id': form.find('input', {'name': 'form_build_id'})['value'],
                    'form_id': form.find('input', {'name': 'form_id'})['value']
                }
                response = requests.post(info['source'], data=payload)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    tables = soup.find_all('div', class_='table-wrapper-evo')
                    # Home
                    playerPart = tables[0].table.tbody
                    scorePart = tables[0].find('td', class_='table-right')
                    
                    playerRows = playerPart.find('tbody').find_all('tr')
                    scoreRows = scorePart.find('tbody').find_all('tr')

                    for index in range(len(playerRows)-1):
                        stat = {}
                        stat['team'] = info['homeTeam']['extid']

                        if index == len(playerRows) - 2:
                            stat['player_extid'] = 'team'
                            stat['player_firstname'] = ''
                            stat['player_lastname'] = '- TEAM -'
                            stat['player_name'] = '- TEAM -'
                        else:
                            stat['player_firstname'] = playerRows[index].find('a').text.split(' ')[0]
                            stat['player_lastname'] = playerRows[index].find('a').text.split(' ')[1]
                            stat['player_name'] = f'{stat["player_lastname"]} {stat["player_firstname"]}'
                            stat['player_extid'] = playerRows[index].find('a')['href'].split('/')[3]

                        item = {}
                        item['2pts Attempts'] = scoreRows[index].find_all('td')[5].text
                        item['2pts Made'] = scoreRows[index].find_all('td')[4].text
                        item['3pts Attempts'] = scoreRows[index].find_all('td')[8].text
                        item['3pts Made'] = scoreRows[index].find_all('td')[7].text
                        item['Assists'] = scoreRows[index].find_all('td')[20].text
                        item['Block Shots'] = scoreRows[index].find_all('td')[16].text
                        item['Defensive rebounds'] = scoreRows[index].find_all('td')[14].text
                        item['FT Attempts'] = scoreRows[index].find_all('td')[11].text
                        item['FT Made'] = scoreRows[index].find_all('td')[10].text
                        item['Minutes played'] = scoreRows[index].find_all('td')[1].text
                        item['Offensive rebounds'] = scoreRows[index].find_all('td')[13].text
                        item['Personal fouls'] = scoreRows[index].find_all('td')[2].text
                        item['Points'] = scoreRows[index].find_all('td')[0].text
                        item['Steals'] = scoreRows[index].find_all('td')[19].text
                        item['Total rebounds'] = scoreRows[index].find_all('td')[15].text
                        item['Turnovers'] = scoreRows[index].find_all('td')[18].text

                        stat['items'] = item
                        info['stats'].append(stat)
                    # Visitor
                    playerPart = tables[1].table.tbody
                    scorePart = tables[1].find('td', class_='table-right')

                    playerRows = playerPart.find('tbody').find_all('tr')
                    scoreRows = scorePart.find('tbody').find_all('tr')

                    for index in range(len(playerRows)-1):
                        stat = {}
                        stat['team'] = info['visitorTeam']['extid']

                        if index == len(playerRows) - 2:
                            stat['player_extid'] = 'team'
                            stat['player_firstname'] = ''
                            stat['player_lastname'] = '- TEAM -'
                            stat['player_name'] = '- TEAM -'
                        else:
                            stat['player_firstname'] = playerRows[index].find('a').text.split(' ')[0]
                            stat['player_lastname'] = playerRows[index].find('a').text.split(' ')[1]
                            stat['player_name'] = f'{stat["player_lastname"]} {stat["player_firstname"]}'
                            stat['player_extid'] = playerRows[index].find('a')['href'].split('/')[3]

                        item = {}
                        item['2pts Attempts'] = scoreRows[index].find_all('td')[5].text
                        item['2pts Made'] = scoreRows[index].find_all('td')[4].text
                        item['3pts Attempts'] = scoreRows[index].find_all('td')[8].text
                        item['3pts Made'] = scoreRows[index].find_all('td')[7].text
                        item['Assists'] = scoreRows[index].find_all('td')[20].text
                        item['Block Shots'] = scoreRows[index].find_all('td')[16].text
                        item['Defensive rebounds'] = scoreRows[index].find_all('td')[14].text
                        item['FT Attempts'] = scoreRows[index].find_all('td')[11].text
                        item['FT Made'] = scoreRows[index].find_all('td')[10].text
                        item['Minutes played'] = scoreRows[index].find_all('td')[1].text
                        item['Offensive rebounds'] = scoreRows[index].find_all('td')[13].text
                        item['Personal fouls'] = scoreRows[index].find_all('td')[2].text
                        item['Points'] = scoreRows[index].find_all('td')[0].text
                        item['Steals'] = scoreRows[index].find_all('td')[19].text
                        item['Total rebounds'] = scoreRows[index].find_all('td')[15].text
                        item['Turnovers'] = scoreRows[index].find_all('td')[18].text

                        stat['items'] = item
                        info['stats'].append(stat)
                
            return info
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        args['extid'] = request.args.get('extid')

        response = requests.get(f'https://www.legapallacanestro.com/giocatore/wp/{args["extid"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = args['extid']
            info['team'] = soup.find('div', class_='player-info-row2').find_all('li')[4].find('span', class_='spec-value').text
            info['dateOfBirth'] = datetime.strptime(soup.find('div', class_='player-info-row2').find_all('li')[0].find('span', class_='spec-value').text, '%d/%m/%Y').strftime('%Y-%m-%d')
            info['shirtNumber'] = soup.find('div', class_='num-maglia').text
            info['firstname'] = soup.find('div', class_='player-name').text.split(' ')[1]
            info['lastname'] = soup.find('div', class_='player-name').text.split(' ')[0]
            info['name'] = f'{info["firstname"]} {info["lastname"]}'
            info['height'] = soup.find('div', class_='player-info-row2').find_all('li')[2].find('span', class_='spec-value').text.replace('cm', '').strip()
            info['weight'] = soup.find('div', class_='player-info-row2').find_all('li')[3].find('span', class_='spec-value').text.replace('kg', '').strip()
            info['nationality'] = soup.find('div', class_='player-info-row2').find_all('li')[1].find('span', class_='spec-value').text
            info['position'] = soup.find('div', class_='ruolo').text
            info['source'] = response.url

            return info
        return {'error': 'Something went wrong!'}
    else:
        return {'error': 'Something went wrong!'}

def func_italy_b(args):
    # Get schedule
    if args['f'] == 'schedule':
        args['season'] = request.args.get('season')
        year = f"x{args['season'][-2:]}{str(int(args['season']) + 1)[-2:]}"

        cal_resp = requests.get('https://www.legapallacanestro.com/serie/4/calendario')
        cal_soup = BeautifulSoup(cal_resp.text, 'html.parser')
        script = cal_soup.find('script', attrs={'src': None})
        calendario = json.loads(script.text.replace('jQuery.extend(Drupal.settings, ', '')[:-2])['calendario']
        leauges = list(calendario.keys())
        
        games = []

        def get_schedule(league: str):
            rounds = list(calendario[league]['round_options'])

            for round in rounds:
                response = requests.get(f'https://lnpstat.domino.it/getstatisticsfiles?task=schedule&year={year}&league={league}&round={round}')

                if response.status_code == 200:
                    data = response.json()

                    for item in data:
                        game = {}
                        game['competition'] = 'SEIRE B'
                        game['playDate'] = datetime.strptime(item['date'], '%d/%m/%Y').strftime('%Y-%m-%d')
                        game['round'] = item['round']
                        
                        if item['game_status'] == 'finished':
                            game['state'] = 'result'
                        else:
                            game['state'] = 'confirmed'

                        game['type'] = 'Regular Season'
                        game['homeTeam'] = {
                            'extid': item['teamid_home'],
                            'name': item['teamname_home']
                        }

                        if game['state'] == 'result':
                            game['homeScores'] = {
                                'final': item['score_home']
                            }

                        game['visitorTeam'] = {
                            'extid': item['teamid_away'],
                            'name': item['teamname_away']
                        }

                        if game['state'] == 'result':
                            game['visitorScores'] = {
                                'final': item['score_away']
                            }

                        game['extid'] = f'{item["gameid"]}-{game["homeTeam"]["extid"]}-{game["homeTeam"]["name"].replace("-", "_")}-{game["visitorTeam"]["extid"]}-{game["visitorTeam"]["name"].replace("-", "_")}-{game["playDate"].replace("-", "_")}-{league}'
                        game['source'] = f'https://www.legapallacanestro.com/wp/match/{item["gameid"]}/{league}/{year}'

                        games.append(game)

        def get_playoff_schedule(league: str):
            response = requests.get(f'https://lnpstat.domino.it/getstatisticsfiles?task=schedule&year={year}&league={league}&round=all&pl=ply')

            if response.status_code == 200:
                try:
                    data = response.json()
                except:
                    return

                for item in data:
                    game = {}
                    game['competition'] = 'SEIRE B'
                    game['playDate'] = datetime.strptime(item['date'], '%d/%m/%Y').strftime('%Y-%m-%d')
                    game['round'] = item['round']
                    
                    if item['game_status'] == 'finished':
                        game['state'] = 'result'
                    else:
                        game['state'] = 'confirmed'

                    game['type'] = 'Playoff'
                    game['homeTeam'] = {
                        'extid': item['teamid_home'],
                        'name': item['teamname_home']
                    }

                    if game['state'] == 'result':
                        game['homeScores'] = {
                            'final': item['score_home']
                        }

                    game['visitorTeam'] = {
                        'extid': item['teamid_away'],
                        'name': item['teamname_away']
                    }

                    if game['state'] == 'result':
                        game['visitorScores'] = {
                            'final': item['score_away']
                        }

                    game['extid'] = f'{item["gameid"]}-{game["homeTeam"]["extid"]}-{game["homeTeam"]["name"].replace("-", "_")}-{game["visitorTeam"]["extid"]}-{game["visitorTeam"]["name"].replace("-", "_")}-{game["playDate"].replace("-", "_")}-{league}'
                    game['source'] = f'https://www.legapallacanestro.com/wp/match/{item["gameid"]}/{league}/{year}'

                    games.append(game)
        
        for league in leauges:
            get_schedule(league)
            get_playoff_schedule(league)

        return json.dumps(games, indent=4)
    elif args['f'] == 'game':
        args['extid'], args['homeTeamId'], args['homeTeamName'], args['visitorTeamId'], args['visitorTeamName'], args['playDate'], args['league'] = request.args.get('extid').split('-')
        args['season'] = request.args.get('season')
        year = f"x{args['season'][-2:]}{str(int(args['season']) + 1)[-2:]}"
        
        response = requests.get(f'https://www.legapallacanestro.com/wp/match/{args["extid"]}/{args["league"]}/{year}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = args['extid']

            target = soup.find('section', id="block-system-main").text.strip()

            args['state'] = 'result'
            
            if target == 'I dati di questa partita non sono ancora disponibili.':
                args['state'] = 'confirmed'

            if args['state'] == 'result':
                info['playDate'] = datetime.strptime(soup.find('div', class_='match-date-value').text.split(' ')[0], '%d/%m/%Y').strftime('%Y-%m-%d')
            else:
                info['playDate'] = args['playDate'].replace('_', '-')
                
            info['source'] = response.url
            info['type'] = 'Regular Season'
            info['homeTeam'] = {
                'extid': args['homeTeamId'],
                'name': args['homeTeamName'].replace('_', '-')
            }
            info['homeScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': 0
            }

            if args['state'] == 'result':
                info['homeScores']['final'] = soup.find('div', class_='match-result-score').find_all('span')[0].text.strip()

            info['visitorTeam'] = {
                'extid': args['visitorTeamId'],
                'name': args['visitorTeamName'].replace('_', '-')
            }
            info['visitorScores'] = {
                'QT1': 0,
                'QT2': 0,
                'QT3': 0,
                'QT4': 0,
                'extra': 0,
                'final': 0
            }

            if args['state'] == 'result':
                info['visitorScores']['final'] = soup.find('div', class_='match-result-score').find_all('span')[1].text.strip()

            info['stats'] = []

            if args['state'] == 'result':
                info['homeScores']['QT1'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[1].find_all('td')[0].text
                info['homeScores']['QT2'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[2].find_all('td')[0].text
                info['homeScores']['QT3'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[3].find_all('td')[0].text
                info['homeScores']['QT4'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[4].find_all('td')[0].text

                info['visitorScores']['QT1'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[1].find_all('td')[1].text
                info['visitorScores']['QT2'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[2].find_all('td')[1].text
                info['visitorScores']['QT3'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[3].find_all('td')[1].text
                info['visitorScores']['QT4'] = soup.find('div', class_='match-result-periods').find_all('tbody')[-1].find_all('tr')[4].find_all('td')[1].text

                homeExtraScores = soup.find('div', class_='match-result-periods').find_all('tr')[0].find_all('td')[5:]

                for score in homeExtraScores:
                    info['homeScores']['extra'] += int(score.text)

                visitorExtraScores = soup.find('div', class_='match-result-periods').find_all('tr')[1].find_all('td')[5:]

                for score in visitorExtraScores:
                    info['visitorScores']['extra'] += int(score.text)

                form = soup.find('form', id='lnp-boxscore-form')
                payload = {
                    'form_build_id': form.find('input', {'name': 'form_build_id'})['value'],
                    'form_id': form.find('input', {'name': 'form_id'})['value']
                }
                response = requests.post(info['source'], data=payload)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    tables = soup.find_all('div', class_='table-wrapper-evo')
                    # Home
                    playerPart = tables[0].table.tbody
                    scorePart = tables[0].find('td', class_='table-right')
                    
                    playerRows = playerPart.find('tbody').find_all('tr')
                    scoreRows = scorePart.find('tbody').find_all('tr')

                    for index in range(len(playerRows)-1):
                        stat = {}
                        stat['team'] = info['homeTeam']['extid']

                        if index == len(playerRows) - 2:
                            stat['player_extid'] = 'team'
                            stat['player_firstname'] = ''
                            stat['player_lastname'] = '- TEAM -'
                            stat['player_name'] = '- TEAM -'
                        else:
                            stat['player_firstname'] = playerRows[index].find('a').text.split(' ')[0]
                            stat['player_lastname'] = playerRows[index].find('a').text.split(' ')[1]
                            stat['player_name'] = f'{stat["player_lastname"]} {stat["player_firstname"]}'
                            stat['player_extid'] = playerRows[index].find('a')['href'].split('/')[3]

                        item = {}
                        item['2pts Attempts'] = scoreRows[index].find_all('td')[5].text
                        item['2pts Made'] = scoreRows[index].find_all('td')[4].text
                        item['3pts Attempts'] = scoreRows[index].find_all('td')[8].text
                        item['3pts Made'] = scoreRows[index].find_all('td')[7].text
                        item['Assists'] = scoreRows[index].find_all('td')[20].text
                        item['Block Shots'] = scoreRows[index].find_all('td')[16].text
                        item['Defensive rebounds'] = scoreRows[index].find_all('td')[14].text
                        item['FT Attempts'] = scoreRows[index].find_all('td')[11].text
                        item['FT Made'] = scoreRows[index].find_all('td')[10].text
                        item['Minutes played'] = scoreRows[index].find_all('td')[1].text
                        item['Offensive rebounds'] = scoreRows[index].find_all('td')[13].text
                        item['Personal fouls'] = scoreRows[index].find_all('td')[2].text
                        item['Points'] = scoreRows[index].find_all('td')[0].text
                        item['Steals'] = scoreRows[index].find_all('td')[19].text
                        item['Total rebounds'] = scoreRows[index].find_all('td')[15].text
                        item['Turnovers'] = scoreRows[index].find_all('td')[18].text

                        stat['items'] = item
                        info['stats'].append(stat)
                    # Visitor
                    playerPart = tables[1].table.tbody
                    scorePart = tables[1].find('td', class_='table-right')

                    playerRows = playerPart.find('tbody').find_all('tr')
                    scoreRows = scorePart.find('tbody').find_all('tr')

                    for index in range(len(playerRows)-1):
                        stat = {}
                        stat['team'] = info['visitorTeam']['extid']

                        if index == len(playerRows) - 2:
                            stat['player_extid'] = 'team'
                            stat['player_firstname'] = ''
                            stat['player_lastname'] = '- TEAM -'
                            stat['player_name'] = '- TEAM -'
                        else:
                            stat['player_firstname'] = playerRows[index].find('a').text.split(' ')[0]
                            stat['player_lastname'] = playerRows[index].find('a').text.split(' ')[1]
                            stat['player_name'] = f'{stat["player_lastname"]} {stat["player_firstname"]}'
                            stat['player_extid'] = playerRows[index].find('a')['href'].split('/')[3]

                        item = {}
                        item['2pts Attempts'] = scoreRows[index].find_all('td')[5].text
                        item['2pts Made'] = scoreRows[index].find_all('td')[4].text
                        item['3pts Attempts'] = scoreRows[index].find_all('td')[8].text
                        item['3pts Made'] = scoreRows[index].find_all('td')[7].text
                        item['Assists'] = scoreRows[index].find_all('td')[20].text
                        item['Block Shots'] = scoreRows[index].find_all('td')[16].text
                        item['Defensive rebounds'] = scoreRows[index].find_all('td')[14].text
                        item['FT Attempts'] = scoreRows[index].find_all('td')[11].text
                        item['FT Made'] = scoreRows[index].find_all('td')[10].text
                        item['Minutes played'] = scoreRows[index].find_all('td')[1].text
                        item['Offensive rebounds'] = scoreRows[index].find_all('td')[13].text
                        item['Personal fouls'] = scoreRows[index].find_all('td')[2].text
                        item['Points'] = scoreRows[index].find_all('td')[0].text
                        item['Steals'] = scoreRows[index].find_all('td')[19].text
                        item['Total rebounds'] = scoreRows[index].find_all('td')[15].text
                        item['Turnovers'] = scoreRows[index].find_all('td')[18].text

                        stat['items'] = item
                        info['stats'].append(stat)
                
            return info
        return {'error': 'Something went wrong!'}
    elif args['f'] == 'player':
        args['extid'] = request.args.get('extid')

        response = requests.get(f'https://www.legapallacanestro.com/giocatore/wp/{args["extid"]}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            info = {}
            info['extid'] = args['extid']
            info['team'] = soup.find('div', class_='player-info-row2').find_all('li')[4].find('span', class_='spec-value').text
            info['dateOfBirth'] = datetime.strptime(soup.find('div', class_='player-info-row2').find_all('li')[0].find('span', class_='spec-value').text, '%d/%m/%Y').strftime('%Y-%m-%d')
            info['shirtNumber'] = soup.find('div', class_='num-maglia').text
            info['firstname'] = soup.find('div', class_='player-name').text.split(' ')[1]
            info['lastname'] = soup.find('div', class_='player-name').text.split(' ')[0]
            info['name'] = f'{info["firstname"]} {info["lastname"]}'
            info['height'] = soup.find('div', class_='player-info-row2').find_all('li')[2].find('span', class_='spec-value').text.replace('cm', '').strip()
            info['weight'] = soup.find('div', class_='player-info-row2').find_all('li')[3].find('span', class_='spec-value').text.replace('kg', '').strip()
            info['nationality'] = soup.find('div', class_='player-info-row2').find_all('li')[1].find('span', class_='spec-value').text
            info['position'] = soup.find('div', class_='ruolo').text
            info['source'] = response.url

            return info
        return {'error': 'Something went wrong!'}
    else:
        return {'error': 'Something went wrong!'}
