# Real Estate Scraper

A Python-based tool to scrape real estate listings for houses on sreality, track updates, and notify via Slack.

Disclaimer: This is a hobby project, it's not going to be perfect. I just needed this to run.

## Overview

This project consists of a set of Python scripts to scrape real estate data from specified sreality API, store the data in Redis, and send notifications via Slack for new listings and updates. It also cleans up old entries from Redis that haven't been updated for over 3 days.

The project is mostly geared towards searching around Brno, but feel free to adjust the targeted URLs.

## Features

- **Real Estate Scraping:** Scrapes real estate listings from specified URLs.
- **Data Storage:** Stores and updates real estate data in Redis.
- **Slack Notifications:** Sends notifications to Slack for new listings and price updates.
- **Old Data Cleanup:** Removes entries from Redis that haven't been updated for over 3 days.

## Prerequisites

- Python 3.6 or higher
- Redis server (use Heroku for easy setup and regular run for free)
- Slack webhook URLs
- Environment variables configuration

## Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/yourusername/real-estate-scraper.git
    cd real-estate-scraper
    ```

2. **Create a Virtual Environment (optional but recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

   3. **Install Required Packages:**

       ```bash
       pip install -r requirements.txt
       ```

      4. **Set Up Environment Variables:**

          Create a `.env` file in the project root directory with the following content:

          ```dotenv
          REDIS_HOST=localhost
          REDIS_PORT=6379
          REDIS_PASSWORD=your_redis_password

          SLACK_WEBHOOK_NEW=your_new_listing_webhook_url
          SLACK_WEBHOOK_UPDATE=your_update_webhook_url
          SLACK_WEBHOOK_FILTERED=your_filtered_listing_webhook_url
          SLACK_WEBHOOK_FILTERED_UPDATE=your_filtered_update_webhook_url
          SOLD_WEBHOOK=webhook
          ```
   
          `SLACK_WEBHOOK_NEW` and  `SLACK_WEBHOOK_UPDATE` is used for all houses within a radius. 
        
          `SLACK_WEBHOOK_FILTERED` and  `SLACK_WEBHOOK_FILTERED_UPDATE` is used for specific filter you may set up, e.g. "perfect houses". 
            
           `SOLD_WEBHOOK` is used for updates on houses that weren't seen for at least 3 days. 

## Usage

1. **Run the Script:**

    To start the scraper and process listings, run:

    ```bash
    python main.py
    ```

    This will:
    - Scrape data from the defined URLs.
    - Save the data to Redis.
    - Send notifications to Slack.
    - Remove old listings that haven't been updated for over 3 days.

2. **Update the Script:**

    - Modify `scraper.py` to add or update URLs and notification settings. (see the last section)
    - Adjust the `RedisHandler` class in `model/RedisHandler.py` as needed for your Redis setup.
    - Customize the `Notifier` and `Scraper` classes as per your requirements.

## Project Structure

- `scraper.py`: Main script to run the scraper, save data, and send notifications.
- `model/RedisHandler.py`: Contains the `RedisHandler` class for interacting with Redis.
- `model/Notifier.py`: Contains the `Notifier` class for sending Slack notifications.
- `model/Scraper.py`: Contains the `Scraper` class for scraping real estate data.
- `.env`: Environment variables configuration file.
- `requirements.txt`: Python package dependencies.

## How to update URLs to fit your locations 
1. Go to sreality site, put in some filters on location, e.g. https://www.sreality.cz/hledani/prodej/domy/rodinne-domy,vily/brno,brno-venkov?region=Rajhrad&region-id=5820&region-typ=municipality&vzdalenost=10
2. When loading the results, open dev tools and search for request with keyword `estates`
3. Congrats, this is now your API call you can use. Feel free to filter on multiple cities/villages and add each API call into the `urls` in `main.py`
2. Use `filtered_urls` as means to store your heavily filtered queries. 

With this setup you will see all houses in your radius, but also have a specific channel for your "ideal homes". 
