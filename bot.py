from aiogram import Bot, types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import asyncio
from pathlib import Path
from threading import Thread
import datetime
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import aioschedule
import os

import csv
from pathlib import Path
import requests
import datetime
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from telegram import ReplyMarkup
from webdriver_manager.chrome import ChromeDriverManager


TOKEN = ""
client_id = 
BASE_DIR = Path(__file__).resolve(strict=True).parent
os.chdir(BASE_DIR)
logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG)
                    
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


class ZprStates(StatesGroup):
    SUBSCRIBE_STATE = State()



@dp.message_handler(commands=['new_subscribe'], state = '*')
async def process_new_subscribe_command(message: types.Message):
    await message.answer("Введите запрос:")
    await ZprStates.SUBSCRIBE_STATE.set()


@dp.message_handler(commands=['my_subscribe'], state = '*')
async def process_new_subscribe_command(message: types.Message):
    file_name = Path(BASE_DIR).joinpath(f"{message.from_user.id}.csv")
    inline_btn = InlineKeyboardButton('Отписаться', callback_data='del_subscribe')
    if Path.is_file(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            for line in f:
                await message.answer(line, reply_markup= InlineKeyboardMarkup().add(inline_btn))    
    else:
        await message.answer('У вас нет подписок')


@dp.callback_query_handler(text= 'del_subscribe', state='*')
async def process_callback_button1(callback_query: types.CallbackQuery):
    del_zpr = callback_query.message.text
    list_zpr = []
    current_file = Path(BASE_DIR).joinpath(f"{callback_query.from_user.id}.csv")
    with open(current_file, "r", encoding="utf-8") as f:
        list_zpr = f.readlines()
        list_zpr.remove(del_zpr + '\n')
    if list_zpr:
        with open(current_file, "w", encoding="utf-8") as f:
            f.writelines(list_zpr)
    else:
        current_file.unlink()
    current_file = Path(BASE_DIR).joinpath(f"{del_zpr}_list.csv")
    with open(current_file, "r", encoding="utf-8") as f:
        list_id = f.readlines()
        list_id.remove(str(callback_query.from_user.id) + '\n')
    if list_id:
        with open(current_file, "w", encoding="utf-8") as f:
            f.writelines(list_id)
    else:
        current_file.unlink()
        if Path.is_file(Path(BASE_DIR).joinpath(f"{del_zpr}.csv")):
            Path(BASE_DIR).joinpath(f"{del_zpr}.csv").unlink()
    if not list_id:
        with open(Path(BASE_DIR).joinpath(f"zapros.txt"), "r", encoding="utf-8") as f:
            list_zpr = f.readlines()
            list_zpr.remove(del_zpr + '\n')
        with open(Path(BASE_DIR).joinpath(f"zapros.txt"), "w", encoding="utf-8") as f:
            f.writelines(list_zpr)

    await callback_query.message.answer("Подписка удалена")
    await callback_query.answer()


@dp.message_handler(state=ZprStates.SUBSCRIBE_STATE)
async def first_test_state_case_met(message: types.Message, state: FSMContext):
    await state.reset_state()
    id = message.from_user.id 
    #await bot.send_message(id, "Пожалуйста, ожидайте")
    zpr = message.text.lower()
    with open(Path(BASE_DIR).joinpath(f"{id}.csv"), "a+", encoding="utf-8") as f:
        f.seek(0)
        f_text = f.read()
        if zpr + '\n' not in f_text:
            f.write(zpr + '\n')
    with open(Path(BASE_DIR).joinpath(f"{zpr}_list.csv"), "a+", encoding="utf-8") as f:
        f.seek(0)
        f_text = f.read()
        if str(id) + '\n' not in f_text:
            f.write(str(id) + '\n')
    with open(Path(BASE_DIR).joinpath("zapros.txt"), "a+", encoding="utf-8") as f:
        f.seek(0)
        find_zpr = zpr + '\n'
        f_text = f.read()
        if find_zpr not in f_text:
            f.write(find_zpr)         
    await message.answer(f'Вы подписались на\n{zpr}')


@dp.message_handler(commands=['start'], state = '*')
async def process_start_command(message: types.Message):
    print(message)
    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()


@dp.message_handler(chat_id = client_id, state = '*')
async def echo_message(message: types.Message):
    zpr, news = message.text.split('&&&&&&&&') 

    await newsletter(zpr,[news])


@dp.message_handler()
async def echo_message(message: types.Message):
    if message.text == "проверка":
        await test_news()
    await message.answer("Выберите пункт меню")


async def scheduler():
    aioschedule.every(10).minutes.do(test_news)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


async def test_news():
    headless = False 
    zapros = []
    if not Path.is_file(Path(BASE_DIR).joinpath('zapros.txt')):
        return
    with open(Path(BASE_DIR).joinpath("zapros.txt"), "r", encoding="utf-8") as f:
        for line in f:
            zapros.append(line.rstrip())

    # инициализируем веб драйвер
    browser = get_driver(headless=headless)
    for zpr in zapros:
        output_filename = f"{zpr}.csv"
        old_news = set()
        if Path.is_file(Path(BASE_DIR).joinpath(output_filename)):
            with open(Path(BASE_DIR).joinpath(output_filename), "r", encoding="utf-8") as f:
                for line in f:
                    old_news.add(line.split('    ')[0])
        new_news = set()
        list_new_news = await connect_to_base(browser, zpr)
        for news in list_new_news:
            if news.split('    ')[0] not in old_news:
                new_news.add(news) 

        await newsletter(zpr, list(new_news))
        write_to_file(list(new_news), output_filename)
    browser.quit()


async def newsletter(filename, list):
    filename = f"{filename}_list.csv"
    with open(Path(BASE_DIR).joinpath(filename), "r", encoding="utf-8") as f:
            for line in f:
                for news in list:
                    if '    ' in news:
                        news_ya = news.split('    ')
                        await bot.send_message(line, f"{news_ya[0]}\n[Ссылка на источник]({news_ya[1]})", parse_mode='Markdown')    
                    else:
                        await bot.send_message(line, news)
                    await asyncio.sleep(1)


def get_driver(headless):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    # инициализируем драйвер с нужными опциями
    driver = webdriver.Chrome(chrome_options=options)
    return driver


async def connect_to_base(browser, zapros):
    zapros = "+%2B".join(zapros.split())
    date_zpr = (datetime.datetime.today() - datetime.timedelta(days=2)).strftime("%Y%m%d")
    base_url = f"https://yandex.ru/search/?text=%2B{zapros}+date%3A>{date_zpr}&lr=21"#&within=77"
    connection_attempts = 0
    current_page = 0
    end_page = 2
    output_list = []
    browser.get(base_url)
    for current_page in range(end_page):
        await asyncio.sleep(random.randint(2,5))
        print(f"Scraping page #{current_page}...")
        html_page = browser.page_source
        try:
            btn = browser.find_element_by_class_name("pager__item_kind_next")
            btn.click()
            await asyncio.sleep(2)
        except:
            try:
                browser.find_element_by_class_name("CheckboxCaptcha-Anchor").click()
                await asyncio.sleep(random.randint(3,5))
                output_list = output_list + parse_html(browser.page_source)
            except:
                output_list = output_list + parse_html(html_page)
                break
    return output_list


def parse_html(html):
    # создадим новый объект soup
    soup = BeautifulSoup(html, "html.parser")
    output_list = []
    tr_blocks = soup.find_all('a', class_='OrganicTitle-Link')
    for tr in tr_blocks:
        str_result = tr.find(class_="OrganicTitleContentSpan organic__title").text + "    " + str(tr.get("href"))
        # добавляем информацию о статье в список
        output_list.append(str_result)
    tr_blocks = soup.find_all('a', class_='mini-snippet__title')
    for tr in tr_blocks:
        if tr.find(class_="cutted"):
            str_result = tr.find(class_="cutted").text + "    " + str(tr.get("href"))
        else:
            str_result = tr.text + "    " + str(tr.get("href"))
        output_list.append(str_result)
    return output_list

def write_to_file(output_list, filename):
    with open(Path(BASE_DIR).joinpath(filename), "a", encoding="utf-8") as csvfile:
        for row in output_list:
            csvfile.write(f"{row}\n")


if __name__ == '__main__':

    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)