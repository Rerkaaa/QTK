from dotenv import load_dotenv
import os
import requests
import pandas as pd
import pygsheets
import time
import re

load_dotenv()

api_key = "RGAPI-a76bbb3e-4659-4021-b035-f0845041d3ed"

service_account = pygsheets.authorize(service_file='JSONS\\spreadsheet-automator-475823-5c8c84bc15e3.json')

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
    response = requests.get(root_url + endpoint_url + f'?api_key={api_key}')
    return response.json()

def process_match_json(match_json, puuid):
    metadata = match_json['metadata']
    info = match_json['info']
    players = info['participants']
    participants = metadata['participants']
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

    barons_killed = player.get('baronKills', 0)  # Safely get with default
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

players = {
    'gingii': '-RPH9IeTdhsXIIlsN4nzUMr73O04IqK_eeLiyKGUtd2cO5kM9jHvBZgeAaU-TATkh_EAjAo-qVHDLA',
    'moldrn': 'JDyvcgSiNxveLcmmbonQfiX15t_85UKaRjWAerymavmnWtYXPPqW328TJgzHP9kLVKBpMEHcLMs06A',
    'frozen': 'kjjaoPkm0xC9OOmydAb6E_ppk1Xyt_BxXdiR_VBMHzQB0IMhH3uHhQHamFUKZe-nItJE3OseV_Qj0g',
    'messefy': '2SesTfJYPDy2DWBeZhvgc2JoE2VxpbzMnGHxH-88JBKm7uhscdPmq0zvBHN7fUTsekdiQOL11jlIpA',
    'vaxerdj': '5-yu7_qiMBXJER-q-X08761VGYmPNn4ibZL46avwbBdtpuM8cNm6gKZWY6BbcBTn4lbRS5s2S6SYDg'
}

def fetch_last_matches(puuid, region, queue=420):
    """
    Fetches the last 20 matches for a given player and returns a concatenated DataFrame.
    
    Parameters:
    - puuid (str): The player's PUUID.
    - region (str): The region (e.g., 'europe').
    - queue (int): The queue type (default is 420 for ranked solo/duo).
    
    Returns:
    - pd.DataFrame: Concatenated DataFrame of match data.
    """
    match_ids = get_match_history(puuid=puuid, region=region, queue=queue)
    df = pd.DataFrame()
    for match_id in match_ids:
        game = get_match_data_from_id(matchId=match_id, region=region)
        match_df = process_match_json(game, puuid=puuid)
        df = pd.concat([df, match_df])
    return df

def get_rank(puuid=None, region='euw1'):
    root_url = f'https://{region}.api.riotgames.com'
    endpoint_url = f'/lol/league/v4/entries/by-puuid/{puuid}'
    response = requests.get(root_url + endpoint_url + f'?api_key={api_key}')
    if response.status_code != 200:
        raise ValueError(f"Failed to get rank data: {response.status_code} - {response.text}")
    return response.json()

def countdown(seconds):
    """
    Creates a countdown timer that prints the remaining seconds.
    """
    while seconds > 0:
        print(f"Time remaining: {seconds} seconds for api reset")
        time.sleep(1)
        seconds -= 1
    print("Proceeding!")

# Fetch matches for all players with rate limiting
df_matches = {}
df_matches['gingii'] = fetch_last_matches(puuid=players['gingii'], region='europe', queue=420)
df_matches['moldrn'] = fetch_last_matches(puuid=players['moldrn'], region='europe', queue=420)
countdown(60)
df_matches['frozen'] = fetch_last_matches(puuid=players['frozen'], region='europe', queue=420)
df_matches['messefy'] = fetch_last_matches(puuid=players['messefy'], region='europe', queue=420)
countdown(60)
df_matches['vaxerdj'] = fetch_last_matches(puuid=players['vaxerdj'], region='europe', queue=420)

def load_lol_data():
    """
    Loads League of Legends data from CommunityDragon resources, including JSON data and dictionaries for perks, items, champions, etc.
    
    Returns:
    - dict: A dictionary containing all fetched and processed data, including raw JSONs, ID-to-name mappings, and icon URLs.
    """
    
    # Base URL for all resources
    base_url = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/'

    # List of JSON URLs (only those ending in .json)
    json_urls = {
        'perks': base_url + 'perks.json',
        'perkstyles': base_url + 'perkstyles.json',
        'items': base_url + 'items.json',
        'queues': base_url + 'queues.json',
        'summoner_spells': base_url + 'summoner-spells.json',
        # Add this for champion IDs/names/icons (it's a summary JSON with all champions)
        'champion_summary': base_url + 'champion-summary.json'
    }

    # Directory URLs (for images; we'll handle via JSON paths instead)
    image_dirs = {
        'champ_icons': base_url + 'champion-icons/',
        'champions': base_url + 'champions/',  # For individual champion JSONs, not images; use IDs from summary to fetch specific if needed
        'perk_styles_img': base_url + 'perk-images/styles/',
        'perk_stat_img': base_url + 'perk-images/statmods/'
    }

    # Fetch and process only JSON URLs
    data_jsons = {}
    for name, url in json_urls.items():
        if url.endswith('.json'):
            response = requests.get(url)
            if response.status_code == 200:
                data_jsons[name] = response.json()
            else:
                print(f"Failed to fetch {name} from {url}: {response.status_code}")

    # Your json_extract function (unchanged)
    def json_extract(obj, key):
        arr = []
        
        def extract(obj, arr, key):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == key:
                        arr.append(v)
                    elif isinstance(v, (dict, list)):
                        extract(v, arr, key)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item, arr, key)
                    
            return arr
        
        values = extract(obj, arr, key)
        return values

    # Create dictionaries for JSONs that have extractable IDs/names (expand as needed)
    # Example for perks
    perk_dict = {}
    if 'perks' in data_jsons:
        perk_ids = json_extract(data_jsons['perks'], 'id')
        perk_names = json_extract(data_jsons['perks'], 'name')
        perk_dict = dict(map(lambda i, j: (int(i), j), perk_ids, perk_names))

    # Example for perkstyles (note: IDs/names are under 'styles' key, but json_extract finds them recursively)
    perk_styles_dict = {}
    if 'perkstyles' in data_jsons:
        perk_styles_ids = json_extract(data_jsons['perkstyles'], 'id')
        perk_styles_names = json_extract(data_jsons['perkstyles'], 'name')
        perk_styles_dict = dict(map(lambda i, j: (int(i), j), perk_styles_ids, perk_styles_names))

    # For items (list of dicts with 'id' and 'name')
    item_dict = {}
    if 'items' in data_jsons:
        item_dict = {entry['id']: entry['name'] for entry in data_jsons['items'] if 'id' in entry and 'name' in entry}

    # For champions (list of dicts with 'id' and 'name')
    champ_dict = {}
    if 'champion_summary' in data_jsons:
        champ_dict = {entry['id']: entry['name'] for entry in data_jsons['champion_summary'] if 'id' in entry and 'name' in entry}

    # For summoner spells (list of dicts with 'id' and 'name')
    summoner_dict = {}
    if 'summoner_spells' in data_jsons:
        summoner_dict = {entry['id']: entry['name'] for entry in data_jsons['summoner_spells'] if 'id' in entry and 'name' in entry}

    # For queues, it's a dict of str(queueId): obj with 'description', etc. – adjust extraction if needed
    queue_dict = {}
    if 'queues' in data_jsons:
        queue_dict = {entry['id']: entry['description'] for entry in data_jsons['queues'] if 'id' in entry and 'description' in entry}

    # Handling images (from JSON iconPaths instead of directories)
    # Base for constructing full image URLs
    image_base = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default'

    # For champion icons (from champion-summary.json)
    champ_icon_dict = {}  # id: full_image_url
    if 'champion_summary' in data_jsons:
        for champ in data_jsons['champion_summary']:
            if 'id' in champ and 'squarePortraitPath' in champ:
                champ_id = champ['id']
                rel_path = champ['squarePortraitPath']
                full_url = image_base + rel_path
                champ_icon_dict[champ_id] = full_url

    # For perk images (including keystones and regular perks; from perks.json)
    perk_icon_dict = {}  # id: full_image_url
    if 'perks' in data_jsons:
        for perk in data_jsons['perks']:
            if 'id' in perk and 'iconPath' in perk:
                perk_id = perk['id']
                rel_path = perk['iconPath']
                full_url = image_base + rel_path
                perk_icon_dict[perk_id] = full_url

    # For stat mod images (stat shards are special perks with IDs 5001-5013; also from perks.json)
    stat_icon_dict = {}  # id: full_image_url
    if 'perks' in data_jsons:
        for perk in data_jsons['perks']:
            if 'id' in perk and str(perk['id']).startswith('50') and 'iconPath' in perk:  # Filter for 500x IDs
                stat_id = perk['id']
                rel_path = perk['iconPath']
                full_url = image_base + rel_path
                stat_icon_dict[stat_id] = full_url

    # For perk style images (from perkstyles.json)
    style_icon_dict = {}  # id: full_image_url
    if 'perkstyles' in data_jsons:
        for style in data_jsons['perkstyles']['styles']:
            if 'id' in style and 'iconPath' in style:
                style_id = style['id']
                rel_path = style['iconPath']
                full_url = image_base + rel_path
                style_icon_dict[style_id] = full_url

    # If you REALLY need to list files from an image directory (e.g., if JSON paths are insufficient), here's how:
    # Example for champ_icons directory (fetches HTML listing, extracts .png links with regex)
    def list_dir_files(dir_url):
        response = requests.get(dir_url)
        if response.status_code == 200:
            text = response.text
            # Extract <a href="...png"> links (assumes Apache-style HTML listing)
            files = re.findall(r'<a href="([^"]+\.png)">', text)
            return files
        else:
            print(f"Failed to list {dir_url}: {response.status_code}")
            return []

    return {
        'data_jsons': data_jsons,
        'perk_dict': perk_dict,
        'perk_styles_dict': perk_styles_dict,
        'item_dict': item_dict,
        'champ_dict': champ_dict,
        'summoner_dict': summoner_dict,
        'queue_dict': queue_dict,
        'champ_icon_dict': champ_icon_dict,
        'perk_icon_dict': perk_icon_dict,
        'stat_icon_dict': stat_icon_dict,
        'style_icon_dict': style_icon_dict,
        'image_dirs': image_dirs,
        'list_dir_files': list_dir_files  # Include the helper function if needed
    }

lol_data = load_lol_data()
perk_dict = lol_data['perk_dict']
perk_styles_dict = lol_data['perk_styles_dict']
item_dict = lol_data['item_dict']
champ_dict = lol_data['champ_dict']
summoner_dict = lol_data['summoner_dict']

# Expanded list of all numerical/stat columns to protect/reverse (add any others from your df if missing)
protected_cols = [
    'game_creation', 'game_duration', 'game_start_timestamp', 'game_end_timestamp',
    'queue_id', 'champion_transform', 'champion_level', 'neutral_minions_killed',
    'total_minions_killed', 'total_ally_jungle_minions_killed', 'total_enemy_jungle_minions_killed',
    'objectives_stolen', 'objectives_stolen_assist', 'kills', 'deaths', 'assists',
    'gold_earned', 'gold_spent', 'total_damage_dealt', 'total_damage_taken',
    'total_heal', 'total_heals_on_teammates', 'total_time_cc_dealt', 'barons_killed',
    'wards_placed', 'wards_killed', 'vision_score', 'detector_wards_placed',
    'vision_wards_bought_in_game', 'turrets_lost', 'total_damage_shielded_on_teammates'
]

def apply_replacements(df, perk_dict, perk_styles_dict, item_dict, champ_dict, summoner_dict, protected_cols):
    pd.options.display.max_columns = 100

    # Replace IDs with names
    replacements = {
        'primary_style': perk_styles_dict,
        'secondary_style': perk_styles_dict,
        'primary_keystone': perk_dict,
        'primary_perk_1': perk_dict,
        'primary_perk_2': perk_dict,
        'primary_perk_3': perk_dict,
        'secondary_perk_1': perk_dict,
        'secondary_perk_2': perk_dict,
        'defense': perk_dict,
        'flex': perk_dict,
        'offense': perk_dict,
        'champion_id': champ_dict,
        'summoner1_id': summoner_dict,
        'summoner2_id': summoner_dict,
        'item0': item_dict,
        'item1': item_dict,
        'item2': item_dict,
        'item3': item_dict,
        'item4': item_dict,
        'item5': item_dict,
        'item6': item_dict
    }

    df = df.replace(replacements)

    # Ensure protected columns are numeric
    for col in protected_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col])

    return df

# Apply replacements to all match dataframes
for player in df_matches:
    df_matches[player] = apply_replacements(
        df_matches[player], perk_dict, perk_styles_dict, item_dict, champ_dict, summoner_dict, protected_cols
    )

# Upload match data to sheets (sheets 0-4 for gingii, moldrn, frozen, messefy, vaxerdj)
player_order = ['gingii', 'moldrn', 'frozen', 'messefy', 'vaxerdj']
for i, player in enumerate(player_order):
    wks = sheet[i]
    wks.set_dataframe(df_matches[player], start='A1', copy_head=True, fit=True)

def process_rank(rank_json):
    data = []
    for entry in rank_json:
        data.append({
            'leagueId': entry.get('leagueId'),
            'queueType': entry.get('queueType'),
            'tier': entry.get('tier'),
            'rank': entry.get('rank'),
            'puuid': entry.get('puuid'),
            'LP': entry.get('leaguePoints'),
            'wins': entry.get('wins'),
            'losses': entry.get('losses'),
        })
    return pd.DataFrame(data)

# Fetch and process ranks
df_ranks = {}
for player, puuid in players.items():
    rank_json = get_rank(puuid)
    df_ranks[player] = process_rank(rank_json)

# Upload rank data to sheets (sheets 5-9 for gingii, moldrn, frozen, messefy, vaxerdj)
for i, player in enumerate(player_order):
    wks = sheet[i + 5]
    wks.set_dataframe(df_ranks[player], start='A1', copy_index=False, copy_head=True)