from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.request as rq

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']

main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="My teams")],
    [KeyboardButton(text="Schedule"),
     KeyboardButton(text="Notifications")]],
    resize_keyboard=True,
    input_field_placeholder="Select menu item")

yes_no_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Yes"), KeyboardButton(text="No")],
    [KeyboardButton(text="My teams")]
], resize_keyboard=True)

my_teams_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Add team"), KeyboardButton(text="Remove team")],
    [KeyboardButton(text="Main menu")]
], resize_keyboard=True)

schedule_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Previous week"), KeyboardButton(text="Today"), KeyboardButton(text="Next week")],
    [KeyboardButton(text="Calendar")],
    [KeyboardButton(text="Main menu")]
], resize_keyboard=True)


async def my_teams(user_id, all_in=True):
    keyboard = InlineKeyboardBuilder()
    teams = rq.get_user_teams(user_id)["teams"].keys()
    for team in teams:
        keyboard.add(InlineKeyboardButton(text=team, callback_data=f"team_{team}"))
    keyboard.adjust(2)
    if all_in:
        keyboard.row(InlineKeyboardButton(text="All in", callback_data="team_all"))
    if len(teams) > 0:
        return keyboard.as_markup()
    else:
        return None


async def teams_to_add(teams):
    keyboard = InlineKeyboardBuilder()
    i = 0
    for team in teams:
        keyboard.add(InlineKeyboardButton(text=team, callback_data=f"add_team_{i}_{team.split(',')[0]}"))
        i += 1
    keyboard.adjust(2)
    return keyboard.as_markup()


async def notifications_kb(status):
    if status:
        btn_on = "ON✅"
        btn_off = "OFF"
    else:
        btn_on = "ON"
        btn_off = "OFF❌"

    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text=btn_on, callback_data=f"notifications_ON"),
        InlineKeyboardButton(text=btn_off, callback_data=f"notifications_OFF")
    )
    keyboard.add(InlineKeyboardButton(text="Set time of notification", callback_data=f"notifications_time"))
    keyboard.adjust(2, 1)

    return keyboard.as_markup()


async def calendar_kb(year):
    keyboard = InlineKeyboardBuilder()

    i = 1
    for mon in months:
        keyboard.add(InlineKeyboardButton(text=mon[:3], callback_data=f"mon_{mon}_{i}"))
        i += 1
    keyboard.adjust(4)
    keyboard.row(
        InlineKeyboardButton(text="<", callback_data=f"year_{year - 1}"),
        InlineKeyboardButton(text=str(year), callback_data="some_year"),
        InlineKeyboardButton(text=">", callback_data=f"year_{year + 1 if year <= int(rq.season_year()) else year}")
    )
    return keyboard.as_markup()

removing_teams = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="yes", callback_data='rem_yes'), InlineKeyboardButton(text="no", callback_data='rem_no')]])
