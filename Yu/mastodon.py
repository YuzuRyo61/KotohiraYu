from mastodon import Mastodon

from .config import config

mastodon = Mastodon(
    access_token=config['instance']['access_token'],
    api_base_url=config['instance']['address']
)
