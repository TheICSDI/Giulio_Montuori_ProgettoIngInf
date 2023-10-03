## Computer Engineering Project
This is a project for the Computer Engineering course at Politecnico di Milano for the 2022/2023 academic year. The idea is to build a Telegram bot that serves as a digital aid for playing the popular tabletop game Dungeons & Dragons 5th Edition. We're using Python and making use of the `asyncio` and `telegram-python-bot` libraries. I received a score of 29/30 on this project as part of the course evaluation.

For those interested in a more detailed breakdown, an official relation in Italian detailing the structure of the bot is available in this repository as official_relation.pdf.

## How to Use
The bot we used for evaluation isn't available for public use, but you can set up your own. Just create a new bot through `@BotFather` on Telegram and replace the `TOKEN` in line 26 of the `srs/dnd.py` file with your own bot token.

## Running the Program
To get the bot up and running, just type:
```properties
python src/dnd.py
```
