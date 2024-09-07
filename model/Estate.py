import time
from datetime import datetime


def get_image(estate_data):
    """Get the main image link for the estate"""
    images = estate_data.get('_links', {}).get('images', [])
    if images:
        return images[0].get('href')
    return None


def get_days_since_first_seen(first_seen):
    timestamp_dt = datetime.fromtimestamp(first_seen)
    now = datetime.now()
    difference = now - timestamp_dt
    return difference.days


class Estate:
    def __init__(self, estate_data, first_seen=None):
        self.id = str(estate_data.get('hash_id'))
        self.price = estate_data.get('price')
        self.location = estate_data.get('locality')
        self.is_auction = estate_data.get('is_auction', False)
        self.labels = estate_data.get('labelsAll', [None])[0]
        self.name = estate_data.get('name')
        self.link = self.generate_link(estate_data)
        self.images = get_image(estate_data)
        self.last_seen = time.time()
        self.first_seen = first_seen or time.time()

    def generate_link(self, estate_data):
        """Generate the link for the estate"""
        seo_locality = estate_data.get('seo', {}).get('locality')
        if self.id and seo_locality:
            return f"https://www.sreality.cz/detail/prodej/dum/rodinny/{seo_locality}/{self.id}"
        return None

    def to_dict(self):
        """Return estate data as a dictionary"""
        return {
            'id': self.id,
            'price': self.price,
            'location': self.location,
            'is_auction': self.is_auction,
            'labels': self.labels,
            'name': self.name,
            'link': self.link,
            'images': self.images,
            'last_seen': self.last_seen,
            'first_seen': self.first_seen,
        }

    def pretty_print_slack(self):
        """Format the estate data for posting to Slack."""
        price_display = "By Request" if self.price in [0, 1] else f"{self.price:,} Kc"
        days_since_first_seen = get_days_since_first_seen(self.first_seen)

        body = f"""
                *🏠 {self.name}*
                * *Price*: {price_display}
                * *Location*: {self.location}
                * *Auction*: {"Yes" if self.is_auction else "No"}
                * *Label*: {self.labels if self.labels else "N/A"}
                * *Photo*: {self.images}
                * *Link*: {self.link}
                * *First seen*: {days_since_first_seen} days ago
                """
        return body

    def __repr__(self):
        """String representation of the Estate object"""
        return f"Estate({self.name}, {self.price}, {self.location})"
