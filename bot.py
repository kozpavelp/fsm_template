from aiogram import Bot, Dispatcher, F
from aiogram.filters import StateFilter, Command, CommandStart, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           Message, PhotoSize)

from config_data.config import Config, load_config


config: Config = load_config(None)

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
redis: Redis = Redis(host='localhost')

storage: RedisStorage = RedisStorage(redis=redis)

bot: Bot = Bot(token=config.tg_bot.token)
dp: Dispatcher = Dispatcher(storage=storage)

# "BD"
users: dict[int, dict[str, str | int | bool]] = {}


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Перечисляем возможные остояния бота
    fill_name = State()
    fill_age = State()
    fill_gender = State()
    upload_photo = State()
    fill_education = State()
    fill_wish_news = State()


@dp.message(CommandStart())
async def start_com(message: Message):
    await message.answer(text='FSM DEMO BOT\n/fillform to continue')


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def cancel_com(message: Message, state: FSMContext):
    await message.answer(text='Leaving FSM\n\ntype /fillform to start again')

    # Сбрасываем FSM
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии по умолчанию и сообщать, что эта команда доступна в машине состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def nothing_to_cancel(message: Message):
    await message.answer(text='You are out of FSM. Nothing to cancel\nUse /fillform to start')


# Этот хэндлер будет срабатывать на команду /fillform и переводить бота в состояние ожидания ввода имени
@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def fillform_com(message: Message, state: FSMContext):
    await message.answer(text='Enter your name')

    # Устававливаем состояние ожидания имени
    await state.set_state(FSMFillForm.fill_name)


# Этот хэндлер будет срабатывать, если введено корректное имя и переводить в состояние ожидания ввода возраста
@dp.message(StateFilter(FSMFillForm.fill_name), F.text.isalpha())
async def fsm_name_sent(message: Message, state: FSMContext):
    # Сохраняем имя по ключу 'name'
    await state.update_data(name=message.text)

    await message.answer(text='Input your age')

    # Переводим FSM в ожидание возраста
    await state.set_state(FSMFillForm.fill_age)


# Этот хэндлер будет срабатывать, если во время ввода имени будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_name))
async def not_name_err(message: Message):
    await message.answer(text='Not name typed. Enter your name, please\n/cancel - to stop filling form')


# Этот хэндлер будет срабатывать, если введен корректный возраст и переводить в состояние выбора пола
@dp.message(StateFilter(FSMFillForm.fill_age), lambda x: x.text.isdigit() and 4 <= int(x.text) <= 120)
async def fsm_age_sent(message: Message, state: FSMContext):
    # Сохраняем возраст по ключу 'age'
    await state.update_data(age=message.text)

    #Создаем кнопки полов
    male_btn: InlineKeyboardButton = InlineKeyboardButton(text='MALE', callback_data='male')
    female_btn: InlineKeyboardButton = InlineKeyboardButton(text='FEMALE', callback_data='female')

    #создаем клавиатуру
    keyboard: list[list[InlineKeyboardButton]] = [[male_btn, female_btn]]
    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Спрашиваем пол
    await message.answer(text='Input your gender', reply_markup=markup)

    # Переводим машину ожидания на ожидание пола
    await state.set_state(FSMFillForm.fill_gender)


# Этот хэндлер будет срабатывать, если во время ввода возраста будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_age))
async def not_age_err(message: Message):
    await message.answer(text='Not age typed. Enter your age, please\n/cancel - to stop filling form')


# Этот хэндлер будет срабатывать на нажатие кнопки при выборе пола и переводить в состояние отправки фото
@dp.callback_query(StateFilter(FSMFillForm.fill_gender), Text(text=['male', 'female']))
async def fsm_gender_sent(callback: CallbackQuery, state: FSMContext):
    # Сохраняем пол по ключу gender
    await state.update_data(gender=callback.data)

    # Удаляем кнопки перед отправкой фото
    await callback.message.delete()

    await callback.message.answer(text='Send photo')

    # Ставим режим ожидания фото
    await state.set_state(FSMFillForm.upload_photo)


# Этот хэндлер будет срабатывать, если во время выбора пола, будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_gender))
async def fsm_gender_err(message: Message):
    await message.answer(text='Not gender typed. Select gender, please\n/cancel - to stop filling form')


# Этот хэндлер будет срабатывать, если отправлено фото и переводить в состояние выбора образования
@dp.message(StateFilter(FSMFillForm.upload_photo), F.photo[-1].as_('largest_photo'))
async def fsm_photo_sent(message: Message, state: FSMContext, largest_photo: PhotoSize):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище по ключам "photo_unique_id" и "photo_id"
    await state.update_data(photo_unique_id=largest_photo.file_unique_id,
                            photo_id=largest_photo.file_id)

    # Создаем кнопки и клавиатуру
    secondary_btn: InlineKeyboardButton = InlineKeyboardButton(text='Secondary education', callback_data='Secondary')
    hightschool_btn: InlineKeyboardButton = InlineKeyboardButton(text='High School education', callback_data='Hight School')
    no_edu_btn: InlineKeyboardButton = InlineKeyboardButton(text='No education', callback_data='No education')

    keyboard: list[list[InlineKeyboardButton]] = [[secondary_btn, hightschool_btn],
                                                  [no_edu_btn]]

    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Задаем вопрос
    await message.answer(text='Chose education level', reply_markup=markup)

    # переводим машину в ожидание выбора образования
    await state.set_state(FSMFillForm.fill_education)


# Этот хэндлер будет срабатывать, если во время отправки фото будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.upload_photo))
async def fsm_photo_err(message: Message):
    await message.answer(text='Waiting for photo\n/cancel- to stop filling form')


# Этот хэндлер будет срабатывать, если выбрано образование и переводить в состояние согласия получать новости
@dp.callback_query(StateFilter(FSMFillForm.fill_education, Text(text=['Secondary', 'Hight School', 'No education'])))
async def fsm_education_sent(callback: CallbackQuery, state: FSMContext):
    # Сохраняем образование по ключу education
    await state.update_data(education=callback.data)

    # создаем кнопки и клавиатуру
    yes_btn: InlineKeyboardButton = InlineKeyboardButton(text='YES', callback_data='yes')
    no_btn: InlineKeyboardButton = InlineKeyboardButton(text='NO', callback_data='no')

    keyboard: list[list[InlineKeyboardButton]] = [[yes_btn, no_btn]]

    markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    # спрашиваем про новости
    await callback.message.edit_text(text='Would you like to recieve news', reply_markup=markup)

    # Устанавливаем состояние
    await state.set_state(FSMFillForm.fill_wish_news)


# Этот хэндлер будет срабатывать, если во время выбора образования будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_education))
async def fsm_education_err(message: Message):
    await message.answer(text='No education chosen. Please chose education\n/cancel - to stop filling form ')


# Этот хэндлер будет срабатывать на выбор получать или не получать новости и выводить из машины состояний
@dp.callback_query(StateFilter(FSMFillForm.fill_wish_news), Text(text=['yes', 'no']))
async def fsm_news_sent(callback: CallbackQuery, state: FSMContext):
    # Сохраняем в бд по ключу wish_news
    await state.update_data(wish_news=callback.data == 'yes')

    # Добавляем в бд карточку пользователя по ключу id
    users[callback.from_user.id] = await state.get_data()

    # Завершаем машину состояний
    await state.clear()

    # Отправляем сообщение о завершении заполнения
    await callback.message.edit_text(text='All done\nexiting FSM')

    # Предложение посмотреть анкету
    await callback.message.answer(text='To view you data type /showdata')


# Этот хэндлер будет срабатывать, если во время согласия на получение новостей будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_wish_news))
async def fsm_news_err(message: Message):
    await message.answer(text='please use buttons to answer\n/cancel - to stop filling form')


# Этот хэндлер будет срабатывать на отправку команды /showdata и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
@dp.message(Command(commands='showdata'), StateFilter(default_state))
async def showdata_com(message: Message):
    # Отправляем анкету, если пользователь есть в бд
    if message.from_user.id in users:
        await message.answer_photo(photo=users[message.from_user.id]['photo_id'],
                                   caption=f"Name: {users[message.from_user.id]['name']}\n"
                                   f"Age: {users[message.from_user.id]['age']}\n"
                                   f"Education: {users[message.from_user.id]['education']}\n"
                                   f"Accept news: {users[message.from_user.id]['wish_news']}")
    else:
        await message.answer(text="You haven't fill form yet")


# Этот хэндлер будет срабатывать на любые сообщения, кроме тех для которых есть отдельные хэндлеры, вне состояний
@dp.message(StateFilter(default_state))
async def anything_else(message: Message):
    await message.answer(text="It's FSM test. nothing else allowed")

if __name__ == '__main__':
    dp.run_polling(bot)