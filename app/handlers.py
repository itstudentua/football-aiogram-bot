from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram import Router, F
from apscheduler.triggers.cron import CronTrigger

import app.keyboards as kb
import app.request as rq
import re

router = Router()  # передается значение переменной dp для роутера из файла запуска бота

from bot import bot, scheduler_


def validate_time(time_str):
    time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
    return time_pattern.match(time_str) is not None


class ScheduleChoice(StatesGroup):
    period = State()
    year = State()
    month = State()


class Team(StatesGroup):
    adding_team = State()
    yes_no = State()
    removing_team = State()


class Notifications(StatesGroup):
    time = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id

    if not scheduler_.running:
        scheduler_.start()
    rq.get_user_teams(user_id, 0, 45)

    await message.answer("Hello and welcome🫶\nHere is your sports helper bot 🤖\n\nIt will remind you of your "
                         "favorite team's soccer games ⚽️.\n\nIt is customizable ⚙️.\nYou can select your favorite "
                         "teams and watch the match schedule.\nYou can set notifications 📢 on the day of the match "
                         "or the day before the event.", reply_markup=kb.main_kb)
    # await message.reply("How are you?")


async def notifications_message():
    for user in list(rq.users_db.keys()):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        hour = rq.get_user_teams(user)["notifications"]["time"].split(':')[0]
        minute = rq.get_user_teams(user)["notifications"]["time"].split(':')[1]
        print(f"Notifications – not_hour: {hour}, not_minute: {minute}, cur_h: {current_time.split(':')[0]}, cur_m: "
              f"{current_time.split(':')[1]}")
        if (rq.get_user_teams(user)["notifications"]["status"] and int(hour) == int(current_time.split(':')[0]) and
                int(minute) == int(current_time.split(':')[1])):
            result = rq.get_matches_of_all_teams(user_id=user, days_count=0,
                                                 date_from=rq.today_date())
            if result == '':
                result = f"There aren't any matches today!"
            else:
                result = f"Today's schedule for your favourite teams:\n\n{result}"
            await bot.send_message(user, result)


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    rq.get_user_teams(user_id)
    await message.answer("You don't need help!")


@router.message(F.text == 'My teams')
async def my_teams(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    user_info = rq.get_user_teams(user_id)
    if len(user_info["teams"]) > 0:
        text = f'My teams ⚽️:'
        keyboard = await kb.my_teams(user_id=message.from_user.id, all_in=False)
    else:
        text = "You don't have any team yet!"
        keyboard = None
    await message.answer("You could add/remove teams.", reply_markup=kb.my_teams_menu)
    # await message.answer(text, reply_markup=await kb.my_teams(user_id=message.from_user.id))
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == 'Main menu')
async def main_menu(message: Message, state: FSMContext):
    await state.clear()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    user_id = message.from_user.id
    rq.get_user_teams(user_id)
    await message.answer("Here we are in the main menu😎", reply_markup=kb.main_kb)


@router.message(F.text == 'Calendar')
async def calendar(message: Message, state: FSMContext):
    await state.clear()

    await state.update_data(year=rq.season_year())
    user_id = message.from_user.id
    rq.get_user_teams(user_id)
    await message.answer("Select the month to show the matches:",
                         reply_markup=await kb.calendar_kb(int(rq.season_year())))


@router.message(F.text == 'Schedule')
async def schedule(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    rq.get_user_teams(user_id)
    result = rq.get_matches_of_all_teams(user_id=message.from_user.id, days_count=0, date_from=rq.today_date())
    if result == '':
        result = f"There aren't any matches today!"
    else:
        result = f"Today's schedule for your favourite teams:\n\n{result}"

    keyboard = kb.schedule_menu
    if len(rq.get_user_teams(user_id)["teams"]) == 0:
        result = "You don't have any teams to discover schedule!"
        keyboard = None
    await message.answer(result, reply_markup=keyboard)


@router.message(F.text == 'Next week')
async def schedule_next_week(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    rq.get_user_teams(user_id)

    await state.update_data(period=message.text)
    await message.answer(f'Choose the team to watch schedule for {message.text.lower()}️:',
                         reply_markup=await kb.my_teams(user_id=message.from_user.id))
    # await schedule_func(message, 7, rq.today_date, kb.schedule_menu, "Next week")


@router.message(F.text == 'Today')
async def schedule_today(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    rq.get_user_teams(user_id)

    await state.update_data(period=message.text)
    await message.answer(f'Choose the team to watch schedule for {message.text.lower()}️:',
                         reply_markup=await kb.my_teams(user_id=message.from_user.id))
    # await schedule_func(message, 0, rq.today_date, kb.schedule_menu, "today")


@router.message(F.text == 'Previous week')
async def schedule_prev_week(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    rq.get_user_teams(user_id)

    await state.update_data(period=message.text)
    await message.answer(f'Choose the team to watch schedule for {message.text.lower()}️:',
                         reply_markup=await kb.my_teams(user_id=message.from_user.id))
    # await schedule_func(message, 7, rq.specify_date(rq.today_date, -7),
    #                     kb.schedule_menu, "Previous week")


@router.message(F.text == 'Add team')
async def add_team(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    rq.get_user_teams(user_id)

    await state.set_state(Team.adding_team)
    await message.answer(f'Enter name of the team️:')


@router.message(Team.adding_team)
async def get_team(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    rq.get_user_teams(user_id)
    teams_list = rq.get_team_info(message.text)
    await state.update_data(adding_team=teams_list)
    keyboard = await kb.teams_to_add(f'{item["name"]}, {item["country"]}' for item in teams_list)
    await message.answer("Choose team to add:", reply_markup=keyboard)


@router.message(Team.yes_no)
async def approve_team(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_info = rq.get_user_teams(user_id)

    await state.update_data(yes_no=message.text)
    add_team_answer = await state.get_data()
    team_info = add_team_answer.get("adding_team")

    name = team_info["name"]
    team_id = team_info["id"]

    if message.text.lower() == "yes":
        user_info["teams"][name] = team_id
        answer_message = f"Team {name} successfully added!"
        mrkup = None
        await answer_func(state, message, answer_message, mrkup)
    elif message.text.lower() == "no":
        answer_message = f"No so not.."
        mrkup = kb.my_teams_menu
        await answer_func(state, message, answer_message, mrkup)
    else:
        await state.clear()
        await state.set_state(Team.adding_team)
        await get_team(message, state)
        # answer_message = "Okay, another one"
        # mrkup = await kb.my_teams()


async def answer_func(state, message, answer_message, mrkup):
    user_id = message.from_user.id
    rq.get_user_teams(user_id)

    await state.clear()
    await message.answer(f'{answer_message}', reply_markup=mrkup)
    await message.answer("What's next?", reply_markup=kb.main_kb)


@router.message(F.text == 'Remove team')
async def remove_team(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id

    result = "You don't have any teams to remove!"
    keyboard = None

    if len(rq.get_user_teams(user_id)["teams"]) != 0:
        result = 'Choose team to remove:'
        keyboard = await kb.my_teams(user_id=message.from_user.id, all_in=False)
        await state.update_data(removing_team="yes")
    await message.answer(result, reply_markup=keyboard)


@router.message(F.text == 'Notifications')
async def notifications_func(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    user_info = rq.get_user_teams(user_id)
    status = user_info["notifications"]["status"]
    notifications_time = user_info["notifications"]["time"]
    answer_status = "On" if status else "Off"
    text = (f"Notification settings:\nCurrent notification status – {answer_status}\nNotification time is – "
            f"{notifications_time}")
    await message.answer(text, reply_markup=await kb.notifications_kb(status))


@router.message(Notifications.time)
async def set_notifications_time(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    job_id = f"job_{user_id}"
    user_info = rq.get_user_teams(user_id)

    time = str(message.text)
    hour = time.split(':')[0]
    minute = time.split(':')[1]

    if validate_time(time):
        await state.update_data(time=message.text)
        try:
            scheduler_.remove_job(job_id)
        except Exception as ex:
            print(ex)
        try:
            scheduler_.add_job(notifications_message, CronTrigger(hour=int(hour), minute=int(minute)),
                               id=f"{job_id}")

            user_info["notifications"]["time"] = f"{hour}:{minute}"
            await message.answer(f"Okay, your notification time changed for {hour}:{minute}!")
        except Exception as ex:
            print(ex)
    else:
        await message.answer("Enter time in HH:MM format. For example 13:03")


@router.message()
async def default_message(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    rq.get_user_teams(user_id)

    await message.reply("I don't understand what is that :-)")


@router.callback_query(F.data.startswith('notifications_'))
async def set_notifications(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    status = True
    btn_res = ["ON✅", "OFF"]

    notifications = callback.data.split('_')[1]

    current_markup = callback.message.reply_markup.dict()

    user_id = callback.from_user.id
    user_info = rq.get_user_teams(user_id)

    if notifications == "ON":
        status = True
        btn_res = ["ON✅", "OFF"]
        user_info["notifications"]["status"] = True
        hour = int(user_info["notifications"]["time"].split(':')[0])
        minute = int(user_info["notifications"]["time"].split(':')[1])
        try:
            scheduler_.remove_job(f"job_{user_id}")
        except Exception as ex:
            print(ex)
        try:
            scheduler_.add_job(notifications_message, CronTrigger(hour=hour, minute=minute), id=f"job_{user_id}")
        except Exception as ex:
            print(ex)

    elif notifications == "OFF":
        status = False
        btn_res = ["ON", "OFF❌"]
        user_info["notifications"]["status"] = False
        try:
            scheduler_.remove_job(f"job_{user_id}")
        except Exception as ex:
            print(ex)

    is_markup_equals = True
    for i in range(2):
        if current_markup['inline_keyboard'][0][i]["text"] == btn_res[i]:
            is_markup_equals = False

    if notifications == "time":
        hour = user_info["notifications"]["time"].split(':')[0]
        minute = user_info["notifications"]["time"].split(':')[1]
        await callback.message.answer(f"Current time: {hour}:{minute}\nEnter time to get notification:")
        await state.set_state(Notifications.time)

    else:
        if is_markup_equals:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=await kb.notifications_kb(status=status))


@router.callback_query(F.data.startswith('add_team_'))
async def choose_adding_team(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_info = rq.get_user_teams(user_id)
    team_name = str(callback.data.split('_')[-1])
    team_number = int(callback.data.split('_')[-2])

    add_team_answer = await state.get_data()
    team_dict = add_team_answer.get("adding_team")

    await state.update_data(adding_team=team_dict[team_number])

    name = team_dict[team_number]["name"]
    stadium = team_dict[team_number]["stadium"]
    logo = team_dict[team_number]["logo"]
    country = team_dict[team_number]["country"]

    if team_name in user_info["teams"]:
        await callback.message.answer("You have such team!")
    else:

        await state.set_state(Team.yes_no)

        answer = f"This one?\n⚽️{name}\n🏟️{stadium}\n🌏{country}\n"
        await callback.message.answer(answer)

        await bot.send_photo(chat_id=callback.from_user.id, photo=logo, caption="Here is the logo!",
                             reply_markup=kb.yes_no_kb)


@router.callback_query(F.data.startswith('team_'))
async def choosing_team(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_info = rq.get_user_teams(user_id)

    period_class = await state.get_data()
    team_name = callback.data.split('_')[1]
    month_year = ""

    if period_class.get("removing_team") is not None:
        await state.update_data(removing_team=team_name)
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await callback.message.answer(f"Are you sure you want to delete the {team_name} team?",
                                      reply_markup=kb.removing_teams)
    else:
        team_name = "All teams" if team_name == "all" else team_name

        await callback.answer(f'{team_name}', show_alert=True)

        # if state is empty, choice of period hasn't been made
        if period_class == {}:
            if team_name == "All teams":
                matches = rq.get_matches_of_all_teams(user_id=callback.from_user.id, days_count=0)
            else:
                matches = rq.get_matches_of_one_team(user_id=callback.from_user.id,
                                                     team_id=user_info["teams"].get(team_name),
                                                     days_count=0)
            date_in_answer = "today"

        # if choice of the period has been made
        else:
            days_count = 7  # for week prev and next
            season = rq.season_year()
            if period_class.get("period") == "Next week":
                date_from = rq.today_date()
            elif period_class.get("period") == "Previous week":
                date_from = rq.specify_date(rq.today_date(), -7)
            # for today
            elif period_class.get("period") == "Today":
                date_from = rq.today_date()
                days_count = 0
            else:
                season = period_class.get("year")
                month = period_class.get("month")
                month = f"0{month}" if int(month) < 10 else month
                date_from = f"{season}-{month}-01"
                print(season, month)
                days_count = rq.get_days_count_in_month(int(season), int(month))
                print(days_count)
                month_year = f" {kb.months[int(month)-1]} {season}"
            # show all teams matches
            if team_name == "All teams":
                matches = rq.get_matches_of_all_teams(user_id=callback.from_user.id, season=season,
                                                      days_count=days_count, date_from=date_from)
            # show matches of specific team
            else:
                matches = rq.get_matches_of_one_team(season=season,
                                                     team_id=rq.get_user_teams(callback.from_user.id)["teams"].get(
                                                         team_name),
                                                     date_from=date_from,
                                                     days_count=days_count, user_id=callback.from_user.id)
            date_in_answer = (period_class.get("period").lower() + month_year) if month_year == "" else (
                month_year.strip())
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
            await state.clear()

        # if there aren't any matches, function return None for one team and "" for all teams
        if matches is None or matches == "":
            matches = f"There aren't any matches on {date_in_answer} for {team_name}"
        await callback.message.answer(f"{team_name}'s schedule for {date_in_answer}:\n\n{matches}")


# function switching years in calendar
@router.callback_query(F.data.startswith('year_'))
async def calendar_year(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    user_id = callback.from_user.id
    rq.get_user_teams(user_id)

    new_year = int(callback.data.split('_')[-1])
    print("new year: ", new_year)
    await state.update_data(year=str(new_year))

    keyboard = kb.calendar_kb(new_year)
    await callback.message.edit_reply_markup(reply_markup=await keyboard)


# function choosing month in calendar
@router.callback_query(F.data.startswith('mon_'))
async def calendar_month(callback: CallbackQuery, state: FSMContext):
    year = await state.get_data()
    await state.clear()

    user_id = callback.from_user.id
    rq.get_user_teams(user_id)

    month_for_answer = str(callback.data.split('_')[-2])
    month_for_state = str(callback.data.split('_')[-1])
    await state.update_data(month=month_for_state)
    await state.update_data(period="month")

    if year.get("year") is None:
        await state.update_data(year=rq.season_year())
        year = await state.get_data()
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    year_answer = year.get("year")
    await state.update_data(year=year_answer)
    await callback.message.answer(f"Which teams' schedule do you want to see on {month_for_answer} {year_answer}",
                                  reply_markup=await kb.my_teams(user_id=callback.from_user.id))


@router.callback_query(F.data.startswith('rem_'))
async def remove_team(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_info = rq.get_user_teams(user_id)

    remove_answer = str(callback.data.split('_')[-1])
    team_name = await state.get_data()
    team_name = team_name.get("removing_team")

    if remove_answer == "yes":
        del user_info["teams"][str(team_name)]
        await state.clear()
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await callback.message.answer(f"Team {team_name} successfully removed!",
                                      reply_markup=None)
    elif remove_answer == "no":
        await state.clear()
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await callback.message.answer(f"No so not ...",
                                      reply_markup=await kb.my_teams(user_id=callback.from_user.id, all_in=False))
