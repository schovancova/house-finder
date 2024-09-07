# redis_handler/RedisHandler.py
import redis
import os
import json


class RedisHandler:
    def __init__(self):
        """Initialize Redis connection using environment variables."""
        self.r = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=os.getenv('REDIS_PORT'),
            password=os.getenv('REDIS_PASSWORD')
        )

    def load_existing_keys(self):
        """Load all existing keys and their corresponding values from Redis."""
        keys = self.r.keys('*')
        keys = [key.decode('utf-8') for key in keys]

        visited_links = {}
        if keys:
            values = self.r.mget(keys)
            for key, value in zip(keys, values):
                try:
                    json_value = json.loads(value.decode('utf-8')) if value else None
                    visited_links[key] = json_value
                except json.JSONDecodeError:
                    pass
        return visited_links

    def get_value(self, key):
        """Retrieve the value for a key and return it as a dictionary."""
        value = self.r.get(key)
        if value:
            try:
                return json.loads(value.decode('utf-8'))
            except json.JSONDecodeError:
                return None
        return None

    def save_house(self, house):
        """Save house to Redis."""
        self.r.set(house.id, json.dumps(house.to_dict()))
