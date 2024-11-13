import time
from datetime import datetime


def get_image(estate_data):
    """Get the main image link for the estate"""
    images = estate_data.get('advert_images', [])
    if images:
        return 'https:' + images[0] + '?fl=res,1800,1800,1|wrm,/watermark/sreality.png,10|shr,,20|webp,60'
    return None


def get_days_since_first_seen(first_seen):
    timestamp_dt = datetime.fromtimestamp(first_seen)
    now = datetime.now()
    difference = now - timestamp_dt
    return difference.days


class Estate:
    def __init__(self, estate_data, first_seen=None):
        city = estate_data.get('locality').get('city_seo_name')
        citypart = estate_data.get('locality').get('citypart_seo_name') or city
        street = estate_data.get('locality').get('street_seo_name') or ""
        self.location = city + "-" + citypart + "-" + street
        self.id = str(estate_data.get('hash_id'))
        self.price = estate_data.get('price')
        self.name = estate_data.get('advert_name')
        self.link = self.generate_link(estate_data)
        self.images = get_image(estate_data)
        self.last_seen = time.time()
        self.first_seen = first_seen or time.time()

    def generate_link(self, estate_data):
        """Generate the link for the estate"""
        if self.id and self.location:
            if estate_data.get('category_main_cb').get("name") == "Byty":
                category = "byt"
            else:
                category = "dum"
            return f"https://www.sreality.cz/detail/prodej/{category}/rodinny/{self.location}/{self.id}"
        return None

    def to_dict(self):
        """Return estate data as a dictionary"""
        return {
            'id': self.id,
            'price': self.price,
            'location': self.location,
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
                * *Photo*: {self.images}
                * *Link*: {self.link}
                * *First seen*: {days_since_first_seen} days ago
                """
        return body

    def __repr__(self):
        """String representation of the Estate object"""
        return f"Estate({self.name}, {self.price}, {self.location})"
