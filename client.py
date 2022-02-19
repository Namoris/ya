from telethon import TelegramClient, events
from pathlib import Path
import os
import re
import logging


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


client = TelegramClient('session_name', api_id, api_hash)
BASE_DIR = Path(__file__).resolve(strict=True).parent
os.chdir(BASE_DIR)
print(os.getcwd())
with open(Path(BASE_DIR).joinpath(f"channels.csv"), 'r') as f:
    channel_list = [int(line.rstrip()) for line in f.readlines()]
bot_name = "_bot"


@client.on(events.NewMessage(pattern=r'(?i).*хрен'))
async def handler(event):
    await event.delete()




@client.on(events.NewMessage(from_users = channel_list))
async def handler(event):
    with open("zapros.txt", "r", encoding="utf-8") as f:
        zpr_list = [line.rstrip() for line in f.readlines()]
    new_news = event.raw_text.lower()
    for zpr in zpr_list:
        flag = 1
        for part_zpr in zpr.split():
            if not re.search(part_zpr, new_news):
                flag = 0
                break
        if flag:
            await client.send_message(bot_name, f"{zpr}&&&&&&&&{event.raw_text}")



client.start()
client.run_until_disconnected()