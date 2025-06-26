Trivial-Discord Quiz Bot
================

This is a Python-based quiz bot for Discord that enables team-based quiz competitions with live buzzing, admin-controlled scoring, automatic timing, and logging. It is designed to simulate a real-time quiz game in a Discord server with multiple participants.

Features
--------

- Team creation and joining
- Buzz-in system with queue handling
- Admin-only commands for controlling quiz flow
- Automatic countdown and skip if no one buzzes
- Logging of all answers and outcomes
- Score tracking and display

Commands
--------

| Command                   | Who Can Use It | Description                                              |
|--------------------------|----------------|-----------------------------------------------------------|
| !join <team>             | Any user       | Join an existing team                                     |
| !confirm_create <team>   | Any user       | Create a new team and join it                             |
| !start_quiz              | Admin only     | Start the quiz session                                    |
| !buzz                    | Team members   | Buzz in to attempt answering the current question         |
| !answer <your answer>    | Buzzed team    | Submit an answer for your team                            |
| !correct                 | Admin only     | Mark the team’s answer as correct (+10 points)            |
| !wrong                   | Admin only     | Mark the team’s answer as incorrect (-10 points)          |
| !score                   | Anyone         | View the current score of all teams                       |
| !end                     | Admin only     | End the quiz early and reset the state                    |
| !teams                   | Any user       | Display existing teams                                    |
| !leave                   | Any user       | Leave current team                                        |
| !skip                    | Admin          | Skip current question                                      

Setup Instructions
------------------

1. Clone the Repository  
   `git clone https://github.com/yourusername/discord-quiz-bot.git`  
   `cd discord-quiz-bot`

2. Install Dependencies  
   Make sure you have Python 3.10+ installed. Then run:  
   `pip install -r requirements.txt`

3. Set Up Your Environment  
   Create a `.env` file in the root directory and add your Discord bot token:  
   `DISCORD_TOKEN=your-bot-token-here`

4. Prepare the Quiz Dataset  
   Make sure there's a file called `quiz_bot_dataset.csv` in the project folder.  
   It should contain at least a column called `question` and optionally an `answer` column.

5. Run the Bot  
   `python quiz_bot.py`

Logging
-------

All quiz activity, including buzz-ins, timeouts, and scoring, is logged to a `quiz_log.txt` file generated during the quiz session. This helps in reviewing the performance or keeping a record.

Notes
-----

- Only users with administrator privileges on the server can start/end the quiz or mark answers as correct or incorrect.
- The bot supports multiple teams and manages answer timing automatically with a visible countdown.
- The project uses the `discord.py`, `pandas`, and `python-dotenv` libraries.
- This bot is live and deployed via Render for continuous hosting and operation.

