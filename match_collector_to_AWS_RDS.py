# Official documentation: https://wiki.teamfortress.com/wiki/WebAPI/GetMatchDetails
#                         http://dev.dota2.com/showthread.php?t=47115
#                         https://developer.valvesoftware.com/wiki/Steam_Web_API
# Dota API documentation: https://dota2api.readthedocs.io/en/latest/responses.html#get-match-details
# Another INTRO: http://sharonkuo.me/dota2/index.html

# Example API URLS:
# 1. Match Detail:
# https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/?match_id=3375310016&key=
# 2. GetMatchHistoryBySequnceNum
# https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/?skill=2&key={{APIKey}}&start_at_match_seq_num=2670059633&matches_requested=1
# 3. GetMatchHistory
# https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/V001/?skill=2&key={{APIKey}}&start_at_match_seq_num=2670059633&matches_requested=100
# 4. Player Summary
# http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={{APIKey}}&steamids=76561198047111308

# Example OpenDOTA API URLS:
# 1. Match Detail:
# https://api.opendota.com/api/matches/3057701293
#

# To get heroes img url:
# api = dota2api.Initialise(APIKey)
# heroes = api.get_heroes()

#### HEROES ####
# primary_attr: '0'=str, '1'=agi, '2'=int
# roles: from least to most significant digit:
# ['Carry', 'Disabler', 'Initiator', 'Jungler', 'Support', 'Durable', 'Nuker', 'Pusher', 'Escape']
#┌──┬──┬──┬──┬──┬──┬──────────────────────────── Not used.
#│  │  │  │  │  │  │
#│  │  │  │  │  │  │  ┌───────────────────────── Escape
#│  │  │  │  │  │  │  │  ┌────────────────────── Pusher
#│  │  │  │  │  │  │  │  │  ┌─────────────────── Nuker
#│  │  │  │  │  │  │  │  │  │  ┌──────────────── Durable
#│  │  │  │  │  │  │  │  │  │  │  ┌───────────── Support
#│  │  │  │  │  │  │  │  │  │  │  │  ┌────────── Jungler
#│  │  │  │  │  │  │  │  │  │  │  │  │  ┌─────── Initiator
#│  │  │  │  │  │  │  │  │  │  │  │  │  │  ┌──── Disabler
#│  │  │  │  │  │  │  │  │  │  │  │  │  │  │  ┌─ Carry
#│  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
#00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00



import psycopg2
import os
import time
import json
import requests
from time import localtime, strftime
from collections import OrderedDict

#############
# CONSTANTS #
#############

TIME_TO_SLEEP = 0.05         # In seconds.

LOCALDB = {"dbname":"dotaoracle", "user":"postgres", "password":os.environ['DATABASE_PASSWORD'], "port":5432}
RDSDB = {"dbname":"dotamatchesdb", "user":os.environ['DATABASE_USER'], "password":os.environ['TRIPFLASKDB_PASSWORD'], "port":5432}
WORKINGDB = LOCALDB     # Change this line if other DB is to be used.

D2APIKEY = os.environ['D2_API_KEY']
STEAMAPI_GETMATCHHISTORY_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/V001/"
STEAMAPI_GETMATCHDETAILS_URL = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/"
STEAMAPI_GETMATCHHISTORYBYSEQUENCENUM = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/"
OPENDOTA_GETMATCHDETAILS_URL = "https://api.opendota.com/api/matches/"
OPENDOTA_GETPLAYERINFO_URL = "https://api.opendota.com/api/players/"


STARTING_SEQ_NUM = "{{STARTING_SEQ_NUM}}"


MIN_DURATION = 600                      # in seconds
CYCLES = 20000
COUNT = 1

####################
#    DB Schema     #
####################

players         =   """players(
                            account_id              VARCHAR(100)     PRIMARY KEY,
                            personaname             VARCHAR(50),
                            avatar_full             TEXT,
                            profile_url             TEXT,
                            loccountrycode          VARCHAR(8),
                            party_mmr               SMALLINT,
                            solo_mmr                SMALLINT,
                            mmr_estimate            SMALLINT
                            )
                    """

heroes          =   """heroes(
                            hero_id                 SMALLINT        PRIMARY KEY,
                            long_name               VARCHAR(255),
                            localized_name          VARCHAR(40),
                            primary_attr            CHAR(15),
                            attack_type             VARCHAR(8),
                            roles                   INTEGER,
                            url_full_portrait       VARCHAR(255),
                            url_large_portrait      VARCHAR(255),
                            url_small_portrait      VARCHAR(255),
                            url_vertical_portrait   VARCHAR(255),
                            base_health             SMALLINT,
                            base_health_regen       NUMERIC(4,2),
                            base_mana               SMALLINT,
                            base_mana_regen         NUMERIC(4,2),
                            base_armor              SMALLINT,
                            base_mr                 INTEGER,
                            base_attack_min         INTEGER,
                            base_attack_max         INTEGER,
                            base_str                SMALLINT,
                            base_agi                SMALLINT,
                            base_int                SMALLINT,
                            str_gain                NUMERIC(3,1),
                            agi_gain                NUMERIC(3,1),
                            int_gain                NUMERIC(3,1),
                            attack_range            SMALLINT,
                            projectile_speed        INTEGER,
                            attack_rate             NUMERIC(3,1),
                            move_speed              SMALLINT,
                            turn_rate               NUMERIC(3,1),
                            cm_enabled              BOOLEAN,
                            legs                    SMALLINT
                    )"""

#hero_roles       =  """hero_roles(
#                            role_id                 SERIAL          PRIMARY KEY,
#                            role_name               VARCHAR(12)
#                    )"""

hero_abilities =  """hero_abilities(
                            ability_id              SMALLINT        PRIMARY KEY,
                            long_name               VARCHAR(400),
                            dname                   VARCHAR(400),
                            behavior                VARCHAR(15),
                            dmg_type                VARCHAR(15),
                            bkbpierce               BOOLEAN,
                            description             TEXT,
                            img_url                 VARCHAR(255)

                    )"""

items            =  """items(
                            item_id                 SMALLINT        PRIMARY KEY,
                            img_url                 VARCHAR(255),
                            long_name               VARCHAR(40),
                            dname                   VARCHAR(40),
                            qual                    VARCHAR(15),
                            gold_cost               SMALLINT,
                            description             TEXT,
                            notes                   TEXT,
                            mana_cost               SMALLINT,
                            cd                      SMALLINT,
                            lore                    TEXT,
                            created                 BOOLEAN
                    )"""

leagues          =  """leagues(
                            league_id               INTEGER         PRIMARY KEY,
                            tier                    VARCHAR(20),
                            league_name             TEXT
                    )"""

teams            =  """teams(
                            team_id                 INTEGER         PRIMARY KEY,
                            team_name               TEXT,
                            tag                     TEXT
                    )"""

matches          =  """matches(
                            match_id                VARCHAR(100)    PRIMARY KEY,
                            match_seq_num           VARCHAR(100),
                            start_time              TIMESTAMP NOT NULL,
                            cluster_id              SMALLINT,
                            region_id               SMALLINT,
                            skill                   CHAR(1),
                            radiant_win             BOOLEAN,
                            radiant_heroes          SMALLINT[],
                            dire_heroes             SMALLINT[],
                            duration                SMALLINT,
                            lobby_type              SMALLINT,
                            game_mode               SMALLINT,
                            first_blood_time        INTEGER,
                            tower_status_radiant    SMALLINT,
                            tower_status_dire       SMALLINT,
                            barracks_status_radiant SMALLINT,
                            barracks_status_dire    SMALLINT,
                            radiant_score           SMALLINT,
                            dire_score              SMALLINT,

                            is_parsed               BOOLEAN,
                            times                   SMALLINT[],
                            radiant_gold_adv        INT[],
                            radiant_xp_adv          INT[],

                            league_id               SMALLINT
                                                    REFERENCES leagues(league_id)
                                                    ON UPDATE CASCADE,
                            radiant_team_id         INTEGER
                                                    REFERENCES teams(team_id)
                                                    ON UPDATE CASCADE,
                            dire_team_id            INTEGER
                                                    REFERENCES teams(team_id)
                                                    ON UPDATE CASCADE
                    )"""

# picks_bans is recorded for matches with leagueid > 0 && game_mode == 2
picks_bans       =  """picks_bans(
                           match_id                VARCHAR(100)
                                                   REFERENCES matches (match_id)
                                                   ON UPDATE CASCADE
                                                   ON DELETE CASCADE,
                           league_id               INTEGER
                                                   REFERENCES leagues(league_id)
                                                   ON UPDATE CASCADE,
                           the_order               SMALLINT,
                           team_radiant            BOOLEAN,
                           is_pick                 BOOLEAN,
                           hero_id                 SMALLINT,
                           CONSTRAINT picks_bans_pkey
                               PRIMARY KEY (match_id, the_order)

                   )"""

# objectives valid when the game is_parsed.
objectives      =   """(
                            match_id                VARCHAR(100)
                                                    REFERENCES matches (match_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,
                            time                    SMALLINT,
                            type                    TEXT,
                            unit                    TEXT,
                            key                     TEXT
                    )"""

match_player_pairs  = """match_player_pairs(
                            match_id                VARCHAR(100)
                                                    REFERENCES matches (match_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,

                            hero_id                 SMALLINT
                                                    REFERENCES heroes (hero_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,

                            account_id              VARCHAR(100)
                                                    REFERENCES players (account_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,
                            is_parsed               BOOLEAN,
                            team_radiant            BOOLEAN,
                            radiant_win             BOOLEAN,
                            player_slot             SMALLINT,
                            item_0                  SMALLINT,
                            item_1                  SMALLINT,
                            item_2                  SMALLINT,
                            item_3                  SMALLINT,
                            item_4                  SMALLINT,
                            item_5                  SMALLINT,
                            backpack_0              SMALLINT,
                            backpack_1              SMALLINT,
                            backpack_2              SMALLINT,
                            ability_upgrades_arr    SMALLINT[],
                            kills                   SMALLINT,
                            deaths                  SMALLINT,
                            assists                 SMALLINT,
                            leaver_status           SMALLINT,
                            last_hits               SMALLINT,
                            denies                  SMALLINT,
                            gold_per_min            SMALLINT,
                            xp_per_min              SMALLINT,
                            final_level             SMALLINT,
                            hero_damage             INT,
                            tower_damage            INT,
                            hero_healing            INT,
                            gold                    INT,
                            gold_spent              INT,

                            gold_t                  INT[],
                            xp_t                    INT[],
                            lane_pos                SMALLINT[][],
                            lane                    SMALLINT,
                            lane_role               SMALLINT,
                            is_roaming              BOOLEAN,
                            purchase_ward_observer  SMALLINT,
                            purchase_ward_sentry    SMALLINT,
                            purchase_tpscroll       SMALLINT,
                            purchase_gem            SMALLINT,

                            CONSTRAINT match_player_pkey
                                PRIMARY KEY (match_id, player_slot)
                    )"""
                    # Fields being considered to add: item_uses, killed_by,

purchase_log     =  """purchase_log(
                            match_id                VARCHAR(100)
                                                    REFERENCES matches (match_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,
                            player_slot             SMALLINT,
                            hero_id                 SMALLINT
                                                    REFERENCES heroes (hero_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,
                            radiant_win             BOOLEAN,
                            time                    SMALLINT,
                            item                    SMALLINT
                                                    REFERENCES items(item_id)
                                                    ON UPDATE CASCADE
                    )"""

obs_log          =  """obs_log(
                            match_id                VARCHAR(100)
                                                    REFERENCES matches (match_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,
                            account_id              VARCHAR(100)
                                                    REFERENCES players (account_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,

                            player_slot             SMALLINT,
                            time                    SMALLINT,
                            x                       SMALLINT,
                            y                       SMALLINT,
                            z                       SMALLINT
                    )"""

sen_log          =  """sen_log(
                            match_id                VARCHAR(100)
                                                    REFERENCES matches (match_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,
                            account_id              VARCHAR(100)
                                                    REFERENCES players (account_id)
                                                    ON UPDATE CASCADE
                                                    ON DELETE CASCADE,

                            player_slot             SMALLINT,
                            time                    SMALLINT,
                            x                       SMALLINT,
                            y                       SMALLINT,
                            z                       SMALLINT
                    )"""

# ability_upgrades =  """ability_upgrades(
#                             ability_upgrades_id     SERIAL      PRIMARY KEY,
#                             ability_id              SMALLINT
#                                                     REFERENCES hero_abilities(ability_id),
#                             match_id                VARCHAR(255)
#                                                     REFERENCES matches(match_id),
#                             hero_id                 SMALLINT,
#                             hero_level              SMALLINT,
#                             time_since              SMALLINT,
#                             CONSTRAINT ability_upgrades_match_hero_pair_fkey
#                             	FOREIGN KEY (match_id, hero_id)
#                             	REFERENCES match_hero_pair (match_id, hero_id)
#                             	ON DELETE CASCADE
#                      )"""

TABLE_NAMES = ['players', 'heroes', 'hero_abilities', 'items', 'leagues', 'teams', 'matches', \
                'picks_bans', 'match_player_pairs', 'purchase_log', 'obs_log', 'sen_log']
TABLES_SCHEMA = [players, heroes, hero_abilities, items, leagues, teams, matches, \
                    picks_bans, match_player_pairs, purchase_log, obs_log, sen_log]

###################
# CONNECT TO RDS  #
###################

#conn = psycopg2.connect(dbname="dotamatchesdb",
#                        user=os.environ['DATABASE_USER'],
#                        password=os.environ['TRIPFLASKDB_PASSWORD'],
#                        host="dotaoracledb.ccpa4e4vnolm.us-east-2.rds.amazonaws.com",
#                        port= 5432)
#
##### Local PostgreSQL DB ####
#conn = psycopg2.connect(dbname="dotaoracle",
#                        user="postgres",
#                        password=os.environ['DATABASE_PASSWORD'],
#                        port=5432)
#cur = conn.cursor()

# Check all the tables in the database.
def check_all_table_names():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    cur.execute("""SELECT table_name FROM information_schema.tables
           WHERE table_schema = 'public'""")
    for table in cur.fetchall():
        print(table)

    cur.close()
    conn.close()

#######################
# Create tables in DB #
#######################

def drop_all_tables():
    # Drop all tables.
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

#    for table in TABLE_NAMES:
#        cur.execute("DROP TABLE IF EXISTS "+table+"CASCADE")

#    Ref: https://stackoverflow.com/a/21247009/6768084
    cur.execute("""
                    DROP SCHEMA public CASCADE;
                    CREATE SCHEMA public;
                    GRANT ALL ON SCHEMA public TO postgres;
                    GRANT ALL ON SCHEMA public TO public;
                    COMMENT ON SCHEMA public IS 'standard public schema';
                """)

    conn.commit()
    cur.close()
    conn.close()

def create_tables():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    for table in TABLES_SCHEMA:
        cur.execute("CREATE TABLE "+table)

    # cur.execute("CREATE TABLE "+players)
    # cur.execute("CREATE TABLE "+heroes)
    # cur.execute("CREATE TABLE "+hero_abilities)
    # cur.execute("CREATE TABLE "+items)
    # cur.execute("CREATE TABLE "+leagues)
    # cur.execute("CREATE TABLE "+teams)
    # cur.execute("CREATE TABLE "+matches)
    # cur.execute("CREATE TABLE "+picks_bans)
    # cur.execute("CREATE TABLE "+match_player_pairs)
    # cur.execute("CREATE TABLE "+purchase_log)
    # cur.execute("CREATE TABLE "+obs_log)
    # cur.execute("CREATE TABLE "+sen_log)

    conn.commit()
    cur.close()
    conn.close()

##############################################################
# Convert dota2_constants json files to dict and dump to DB. #
#                       SAVE CONSTANTS                       #
##############################################################

CUR_WORKING_DIR = os.getcwd()
CONSTANT_FILES_PATH = os.path.join(os.getcwd(), "data", "dotaconstants-master", "dotaconstants-master", "build")

def save_constants():
    save_heroes()
    save_hero_abilities()
    save_items()
    init_leagues()
    save_leagues()
    save_teams()

### Save heroes
def save_heroes():
    HERO_ROLES_LIST = ["Carry", "Disabler", "Initiator", "Jungler", "Support", "Durable", "Nuker", "Pusher", "Escape"]
    IMG_URL_PREFIX = "http://cdn.dota2.com/apps/dota2/images/heroes/"

    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    with open(os.path.join(CONSTANT_FILES_PATH,'heroes.json')) as data_file:
        data_all = json.load(data_file, object_pairs_hook=OrderedDict)
        for key, data in data_all.items():
            hero_name = data['name'][14:]
            IMG_URL_ = IMG_URL_PREFIX + hero_name + "_"

            roles_value = 0
            for role in data["roles"]:
                roles_value |= 1 << (HERO_ROLES_LIST.index(role)*2)

            sql_string =    "INSERT INTO heroes(hero_id, long_name, localized_name, primary_attr, " + \
                            "attack_type, roles, url_small_portrait, url_large_portrait, " + \
                            "url_full_portrait, url_vertical_portrait, base_health, " + \
                            "base_health_regen, base_mana, base_mana_regen, base_armor, base_mr, base_attack_min, " +\
                            "base_attack_max, base_str, base_agi, base_int, str_gain, agi_gain, int_gain, attack_range, " +\
                            "projectile_speed, attack_rate, move_speed, turn_rate, cm_enabled, legs) " +\
                            "VALUES (" + "%s, "*30 + "%s)"
            values = (data['id'], data['name'], data['localized_name'], data['primary_attr'], data['attack_type'], \
                    roles_value, IMG_URL_+"sb.png", IMG_URL_+"lg.png", IMG_URL_+"full.png", IMG_URL_+"vert.jpg", \
                    data['base_health'], data['base_health_regen'], data['base_mana'], data['base_mana_regen'], \
                    data['base_armor'], data['base_mr'], data['base_attack_min'], data['base_attack_max'], \
                    data['base_str'], data['base_agi'], data['base_int'], data['str_gain'], data['agi_gain'], \
                    data['int_gain'], data['attack_range'], data['projectile_speed'], data['attack_rate'], \
                    data['move_speed'], data['turn_rate'], data['cm_enabled'], data['legs'])

            cur.execute(sql_string, values)

    conn.commit()
    cur.close()
    conn.close()

### Save hero_abilities
def save_hero_abilities():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    # 1. Store ability_ids
    with open(os.path.join(CONSTANT_FILES_PATH,'ability_ids.json')) as data_file:
        data_all = json.load(data_file, object_pairs_hook=OrderedDict)
        for key, data in data_all.items():
            sql_string = "INSERT INTO hero_abilities(ability_id, long_name) VALUES (%s, %s)"
            values = (key, data)

            cur.execute(sql_string, values)

    # 2. Store other info.
    with open(os.path.join(CONSTANT_FILES_PATH,'abilities.json')) as data_file:
        data_all = json.load(data_file, object_pairs_hook=OrderedDict)
        for key, data in data_all.items():
            sql_string =    "UPDATE hero_abilities SET " + \
                            "dname=%s, description=%s " + \
                            "WHERE long_name=%s"
            dname = data['dname'] if 'dname' in data.keys() else ""
            desc = data['desc'] if 'desc' in data.keys() else ""
            values = (dname, desc, key)

            cur.execute(sql_string, values)


    conn.commit()
    cur.close()
    conn.close()

### Save items
def save_items():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    with open(os.path.join(CONSTANT_FILES_PATH,'items.json')) as data_file:
        data_all = json.load(data_file, object_pairs_hook=OrderedDict)
        for key, data in data_all.items():
            img_url = "http://cdn.dota2.com/apps/dota2/images/items/{}_lg.png".format(key)
            mana_cost = 0 if data.get("mc", 0) == False else data.get("mc", 0)
            cd        = 0 if data.get("cd", 0) == False else data.get("cd", 0)
            sql_string =    "INSERT INTO items(item_id, long_name, dname, img_url, qual, " + \
                            "gold_cost, description, notes, mana_cost, cd, lore, created) " + \
                            "VALUES (" + "%s, "*11 + "%s)"
            values =    (data.get('id'), key, data.get('dname', "Unknown"), img_url, \
                        data.get("qual",""), data.get("cost", 0), data.get("desc",""), \
                        data.get("notes",""), mana_cost, cd, \
                        data.get("lore",""), data.get("created", False)
                        )

            cur.execute(sql_string, values)

    conn.commit()
    cur.close()
    conn.close()

### Initialize leagues table with league_id = 0
def init_leagues():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    sql_string =    "INSERT INTO leagues(league_id, tier, league_name) " + \
                    "VALUES(%s, %s, %s)"
    values =    (0, "pub games", "pub games")

    cur.execute(sql_string, values)

    conn.commit()
    cur.close()
    conn.close()

### Initialize players table with account_id = '0'
def init_players():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    sql_string =    "INSERT INTO players(account_id, personaname, avatar_full) " + \
                    "VALUES(%s, %s, %s) " + \
                    "ON CONFLICT (account_id) DO NOTHING"
    values =    ('0', "Anonymous", "")

    cur.execute(sql_string, values)

    conn.commit()
    cur.close()
    conn.close()

# Save leagues to date.
def save_leagues():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()
    
    r = requests.get("https://api.opendota.com/api/leagues")
    data = r.json()
    for league in data:
        if league['leagueid'] != 0:
            sql_string =    "INSERT INTO leagues(league_id, tier, league_name) " + \
                            "VALUES(%s, %s, %s) ON CONFLICT (league_id) DO UPDATE SET " + \
                            "tier=%s, league_name=%s"
            values =    (league['leagueid'], league['tier'], league['name'], league['tier'], league['name'])
        
            cur.execute(sql_string, values)

    conn.commit()
    cur.close()
    conn.close()

# Save teams.
def save_teams():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()
    
    r = requests.get("https://api.opendota.com/api/teams")
    data = r.json()
    for team in data:
        sql_string =    "INSERT INTO teams(team_id, team_name, tag) " + \
                        "VALUES(%s,%s,%s) ON CONFLICT (team_id) DO UPDATE SET " + \
                        "team_name=%s, tag=%s"
        values =    (team['team_id'], team['name'], team['tag'], team['name'], team['tag'])
    
        cur.execute(sql_string, values)

    conn.commit()
    cur.close()
    conn.close()


#############################
# Call API. Collect matches #
#############################

def APICall(STARTING_SEQ_NUM=STARTING_SEQ_NUM):
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    start_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    start_seq = int(STARTING_SEQ_NUM)
    t = '\n\n'+'Start: '+start_time+'\t'+str(start_seq)+'\n'
    with open('dotaoracle_log.txt','a') as f:
        f.write(t)

    # Call Steam API GetMatchHistoryBySequenceNum
    cycle = 0
    while cycle < CYCLES:
        url_req = STEAMAPI_GETMATCHHISTORYBYSEQUENCENUM
        url_req += "?key={}&matches_requested={}&start_at_match_seq_num={}".format(D2APIKEY, 100, start_seq)
        try:
            r = requests.get(STEAMAPI_GETMATCHHISTORYBYSEQUENCENUM, \
                {"key":D2APIKEY, "matches_requested":100, "start_at_match_seq_num":start_seq})
            
            raw_data = r.json()
            if 'result' not in raw_data or raw_data['result']['status'] != 1:
                print("Status {}; Seq_num {}".format(raw_data['result']['status'], start_seq))
                print("\n-----------\n",raw_data,"\n-----------\n")
                
            data = raw_data['result']
            matches = data['matches']
            start_seq = data['matches'][-1]['match_seq_num'] + 1
            for match in matches:
                try:
                    match_id, duration = match['match_id'], match['duration']
                    if match['human_players']==10 and duration >= MIN_DURATION and match['game_mode'] in (1,2,3,5,16,22):
                        # OpenDOTA getmatchdetails often gives account_id=null.
                        # So we obtain the account ids from Steam API and pass them to OpenDOTA.
                        account_ids = [player['account_id'] for player in match['players']]
                        # Call OpenDOTA API to obtain details of a specific match
                        get_match_details(str(match_id), account_ids)
                except Exception as e:
                    print(e)
            time.sleep(TIME_TO_SLEEP)
            print(start_seq)
        except Exception as e:
            print("579, APICall() error, ", e)
            print("Start_seq: {} ".format(start_seq))
            print("URL requested: " + url_req)
            time.sleep(20)
            # Sometimes the error occurs because the Steam API is down. In that case,
            # we may want to keep trying until it recovers.
            cycle -= 1
#            start_seq += 1
        STARTING_SEQ_NUM = str(start_seq+1)
        t = "\tCycle: {}. Last_seq_num: {}.".format(cycle, start_seq)
        print(t)
        with open('dotaoracle_log.txt','a') as f:
            f.write("\n"+t)
        cycle += 1

    end_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    end_seq = STARTING_SEQ_NUM

    cur.close()
    conn.close()

    t = '\nEnd: '+end_time+'\t'+end_seq
    print("DONE\n"+t)
    with open('dotaoracle_log.txt','a') as f:
        f.write(t)

def get_match_details(match_id, account_ids):
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()
    
    start_time = time.time()
    global COUNT

    try:
        print("----Start recording match {}.----".format(match_id))
        r = requests.get(OPENDOTA_GETMATCHDETAILS_URL+match_id)
        data = r.json()
        
        print("{} secs taken after retrieving the data.".format(time.time()-start_time))
        
        # Sometimes the response is corrupted even if the match_id is valid.
        # We give it a second try to see if error occurs.
        gamemode = data.get('game_mode')
        if gamemode is None:
            print("Failed retrieving match {}. Will try again soon...".format(match_id))
            time.sleep(10)
            r = requests.get(OPENDOTA_GETMATCHDETAILS_URL+match_id)
            data = r.json()
            

        # Double check if the match is valid
        if (data['game_mode'] not in (1,2,3,5,16,22)) or data['human_players'] < 10 or data['duration'] < 480:
            time.sleep(TIME_TO_SLEEP)
            return False

        radiant_heroes, dire_heroes = [], []
        for player in data['players']:
            hero_id = player['hero_id']
            if player['player_slot'] < 100:
                radiant_heroes.append(hero_id)
            else:
                dire_heroes.append(hero_id)

        is_parsed = (data['radiant_gold_adv'] != None)

        # Update picks_bans, league and team info if needed.
        if data['leagueid'] > 0 and data['picks_bans'] != None and 'league' in \
        data.keys() and 'radiant_team' in data.keys() and 'dire_team' in data.keys():

            # Upsert the league
            sql_string =    "INSERT INTO leagues(league_id, tier, league_name) " + \
                            "VALUES (%s, %s, %s) ON CONFLICT (league_id) DO " + \
                            "UPDATE SET tier=%s, league_name=%s"
            values =    (data['league']['leagueid'], data['league']['tier'], \
                        data['league']['name'], data['league']['tier'], \
                        data['league']['name'])
            cur.execute(sql_string, values)

            # Upsert the team
            for team in (data['radiant_team'], data['dire_team']):
                sql_string =    "INSERT INTO teams(team_id, team_name, tag) " + \
                                "VALUES (%s, %s, %s) ON CONFLICT (team_id) DO " + \
                                "UPDATE SET team_name=%s, tag=%s"
                values =    (team['team_id'], team['name'], team['tag'], team['name'], team['tag'])
                cur.execute(sql_string, values)

            # Update picks_bans
            picks_bans = data['picks_bans']
            for pick_ban in picks_bans:
                sql_string =    "INSERT INTO picks_bans(match_id, league_id, the_order, team_radiant, " + \
                                "is_pick, hero_id) VALUES (" + "%s, "*5 +"%s) ON CONFLICT (match_id) DO NOTHING"
                values =    (pick_ban['match_id'], data['league']['leagueid'], pick_ban['order'], \
                            pick_ban['team'] == 0, pick_ban['is_pick'], pick_ban['hero_id'])
                cur.execute(sql_string, values)

        # Now insert the new match.
        sql_string= "INSERT INTO matches(start_time, match_id, match_seq_num, cluster_id, " + \
                    "region_id, skill, radiant_win, radiant_heroes, dire_heroes, " + \
                    "duration, lobby_type, game_mode, first_blood_time, " + \
                    "tower_status_radiant, tower_status_dire, barracks_status_radiant, " + \
                    "barracks_status_dire, radiant_score, dire_score, league_id, " + \
                    "is_parsed, times, radiant_gold_adv, radiant_xp_adv) " + \
                    "VALUES (to_timestamp(%s)," + "%s, "*22 + "%s) " + \
                    "ON CONFLICT (match_id) DO NOTHING"
        values =    (data['start_time'], data['match_id'], data['match_seq_num'], data['cluster'], \
                    data['region'], data['skill'], data['radiant_win'], radiant_heroes, dire_heroes, \
                    data['duration'], data['lobby_type'], data['game_mode'], \
                    data['first_blood_time'], data['tower_status_radiant'], \
                    data['tower_status_dire'], data['barracks_status_radiant'], \
                    data['barracks_status_dire'], data['radiant_score'], \
                    data['dire_score'], data['leagueid'], is_parsed, \
                    data['players'][0]['times'], data['radiant_gold_adv'], \
                    data['radiant_xp_adv'])

        cur.execute(sql_string, values)
        
        print("{} secs taken after inserting the match.".format(round(time.time()-start_time,3)))

        # Update the match info if it's a league match.
        if data['leagueid'] > 0 and data['picks_bans'] != None and 'league' in \
        data.keys() and 'radiant_team' in data.keys() and 'dire_team' in data.keys():

            sql_string =    "UPDATE matches SET radiant_team_id=%s, dire_team_id=%s " + \
                            "WHERE match_id=%s"
            values = (data['radiant_team']['team_id'], data['dire_team']['team_id'],
                      data['match_id'])

            cur.execute(sql_string, values)


        # Update match_player_pairs
        radiant_win = data['radiant_win']
        for player in data['players']:
#           print("Currently handling hero_id: {}".format(hero['hero_id']))

            # Update player info
            try:
                account_id = str(account_ids.pop(0))
                get_player_info(account_id)

            except Exception as e:
                print("407",match_id,e)
                time.sleep(TIME_TO_SLEEP)
                return False

            # Update match_player_pairs
            try:
                sql_string =    "INSERT INTO match_player_pairs(match_id, hero_id, account_id, " + \
                                "is_parsed, team_radiant, radiant_win, player_slot, item_0, item_1, item_2, item_3, " + \
                                "item_4, item_5, backpack_0, backpack_1, backpack_2, " + \
                                "ability_upgrades_arr, kills, deaths, assists, leaver_status, " + \
                                "last_hits, denies, gold_per_min, xp_per_min, final_level, hero_damage, " + \
                                "tower_damage, hero_healing, gold, gold_spent)" + \
                                "VALUES (" + "%s, "*30 + "%s) ON CONFLICT (match_id, player_slot) DO NOTHING"
                values =    (match_id, player['hero_id'], account_id, is_parsed, player['player_slot']<100, \
                            data['radiant_win'], player['player_slot'], player['item_0'], player['item_1'], player['item_2'], \
                            player['item_3'], player['item_4'], player['item_5'], player['backpack_0'], \
                            player['backpack_1'], player['backpack_2'], player['ability_upgrades_arr'], \
                            player['kills'], player['deaths'], player['assists'], player['leaver_status'], \
                            player['last_hits'], player['denies'], \
                            player['gold_per_min'], player['xp_per_min'], player['level'], player['hero_damage'], \
                            player['tower_damage'], player['hero_healing'], player['gold'], player['gold_spent'])

                cur.execute(sql_string, values)
#                conn.commit()

                # If is_parsed, record extra info such as gold_t, xp_t, purchase_log, etc.
                if is_parsed:

                    # gold_t, xp_t
                    try:
                        sql_string =    "UPDATE match_player_pairs SET gold_t=%s, xp_t=%s" + \
                                        "WHERE match_id=%s AND hero_id=%s"
                        values = (player['gold_t'], player['xp_t'], match_id, player['hero_id'])
                        cur.execute(sql_string, values)

                    except Exception as e:
                        print("400, gold_t and xp_t, ",match_id,e)
                        time.sleep(TIME_TO_SLEEP)
                        return False

                    # lane_pos
                    try:
                        lane_pos = "{"
                        lane_pos_dict = player['lane_pos']
                        for x, y_dict in lane_pos_dict.items():
                            for y, count in y_dict.items():
                                lane_pos += "{"+str(x)+","+str(y)+","+str(count)+"},"
                        lane_pos = lane_pos[:-1] + "}"

                        sql_string =    "UPDATE match_player_pairs SET lane_pos=%s" + \
                                        "WHERE match_id=%s AND hero_id=%s"
                        values = (lane_pos, match_id, player['hero_id'])
                        cur.execute(sql_string, values)

                    except Exception as e:
                        print("401, lane_pos, ",match_id,e)
                        time.sleep(TIME_TO_SLEEP)
                        return False

                    # purchase_log
                    try:
                        for purchase in player['purchase_log']:
                            # find item_id
                            sql_string =    "SELECT item_id FROM items WHERE long_name='"+purchase['key']+"'"
                            cur.execute(sql_string)
                            item_id = cur.fetchone()[0]

                            sql_string =    "INSERT INTO purchase_log(match_id, player_slot, " + \
                                            "hero_id, radiant_win, time, item) " + \
                                            "VALUES(%s,%s,%s,%s,%s,%s)"
                            values =        (match_id, player['player_slot'], player['hero_id'], + \
                                            radiant_win==1, purchase['time'], item_id)
                            cur.execute(sql_string, values)

                    except Exception as e:
                        print("402, purchase_log, ",match_id,e)
                        time.sleep(TIME_TO_SLEEP)
                        return False

                    # lane, lane_role, is_roaming, purchase_ward_observer, purchase_ward_sentry
                    # purchase_tpscroll, purchase_gem
                    try:
                        sql_string =    "UPDATE match_player_pairs " + \
                                        "SET lane=%s, lane_role=%s, is_roaming=%s, " + \
                                        "purchase_ward_observer=%s, purchase_ward_sentry=%s, " + \
                                        "purchase_tpscroll=%s, purchase_gem=%s " + \
                                        "WHERE match_id=%s AND hero_id=%s"
                        values =    (player['lane'], player['lane_role'], + \
                                    player['is_roaming']==1, player.get('purchase_ward_observer',0), + \
                                    player.get('purchase_ward_sentry',0), player.get('purchase_tpscroll',0), + \
                                    player.get('purchase_gem',0), match_id, player['hero_id'])
                        cur.execute(sql_string, values)

                    except Exception as e:
                        print("403, lane, lane_role, is_roaming, etc.",match_id,e)
                        time.sleep(TIME_TO_SLEEP)
                        return False

                    # obs_log
                    try:
                        logs = player['obs_log']

                        for log in logs:

                            sql_string =    "INSERT INTO obs_log(match_id, account_id, " + \
                                            "player_slot, time, x, y, z)" + \
                                            "VALUES(%s,%s,%s,%s,%s,%s,%s)"
                            values =        (match_id, account_id, player['player_slot'], + \
                                            log['time'], log['x'], log['y'], log['z'])

                            cur.execute(sql_string, values)

                    except Exception as e:
                        print("404, obs_log",match_id,e)
                        time.sleep(TIME_TO_SLEEP)
                        return False

                    # sen_log
                    try:
                        logs = player['sen_log']

                        for log in logs:

                            sql_string =    "INSERT INTO sen_log(match_id, account_id, " + \
                                            "player_slot, time, x, y, z)" + \
                                            "VALUES(%s,%s,%s,%s,%s,%s,%s)"
                            values =        (match_id, account_id, player['player_slot'], + \
                                            log['time'], log['x'], log['y'], log['z'])

                            cur.execute(sql_string, values)

                    except Exception as e:
                        print("404, sen_log",match_id,e)
                        time.sleep(TIME_TO_SLEEP)
                        return False

            except Exception as e:
                print("408",match_id,e)
                time.sleep(TIME_TO_SLEEP)
                return False
        
        print("{} secs taken after updating match_player_pairs.".format(round(time.time()-start_time,2)))
        
        conn.commit()
        print("----Successfully recorded {}th match {}----\n\n".format(COUNT, match_id))
        COUNT += 1
        time.sleep(TIME_TO_SLEEP)
        return True

    except Exception as e:
        print("414",match_id,e)
        time.sleep(max(TIME_TO_SLEEP, 10))
#        return False

    cur.close()
    conn.close()

def get_player_info(account_id):
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    try:
        start_time = time.time()
        r = requests.get(OPENDOTA_GETPLAYERINFO_URL+account_id)
        player_info = r.json()

        if 'profile' not in player_info.keys():
            # Anonymous user.
            sql_string =    "INSERT INTO players(account_id, personaname, avatar_full) " + \
                            "VALUES(%s, %s, %s) " + \
                            "ON CONFLICT (account_id) DO NOTHING"
            values =    (account_id, "Anonymous", "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg")

        else:
            player_profile = player_info['profile']
#            print("PLAYER_PROFILE: ", player_profile)
            mmr_estimate = player_info['mmr_estimate'].get('estimate', None)

            sql_string =    "INSERT INTO players(account_id, personaname, avatar_full, " + \
                            "profile_url, loccountrycode, party_mmr, solo_mmr, mmr_estimate) " + \
                            "VALUES (" + "%s, "*7 + "%s)" + \
                            "ON CONFLICT (account_id) DO UPDATE SET " + \
                            "personaname=%s, avatar_full=%s, profile_url=%s, loccountrycode=%s, " + \
                            "party_mmr=%s, solo_mmr=%s, mmr_estimate=%s"
            values =    (account_id, player_profile['personaname'], player_profile['avatarfull'], \
                        player_profile['profileurl'], player_profile['loccountrycode'], \
                        player_info['competitive_rank'], player_info['solo_competitive_rank'], \
                        mmr_estimate, \
                        player_profile['personaname'], player_profile['avatarfull'], \
                        player_profile['profileurl'], player_profile['loccountrycode'], \
                        player_info['competitive_rank'], player_info['solo_competitive_rank'], \
                        mmr_estimate)
            print("\t{} sec taken retrieving player account info.".format(round(time.time()-start_time,3)))

#        print("----------------------------------\n", sql_string)
#        print("------------------------------------\n", values, "--------------------------------\n")
        cur.execute(sql_string, values)

        conn.commit()
        time.sleep(TIME_TO_SLEEP)
        return account_id

    except Exception as e:
        print("415",account_id,e)
        time.sleep(TIME_TO_SLEEP)
        return '0'

    cur.close()
    conn.close()

def rebuild_db():
    drop_all_tables()
    create_tables()
    save_constants()

def emtpy_matches():
    conn = psycopg2.connect(**WORKINGDB)
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE matches CASCADE")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'rebuild':
        rebuild_db()
    APICall()