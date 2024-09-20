import pytz
import requests
from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger

import app.handlers as h
from config import api_key

# https://www.devglan.com/online-tools/aes-encryption-decryption

# maybe pirluda
# api_key = 'BFF58C4C427053DBF25240400CDCBB2FE0A132A9D31CA55BC52D937A8192018E37BE2AA7B46B1C3739E4A717DCA46A8E'
# illuhaproger
# api_key = '291E126C514388688D07751930BA642F1F092D6D204D704796B631A77585D8219FF8E06AD5B352CE9196226B86CE77FD'
# illyakup
# api_key = '9E130836BDE61423C0FFA21E4A7FD6A55729FAF8E2E14AEEFF1EBBD3F4C56A4AC9226221A6DCE5791C226A6BC69D62D6'


BASE_URL = 'https://v3.football.api-sports.io/'
timezone = 'Europe/Kiev'

users_db = dict()
team_dict = {"Dynamo Kyiv": 572, "Real Madrid": 541}


# function which helps avoid error with dictionary users_db, job scheduler if bot server restart
def get_user_teams(user_id, hour=9, minute=5):
    # If there is no data for the user, create it
    if user_id not in users_db:
        users_db[user_id] = {}
        users_db[user_id]["teams"] = team_dict.copy()

        users_db[user_id]["notifications"] = {}
        users_db[user_id]["notifications"]["status"] = True
        users_db[user_id]["notifications"]["time"] = "07:45"

        # starting scheduler
        if not h.scheduler_.running:
            h.scheduler_.start()
        job_id = f"job_{user_id}"
        h.scheduler_.add_job(h.notifications_message, CronTrigger(hour=hour, minute=minute), id=job_id)
    return users_db[user_id]


def get_date(date_format):
    current_time = datetime.now()
    return current_time.strftime(date_format)


def today_date():
    return get_date('%Y-%m-%d')


def season_year():
    return get_date('%Y')


def get_days_count_in_month(year, month):
    import calendar
    return calendar.monthrange(year, month)[1]


def set_right_parameters(value, func):
    if value is None:
        return func
    else:
        return value


# function to create custom date_from
def specify_date(date_from=None, days_count=0):
    date_from = set_right_parameters(date_from, today_date())

    return (datetime.strptime(date_from, "%Y-%m-%d") + timedelta(days=days_count)).strftime('%Y-%m-%d')


def get_matches_of_one_team(user_id,
                            season=None,
                            team_id=572,
                            date_from=None,
                            days_count=0):

    season = set_right_parameters(season, season_year())
    date_from = set_right_parameters(date_from, today_date())

    end_date = specify_date(date_from, days_count)
    get_user_teams(user_id)

    # If month is Jan-Jun – it is previous season
    if 1 <= int(date_from.split('-')[1]) <= 6:
        season = int(season) - 1

    url = f'{BASE_URL}fixtures?season={season}&team={team_id}&from={date_from}&to={end_date}'
    response = requests.get(url, headers={'x-apisports-key': api_key})
    fixtures = response.json()

    print("Response API:", response.json())

    if 'response' in fixtures:
        matches_response = fixtures['response']
        if len(matches_response) == 0:
            # "There aren't any matches today if fixture['response'] = []"
            return None
        else:
            matches_result = ''
            for match in matches_response:

                home_team = match['teams']['home']['name']
                away_team = match['teams']['away']['name']

                league_name = match['league']['name']
                league_country = match['league']['country']
                league_round = match['league']['round']

                # Regular season it is order of match (round 3)
                if "Regular Season" in league_round:
                    league_round = "round" + league_round.split('-')[1]

                stadium = match['fixture']['venue']['name']
                city = match['fixture']['venue']['city']

                match_date = match['fixture']['date']
                status = match['fixture']['status']['long']
                score = match['goals']

                home_score = score['home'] if score['home'] is not None else '–'
                away_score = score['away'] if score['away'] is not None else '–'

                parsed_datetime = datetime.fromisoformat(match_date)
                local_timezone = pytz.timezone(timezone)
                match_time_local = parsed_datetime.astimezone(local_timezone)

                # Extract the time in HH:MM format
                time_str = match_time_local.strftime("%H:%M")
                date_res = datetime.fromisoformat(match_date).strftime("%d-%m-%Y – %A")
                matches_result += (f"🏆{league_country}, {league_name} – {league_round}\n"
                                   f"📅{date_res}\n"
                                   f"⚽️{home_team} {home_score}:{away_score} {away_team}, Status: {status}\n"
                                   f"⏰{time_str}\n"
                                   f"📍{city}\n"
                                   f"🏟{stadium}\n\n")
            return matches_result


def get_matches_of_all_teams(days_count,
                             user_id,
                             date_from=None,
                             season=None):

    date_from = set_right_parameters(date_from, today_date())
    season = set_right_parameters(season, season_year())

    get_user_teams(user_id)

    result = ''
    for team in users_db.get(user_id).get("teams").values():
        today_matches = get_matches_of_one_team(season=season, team_id=team, date_from=date_from,
                                                days_count=days_count, user_id=user_id)
        if today_matches is not None:
            result += today_matches
    return result


def get_team_info(team_name):
    url = f'{BASE_URL}teams?search={team_name}'
    response = requests.get(url, headers={'x-apisports-key': api_key})
    fixtures = response.json()

    if not fixtures["response"]:
        return ["Couldn't find the team."]
    i = 0
    result = []
    for team in fixtures["response"]:
        if team["team"]["name"].lower() == team_name.lower() or team_name.lower() in team["team"]["name"].lower():
            result.append({"name": team["team"]["name"], "country": team["team"]["country"], "id": team["team"]["id"],
                           "logo": team["team"]["logo"], "stadium": team["venue"]["name"]})
            i += 1
            if i == 3:
                break
    return result
