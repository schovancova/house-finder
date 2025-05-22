#!/usr/bin/env python3
import datetime
import json
import os

from dotenv import load_dotenv

from model.Estate import get_days_since_first_seen
from model.Notifier import Notifier
from model.RedisHandler import RedisHandler
from model.Scraper import Scraper


def save_houses(links, redis_handler, new_hook, update_hook):
    visited_links = redis_handler.load_existing_keys()
    for house in links:
        if not visited_links.get(house.id):
            new_hook.send_slack(house.name, house.pretty_print_slack())
        else:
            if visited_links[house.id].get('first_seen'):
                house.first_seen = visited_links[house.id]['first_seen']
            if house.price != visited_links[house.id]['price']:
                update_hook.send_slack("House price update",
                                       f"From {visited_links[house.id]['price']:,} to {house.price:,}. {house.link}")
        redis_handler.save_house(house)  # save every time to update the timestamp


def check_slack_webhooks():
    """Check if necessary Slack webhooks are provided in environment variables."""
    webhook_new = os.getenv('SLACK_WEBHOOK_NEW')
    webhook_update = os.getenv('SLACK_WEBHOOK_UPDATE')
    webhook_flat = os.getenv('SLACK_WEBHOOK_FLAT')
    webhook_flat_update = os.getenv('SLACK_WEBHOOK_FLAT_UPDATE')
    webhook_sold = os.getenv('SOLD_WEBHOOK')

    if not webhook_new or not webhook_update:
        raise Exception("Please provide minimal Slack webhooks (SLACK_WEBHOOK_NEW, SLACK_WEBHOOK_UPDATE)")

    if not webhook_flat or not webhook_flat_update or not webhook_sold:
        raise Exception(
            "Please provide Slack webhooks for flat houses (SLACK_WEBHOOK_FLAT, "
            "SLACK_WEBHOOK_FLAT_UPDATE, SOLD_WEBHOOK)")

    return webhook_new, webhook_update, webhook_flat, webhook_flat_update, webhook_sold


def remove_old_houses(redis_handler, sold_webook):
    """Remove houses that haven't been updated for over 3 days."""
    three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
    three_days_ago_timestamp = three_days_ago.timestamp()

    # Retrieve all houses from Redis, this is much more efficient than going one by one due to my cheap tier of redis :c
    all_houses = redis_handler.load_existing_keys()

    for house_id, house_data in all_houses.items():
        last_seen = house_data.get('last_seen')
        if last_seen is not None:
            try:
                # Convert the Unix timestamp to a datetime object
                last_seen_datetime = datetime.datetime.fromtimestamp(float(last_seen))
            except ValueError:
                continue  # Skip if the timestamp conversion fails
            if last_seen_datetime.timestamp() < three_days_ago_timestamp:
                redis_handler.r.delete(house_id)
                print(f"Removed old house: {house_id}")
                sold_webook.send_slack(
                    f"House was sold or removed, first seen {get_days_since_first_seen(house_data.get('first_seen'))} days ago",
                    json.dumps(house_data))


if __name__ == "__main__":
    load_dotenv()

    # Initialize Redis handler
    redis_handler = RedisHandler()

    # Check Slack webhooks
    slack_webhook_new, slack_webhook_update, slack_webhook_flat, slack_webhook_flat_update, slack_webhook_sold = check_slack_webhooks()

    # Initialize Notifiers
    new_house_notifier = Notifier(slack_webhook_new)
    update_house_notifier = Notifier(slack_webhook_update)
    flat_house_notifier = Notifier(slack_webhook_flat)
    flat_update_notifier = Notifier(slack_webhook_flat_update)
    sold_notifier = Notifier(slack_webhook_sold)

    # Initialize scraper
    scraper = Scraper()

    # Define URLs
    house_urls = [
        "https://www.sreality.cz/api/v1/estates/search?category_type_cb=1&category_main_cb=2&category_sub_cb=37,39&locality_country_id=112&locality_region_id=14&locality_district_id=72,73&price_from=6000000&price_to=11000000&parking_lots=true&garage=true"
    ]
    flat_urls = [
        "https://www.sreality.cz/api/v1/estates/search?category_type_cb=1&category_main_cb=1&locality_country_id=112&locality_region_id=14&locality_district_id=72,73&price_from=6000000&price_to=11000000&parking_lots=true&garage=true&usable_area_from=55",
       ]

    # Scrape flat URLs first
    for flat_url in flat_urls:
        houses = scraper.scrape_all_pages(flat_url)
        save_houses(houses, redis_handler, flat_house_notifier, flat_update_notifier)

    # Scrape base URLs
    for base_url in house_urls:
        houses = scraper.scrape_all_pages(base_url)
        save_houses(houses, redis_handler, new_house_notifier, update_house_notifier)

    # Check for houses that haven't been seen for over 3 days and remove them
    remove_old_houses(redis_handler, sold_notifier)

    print("Run finished")
