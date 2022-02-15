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
from webdriver_manager.chrome import ChromeDriverManager


TOKEN = ""

BASE_DIR = Path(__file__).resolve(strict=True).parent

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG)
                    
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


class ZprStates(StatesGroup):
    ONE_ZPR_STATE = State()
    SUBSCRIBE_STATE = State()


@dp.callback_query_handler(text= 'one_zpr')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите запрос:")
    await ZprStates.ONE_ZPR_STATE.set()


@dp.callback_query_handler(text= 'btn_subscribe')
async def process_callback_button2(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите запрос:")
    await ZprStates.SUBSCRIBE_STATE.set()


@dp.callback_query_handler(text="one_zpr_true")
async def process_callback_button3(callback_query: types.CallbackQuery):
    await callback_query.message.answer( "Пожалуйста, ожидайте")
    browser = get_driver(False)
    zpr = callback_query.message.text 
    output_filename = f"{zpr}.csv"
    list = await connect_to_base(browser, zpr)
    for l in list:
        await callback_query.message.answer(l)
    browser.quit()
    await callback_query.message.answer("Выберите интересующий пункт меню:", reply_markup=inline_menu())
    

@dp.callback_query_handler(text="Menu")
async def process_callback_menu(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Выберите интересующий пункт меню:", reply_markup=inline_menu())


def inline_menu():
    inline_btn_1 = InlineKeyboardButton('Разовый запрос', callback_data='one_zpr')
    inline_btn_2 = InlineKeyboardButton('Подписка', callback_data='btn_subscribe')
    inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2)
    return inline_kb1 


@dp.callback_query_handler(text="btn_subscribe_true")
async def process_callback_button4(callback_query: types.CallbackQuery):
    id = callback_query.from_user.id 
    await bot.send_message(id, "Пожалуйста, ожидайте")
    zpr = callback_query.message.text.lower()
    output_filename = f"{zpr}.csv"
    flag = 1
    if Path.is_file(Path(BASE_DIR).joinpath(f"{zpr}_list.csv")):
        with open(Path(BASE_DIR).joinpath(f"{zpr}_list.csv"), "r", encoding="utf-8") as f:
            if str(id) in f.read():
                flag = 0
    if flag:
        with open(Path(BASE_DIR).joinpath(f"{zpr}_list.csv"), "a", encoding="utf-8") as f:
            f.write(str(id) + '\n')
    zapros = set()
    if Path.is_file(Path(BASE_DIR).joinpath("zapros.txt")):
        with open(Path(BASE_DIR).joinpath("zapros.txt"), "r", encoding="utf-8") as f:
            for line in f:
                zapros.add(line.rstrip())
    if zpr not in zapros:
        with open(Path(BASE_DIR).joinpath("zapros.txt"), "a", encoding="utf-8") as f:
            f.write(zpr + "\n")
    browser = get_driver(False)
    list = await connect_to_base(browser, zpr)
    for l in list:
        await bot.send_message(id, l)
    browser.quit()
    await callback_query.message.answer("Выберите интересующий пункт меню:", reply_markup=inline_menu())


@dp.message_handler(state=ZprStates.ONE_ZPR_STATE)
async def first_test_state_case_met(message: types.Message, state: FSMContext): 
    await state.reset_state()
    await bot.send_message(message.from_user.id, "Подтвердите правильность запроса\nВаш запрос:")
    inline_btn_1 = InlineKeyboardButton('Верно', callback_data='one_zpr_true')
    inline_btn_2 = InlineKeyboardButton('Изменить', callback_data='one_zpr')
    inline_btn_3 = InlineKeyboardButton('Меню', callback_data='Menu')
    inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2).add(inline_btn_3)
    await bot.send_message(message.from_user.id, message.text, reply_markup=inline_kb1)


@dp.message_handler(state=ZprStates.SUBSCRIBE_STATE)
async def first_test_state_case_met(message: types.Message, state: FSMContext):
    await state.reset_state()
    await bot.send_message(message.from_user.id, "Подтвердите правильность запроса\nВаш запрос:")
    inline_btn_1 = InlineKeyboardButton('Верно', callback_data='btn_subscribe_true')
    inline_btn_2 = InlineKeyboardButton('Изменить', callback_data='btn_subscribe')
    inline_btn_3 = InlineKeyboardButton('Меню', callback_data='Menu')
    inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2).add(inline_btn_3)
    await bot.send_message(message.from_user.id, message.text, reply_markup=inline_kb1)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()
    await message.reply("Выберите интересующий пункт меню:", reply_markup=inline_menu(), reply = False)


@dp.message_handler()
async def echo_message(message: types.Message):
    await message.reply("Выберите интересующий пункт меню:", reply_markup= inline_menu())


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
    with open(Path(BASE_DIR).joinpath("zapros.txt"), "r", encoding="utf-8") as f:
        for line in f:
            zapros.append(line.rstrip())
    if len(zapros) > len(set(zapros)):
            with open(Path(BASE_DIR).joinpath("zapros.txt"), "w", encoding="utf-8") as f:
                for line in set(zapros):
                    f.write(line+"\n")
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
        for news in await connect_to_base(browser, zpr):
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
    end_page = 3
    output_list = []
    for current_page in range(end_page):
        await asyncio.sleep(random.randint(2,5))
        print(f"Scraping page #{current_page}...")
        try:
            if current_page == 0:
                browser.get(base_url)
                await asyncio.sleep(5)
            else:
                try:
                    btn = browser.find_element_by_class_name("pager__item_kind_next")
                    btn.click()
                    await asyncio.sleep(3)
                except:
                    break
            output_list = output_list + parse_html(browser.page_source)
        except Exception as e:
            print(e)
            await asyncio.sleep(random.randint(3,5))
            browser.find_element_by_class_name("CheckboxCaptcha-Anchor").click()
            await asyncio.sleep(random.randint(3,5))
            print(f"Error connecting to {base_url}.")
            print(f"Attempt #{connection_attempts}.")
            output_list = output_list + parse_html(browser.page_source)
    return output_list


def parse_html(html):
    # создадим новый объект soup
    soup = BeautifulSoup(html, "html.parser")
    output_list = []
    tr_blocks = soup.find_all('a', class_='OrganicTitle-Link')
    for tr in tr_blocks:
        str_result = tr.find(class_="OrganicTitleContentSpan organic__title").text + "    " + str(tr.get("href")) + '\n'
        # добавляем информацию о статье в список
        output_list.append(str_result)
    tr_blocks = soup.find_all('a', class_='mini-snippet__title')
    for tr in tr_blocks:
        if tr.find(class_="cutted"):
            str_result = tr.find(class_="cutted").text + "    " + str(tr.get("href")) + '\n'
        else:
            str_result = tr.text + "    " + str(tr.get("href")) + '\n'
        output_list.append(str_result)
    return output_list

def write_to_file(output_list, filename):
    with open(Path(BASE_DIR).joinpath(filename), "a", encoding="utf-8") as csvfile:
        for row in output_list:
            csvfile.write(row)


if __name__ == '__main__':

    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)