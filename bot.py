import config
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ChatPermissions
from aiogram.dispatcher.filters import BoundFilter

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

class IsAdminFilter(BoundFilter):
	key="is_admin"
	
	def __init__(self, is_admin):
		self.is_admin = is_admin
		
	async def check(self, message:types.Message):
		member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
		return member.is_chat_admin()

dp.filters_factory.bind(IsAdminFilter)

@dp.message_handler(is_admin=True, commands=["ban"], commands_prefix="!/")
async def cmd_ban(message: types.Message):
	if not message.reply_to_message:
		await message.reply("Ця команда повинна відповідати на повідомлення корстувача")
		return
	
	await message.bot.delete_message(config.GROUP_ID, message.message_id)
	await message.bot.kick_chat_member(chat_id=config.GROUP_ID, user_id=message.reply_to_message.from_user.id)
	user_id=message.reply_to_message.from_user.id
	await message.reply_to_message.reply(f"Користувач {message.reply_to_message.from_user.full_name} заблокований!")
	
	
	
@dp.message_handler(is_admin=True, commands=["unban"], commands_prefix="!/")
async def cmd_unban(message: types.Message):
	if not message.reply_to_message:
		await message.reply("Ця команда повинна відповідати на повідомлення корстувача")
		return
	
	user = await message.bot.get_chat_member(config.GROUP_ID, message.reply_to_message.from_user.id)
	if user.is_chat_admin():
		await message.reply("Не можна заблокувати адміністратора")
		return

	await message.bot.delete_message(config.GROUP_ID, message.message_id)
	await message.bot.unban_chat_member(chat_id=config.GROUP_ID, user_id=message.reply_to_message.from_user.id)
	user_id=message.reply_to_message.from_user.id
	await message.reply_to_message.reply(f"Користувач {message.reply_to_message.from_user.full_name} розблокований!")



@dp.message_handler(is_admin=True, commands=["mute"], commands_prefix="!/")
async def cmd_mute(message: types.Message):
	if not message.reply_to_message:
		await message.reply("Ця команда повинна відповідати на повідомлення корстувача")
		return

	permissions = ChatPermissions()
	permissions.can_send_messages = False
	permissions.can_send_media_messages = False
	permissions.can_send_stickers = False
	permissions.can_send_animations = False
	permissions.can_send_games = False
	
	await bot.restrict_chat_member(chat_id=config.GROUP_ID, user_id=message.reply_to_message.from_user.id, permissions=permissions)
	
	mute_duration = int(message.text.split()[1])
	
	await message.reply(f"Користувач {message.reply_to_message.from_user.full_name} не може говорити протягом {mute_duration} хвилин!")
	
	await asyncio.sleep(mute_duration*60)
	permissions = ChatPermissions()
	permissions.can_send_messages = True
	permissions.can_send_media_messages = True
	permissions.can_send_stickers = True
	permissions.can_send_animations = True
	permissions.can_send_games = True
	
	await bot.restrict_chat_member(chat_id=config.GROUP_ID, user_id=message.reply_to_message.from_user.id, permissions=permissions)
	
	await message.reply(f"Користувач {message.reply_to_message.from_user.full_name} знову може говорити!")
	
	
	
@dp.message_handler(is_admin=True, commands=["unmute"], commands_prefix="!/")
async def cmd_unmute(message: types.Message):
	if not message.reply_to_message:
		await message.reply("Ця команда повинна відповідати на повідомлення корстувача")
		return
	
	permissions = ChatPermissions()
	permissions.can_send_messages = True
	permissions.can_send_media_messages = True
	permissions.can_send_stickers = True
	permissions.can_send_animations = True
	permissions.can_send_games = True
	
	await bot.restrict_chat_member(chat_id=config.GROUP_ID, user_id=message.reply_to_message.from_user.id, permissions=permissions)
	
	await message.reply(f"Користувач {message.reply_to_message.from_user.full_name} знову може говорити!")

user_id_ban=0
user_name=0
@dp.message_handler(commands=["report"], commands_prefix="!/")
async def cmd_report(message: types.Message):
	global user_name, user_id_ban
	if(user_id_ban==0):
		user_id = message.reply_to_message.from_user.id
		user_name = message.reply_to_message.from_user.full_name
		user_id_ban = message.reply_to_message.from_user.id
		report_text = f"Користувача {message.reply_to_message.from_user.full_name} в групі {message.chat.title} відправили на перевірку {message.from_user.full_name}."
		
		keyboard = types.InlineKeyboardMarkup(row_width=2)
		ban_button = types.InlineKeyboardButton("Заблокувати", callback_data="ban")
		skip_button = types.InlineKeyboardButton("Пропустити", callback_data="skip")
		keyboard.add(ban_button, skip_button)
		
		for recipient_id in config.REPORT_RECIPIENT_IDS:
			await bot.send_message(recipient_id, report_text,reply_markup=keyboard)
		await message.reply("Дякую за доповідь. Адміністратори розглянуть ваше повідомлення.")
		
	else:
		await message.reply("Зачекайте будь ласка. Адміністратори розглядають попереднє доповідь.")


@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
	global user_id_ban
	if callback_query.data == 'ban':
		await bot.answer_callback_query(callback_query.id, text='Користувача заблоковано')
		await bot.kick_chat_member(chat_id=config.GROUP_ID, user_id=user_id_ban)
		await bot.send_message(config.GROUP_ID, text=f"Користувача {user_name} заблокували")
	elif callback_query.data == 'skip':
		await bot.answer_callback_query(callback_query.id, text='Повідомлення пропущено')
		await bot.send_message(config.GROUP_ID, text=f"Користувача {user_name} звільнили")
	user_id_ban = 0
		
@dp.message_handler(content_types=["new_chat_members","left_chat_member"])
async def on_user_joined(message:types.Message):
	await message.delete()


@dp.message_handler()
async def filter_links(message: types.Message):
	chat_id = config.GROUP_ID 						#or message.chat.id
	user_id = message.from_user.id

	chat_member = await bot.get_chat_member(chat_id, user_id)
	if chat_member.status not in ['creator', 'administrator', 'owner']:
		if 't.me' in message.text:
			await message.reply("Вибачте, тільки адміністратори можуть відправляти посилання")
			await message.delete()
		elif '@' in message.text:
			await message.reply("Вибачте, тільки адміністратори можуть відправляти посилання")
			await message.delete()	

if __name__ == "__main__":
	executor.start_polling(dp, skip_updates=True)
	
