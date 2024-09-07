#!/usr/bin/env python3
import datetime
import json
import os

from dotenv import load_dotenv

from model.Notifier import Notifier
from model.RedisHandler import RedisHandler
from model.Scraper import Scraper


def save_houses(links, redis_handler, new_hook, update_hook):
    visited_links = redis_handler.load_existing_keys()
    for house in links:
        if not visited_links.get(house.id):
            new_hook.send_slack(house.name, house.pretty_print_slack())
        else:
            if house.price != visited_links[house.id]['price']:
                update_hook.send_slack("House price update",
                                       f"From {visited_links[house.id]['price']:,} to {house.price:,}. {house.link}")
        redis_handler.save_house(house)  # save every time to update the timestamp


def check_slack_webhooks():
    """Check if necessary Slack webhooks are provided in environment variables."""
    webhook_new = os.getenv('SLACK_WEBHOOK_NEW')
    webhook_update = os.getenv('SLACK_WEBHOOK_UPDATE')
    webhook_filtered = os.getenv('SLACK_WEBHOOK_FILTERED')
    webhook_filtered_update = os.getenv('SLACK_WEBHOOK_FILTERED_UPDATE')
    webhook_sold = os.getenv('SOLD_WEBHOOK')

    if not webhook_new or not webhook_update:
        raise Exception("Please provide minimal Slack webhooks (SLACK_WEBHOOK_NEW, SLACK_WEBHOOK_UPDATE)")

    if not webhook_filtered or not webhook_filtered_update or not webhook_sold:
        raise Exception(
            "Please provide Slack webhooks for filtered houses (SLACK_WEBHOOK_FILTERED, "
            "SLACK_WEBHOOK_FILTERED_UPDATE, SOLD_WEBHOOK)")

    return webhook_new, webhook_update, webhook_filtered, webhook_filtered_update, webhook_sold


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
                sold_webook.send_slack("House was sold or removed", json.dumps(house_data))


if __name__ == "__main__":
    load_dotenv()

    # Initialize Redis handler
    redis_handler = RedisHandler()

    # Check Slack webhooks
    slack_webhook_new, slack_webhook_update, slack_webhook_filtered, slack_webhook_filtered_update, slack_webhook_sold = check_slack_webhooks()

    # Initialize Notifiers
    new_house_notifier = Notifier(slack_webhook_new)
    update_house_notifier = Notifier(slack_webhook_update)
    filtered_house_notifier = Notifier(slack_webhook_filtered)
    filtered_update_notifier = Notifier(slack_webhook_filtered_update)
    sold_notifier = Notifier(slack_webhook_sold)

    # Initialize scraper
    scraper = Scraper()

    # Define URLs
    urls = [
        "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&distance=10&locality_district_id=72%7C73&locality_region_id=14&per_page=60&region=Rajhrad&region_entity_id=5820&region_entity_type=municipality",
        "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&distance=10&locality_district_id=73%7C72&locality_region_id=14&per_page=60&region=%C5%A0lapanice&region_entity_id=5838&region_entity_type=municipality"
    ]
    filtered_urls = [
        "https://www.sreality.cz/api/cs/v2/estates?building_condition=1%7C4%7C5%7C6&category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&czk_price_summary_order2=0%7C15000000&distance=10&estate_area=300%7C10000000000&locality_district_id=72%7C73&locality_region_id=14&per_page=60&region=Rajhrad&region_entity_id=5820&region_entity_type=municipality&usable_area=100%7C10000000000",
        "https://www.sreality.cz/api/cs/v2/estates?building_condition=1%7C4%7C5%7C6&category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&czk_price_summary_order2=0%7C15000000&distance=10&estate_area=300%7C10000000000&locality_district_id=73%7C72&locality_region_id=14&per_page=60&region=%C5%A0lapanice&region_entity_id=5838&region_entity_type=municipality&usable_area=100%7C10000000000"
    ]

    # Scrape filtered URLs first
    for filtered_url in filtered_urls:
        houses = scraper.scrape_all_pages(filtered_url)
        save_houses(houses, redis_handler, filtered_house_notifier, filtered_update_notifier)

    # Scrape base URLs
    for base_url in urls:
        houses = scraper.scrape_all_pages(base_url)
        save_houses(houses, redis_handler, new_house_notifier, update_house_notifier)

    # Check for houses that haven't been seen for over 3 days and remove them
    remove_old_houses(redis_handler, sold_notifier)

    print("Run finished")
