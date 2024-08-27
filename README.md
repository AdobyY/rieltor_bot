# Real Estate Bot

This is a Telegram bot built using `aiogram 3` that helps users find their dream apartments. The bot allows users to browse available apartments, save their favorite ones, and schedule viewings. Managers have access to a database of all apartments, users, and saved apartments in Excel format.

## Features

- **Apartment Browsing**: Users can browse available apartments with details such as address, price, region, number of rooms, floor, metro station, and additional information.
- **Saving Favorites**: Users can save their favorite apartments and access them later.
- **Viewing Scheduling**: Users can schedule a viewing for any apartment.
- **Manager Access**: Managers can download the entire database in Excel format, which includes different sheets for apartments, users, and saved apartments.

## Installation

### Prerequisites

- Python 3.8+
- `pip` (Python package installer)
- A Telegram bot token (from @BotFather)

### Step-by-Step Guide

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/real-estate-bot.git
    cd real-estate-bot
    ```

2. **Create a virtual environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database**:

    Ensure you have SQLite installed. The database will be created automatically based on the models provided in the `models.py` file.

5. **Configure environment variables**:

    Create a `.env` file in the root of the project and add your Telegram bot token:

    ```env
    BOT_TOKEN=your_telegram_bot_token_here
    ```

6. **Run the bot**:

    ```bash
    python main.py
    ```

## Usage

- **/start**: Start interacting with the bot.
- **/help**: Get a list of available commands.
- **/get_data**: (Managers only) Download the database in Excel format.
- **/updata_data**: (Managers only) Updata the database if the External Excel file with all apartments has been changed.

## Project Structure

RIELTOR_BOT/
│
├── app/
│   ├── database/
│   │   ├── models.py
│   │   ├── requests.py
│   ├── constants.py
│   ├── notify_managers.py
│   ├── handlers.py
│   ├── keyboards.py
│   ├── states.py
├── data.py
├── drop_tables.py
├── main.py
├── .gitignore
├── Procfile
├── README.md
└── requirements.txt
