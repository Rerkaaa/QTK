#MUST RUN FIRST
from dotenv import load_dotenv
import os
import requests
import pandas as pd
import pygsheets
import time
import asyncio

load_dotenv()

api_key = "RGAPI-a76bbb3e-4659-4021-b035-f0845041d3ed"
#print(api_key)

service_account = pygsheets.authorize(service_file='JSONS\spreadsheet-automator-475823-5c8c84bc15e3.json')

sheet = service_account.open_by_url('https://docs.google.com/spreadsheets/d/1rOsmVGBkR-1OcwmnIbIDt-J50JX0O0zHtIGGDKxOzmI/edit?usp=sharing')

def get_puuid(gameName=None, tagline=None, api_key=None):
    link = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagline}?api_key={api_key}'

    response = requests.get(link)

    return response.json()['puuid']

def get_name_and_tag(puuid=None, api_key=None):
    link = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}?api_key={api_key}'

    response = requests.get(link)
    
    gameName = response.json()['gameName']
    tagline = response.json()['tagLine']

    return f'{gameName}#{tagline}'

def get_ladder(top=None):

    root = 'https://euw1.api.riotgames.com/'
    chall = 'lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
    gm = 'lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5'
    master = 'lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5'


    chall_response = requests.get(root + chall + f'?api_key={api_key}')
    gm_response = requests.get(root + gm + f'?api_key={api_key}')
    master_response = requests.get(root + master + f'?api_key={api_key}')

    chall_df = pd.DataFrame(chall_response.json()['entries']).sort_values(by='leaguePoints', ascending=False).reset_index(drop=True)
    gm_df = pd.DataFrame(gm_response.json()['entries']).sort_values(by='leaguePoints', ascending=False).reset_index(drop=True)
    master_df = pd.DataFrame(master_response.json()['entries']).sort_values(by='leaguePoints', ascending=False).reset_index(drop=True)

    ladder = pd.concat([chall_df, gm_df, master_df]).reset_index(drop=True)[:top]
    ladder = ladder.drop(columns='rank').reset_index(drop=False).rename(columns={'index':'rank'})
    ladder['rank'] += 1
    
    return ladder

def get_match_history(puuid=None, region=None, start=0, count=20):
    
    root_url = f'https://{region}.api.riotgames.com'
    endpoint_url = f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
    query_params = f'?start={start}&count={count}'

    response = requests.get(root_url + endpoint_url + query_params + f'&api_key={api_key}')

    return response.json()

def get_match_data_from_id(matchId=None, region=None):
    root_url = f'https://{region}.api.riotgames.com'
    endpoint_url = f'/lol/match/v5/matches/{matchId}'

    response = requests.get(root_url + endpoint_url + f'?api_key={api_key}')

    return response.json()

def get_match_history(puuid=None, region=None, start=0, count=20, queue=None):
    
    root_url = f'https://{region}.api.riotgames.com'
    endpoint_url = f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
    query_params = f'?start={start}&count={count}'
    
    if queue is not None:
        query_params += f'&queue={queue}'

    response = requests.get(root_url + endpoint_url + query_params + f'&api_key={api_key}')

    return response.json()

def get_match_data_from_id(matchId=None, region=None):
    
    root_url = f'https://{region}.api.riotgames.com'
    endpoint_url = f'/lol/match/v5/matches/{matchId}'
    print(root_url + endpoint_url + f'?api_key={api_key}')
    response = requests.get(root_url + endpoint_url + f'?api_key={api_key}')

    return response.json()

def process_match_json(match_json, puuid):
    ##Architecture
    metadata = match_json['metadata']
    info = match_json['info']
    players = info['participants']
    participants = metadata['participants']
    teams = info['teams']
    player = players[participants.index(puuid)]
    perks = player['perks']
    stats = perks['statPerks']
    styles = perks['styles']
    

    primary = styles[0]
    secondary = styles[1]
    
    side_dict = {
        100: 'blue',
        200: 'red'
    }

    #information
    match_id = metadata['matchId']

    game_creation = info['gameCreation']
    game_duration = info['gameDuration']
    game_start_timestamp = info['gameStartTimestamp']
    game_end_timestamp = info['gameEndTimestamp']
    patch = info['gameVersion']
    game_mode = info['gameMode']
    game_type = info['gameType']
    queue_id = info['queueId']

    riot_id = player['riotIdGameName']
    riot_tag = player['riotIdTagline']
    summoner_id = player['summonerId']
    summoner_name = player['summonerName']
    
    side = side_dict[player['teamId']]
    win = player['win']

    champ_id = player['championId']
    champ_transform = player['championTransform']
    champ_level = player['champLevel']
    team_position = player['teamPosition']
    
    gold_earned = player['goldEarned']
    gold_spent = player['goldSpent']
    neutral_minions_killed = player['neutralMinionsKilled']
    total_minions_killed = player['totalMinionsKilled']
    total_ally_jungle_minions_killed = player['totalAllyJungleMinionsKilled']
    total_enemy_jungle_minions_killed = player['totalEnemyJungleMinionsKilled']
    
    kills = player['kills']
    deaths = player['deaths']
    assists = player['assists']
    first_blood = player['firstBloodKill']
    
    total_damage_dealt = player['totalDamageDealtToChampions']
    total_damage_shielded_on_teammates = player['totalDamageShieldedOnTeammates']
    total_damage_taken = player['totalDamageTaken']
    total_heal = player['totalHeal']
    total_heals_on_teammates = player['totalHealsOnTeammates']
    total_time_cc_dealt = player['totalTimeCCDealt']
    
    barons_killed = player['baronKills']
    turrets_lost = player['turretsLost']
    objectives_stolen = player['objectivesStolen']
    objectives_stolen_assist = player['objectivesStolenAssists']

    early_surrender = player['gameEndedInEarlySurrender']
    surrender = player['gameEndedInSurrender']

    item0 = player['item0']
    item1 = player['item1']
    item2 = player['item2']
    item3 = player['item3']
    item4 = player['item4']
    item5 = player['item5']
    item6 = player['item6']
    
    summoner1_id = player['summoner1Id']
    summoner2_id = player['summoner2Id']
    
    wards_placed = player['wardsPlaced']
    wards_killed = player['wardsKilled']
    vision_score = player['visionScore']
    detector_wards_placed = player['detectorWardsPlaced']

    defense = stats['defense']
    flex = stats['flex']
    offense = stats['offense']

    ##what is this
    role = player['role']
    vision_wards_bought_in_game = player['visionWardsBoughtInGame']

    primary_style = primary['style']
    secondary_style = secondary['style']

    primary_keystone = primary['selections'][0]['perk']
    primary_perk_1 = primary['selections'][1]['perk']
    primary_perk_2 = primary['selections'][2]['perk']
    primary_perk_3 = primary['selections'][3]['perk']

    secondary_perk_1 = secondary['selections'][0]['perk']
    secondary_perk_2 = secondary['selections'][1]['perk']

    #need to implement bans

    matchDF = pd.DataFrame({
        'match_id': [match_id],
        'game_creation': [game_creation],
        'game_duration': [game_duration],
        'game_start_timestamp': [game_start_timestamp],
        'game_end_timestamp': [game_end_timestamp],
        'patch': [patch],
        'game_mode': [game_mode],
        'game_type': [game_type],
        'queue_id': [queue_id],
        'riot_id': [riot_id],
        'riot_tag': [riot_tag],
        'summoner_id': [summoner_id],
        'summoner_name': [summoner_name],
        'side': [side],
        'win': [win],
        'puuid': [puuid],
        'champion_id': [champ_id],
        'champion_transform': [champ_transform],
        'champion_level': [champ_level],
        'team_position': [team_position],
        'item0': [item0],
        'item1': [item1],
        'item2': [item2],
        'item3': [item3],
        'item4': [item4],
        'item5': [item5],
        'item6': [item6],
        'summoner1_id': [summoner1_id],
        'summoner2_id': [summoner2_id],
        'neutral_minions_killed': [neutral_minions_killed],
        'total_minions_killed': [total_minions_killed],
        'total_ally_jungle_minions_killed': [total_ally_jungle_minions_killed],
        'total_enemy_jungle_minions_killed': [total_enemy_jungle_minions_killed],
        'objectives_stolen': [objectives_stolen],
        'objectives_stolen_assist': [objectives_stolen_assist],
        'kills': [kills],
        'deaths': [deaths],
        'assists': [assists],
        'gold_earned': [gold_earned],
        'gold_spent': [gold_spent],
        'total_damage_dealt': [total_damage_dealt],
        'total_damage_taken': [total_damage_taken],
        'total_heal': [total_heal],
        'total_heals_on_teammates': [total_heals_on_teammates],
        'total_time_cc_dealt': [total_time_cc_dealt],
        'barons_killed': [barons_killed],
        'first_blood': [first_blood],
        'early_surrender': [early_surrender],
        'surrender': [surrender],
        'wards_placed': [wards_placed],
        'wards_killed': [wards_killed],
        'vision_score': [vision_score],
        'detector_wards_placed': [detector_wards_placed],
        'role': [role],
        'vision_wards_bought_in_game': [vision_wards_bought_in_game],
        'primary_style': [primary_style],
        'secondary_style': [secondary_style],
        'primary_keystone': [primary_keystone],
        'primary_perk_1': [primary_perk_1],
        'primary_perk_2': [primary_perk_2],
        'primary_perk_3': [primary_perk_3],
        'secondary_perk_1': [secondary_perk_1],
        'secondary_perk_2': [secondary_perk_2],
        'defense': [defense],
        'flex': [flex],
        'offense': [offense],
        'turrets_lost': [turrets_lost],
        'total_damage_shielded_on_teammates': [total_damage_shielded_on_teammates],
    })
    return matchDF

# Get PUUID
#print("Gingii puuid >>", get_puuid(gameName='Robb Stark', tagline='444', api_key=api_key))
#print("Moldrn puuid >>", get_puuid(gameName='2018 Ame', tagline='PSG', api_key=api_key))
#print("Frozen puuid >>", get_puuid(gameName='TwInkMage', tagline='QTK', api_key=api_key))
#print("Messefy puuid >>", get_puuid(gameName='messefy', tagline='6969', api_key=api_key))
#print("VaxerDJ puuid >>", get_puuid(gameName='I love Alt girls', tagline='Love', api_key=api_key))