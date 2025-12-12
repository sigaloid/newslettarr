import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser
from jellyfin_apiclient_python import JellyfinClient
from config import Config

class JellyfinService:
    def __init__(self):
        self.client = JellyfinClient()
        self.client.config.app('Newslettarr', '0.0.1', 'newslettarr-server', 'newslettarr-id')
        self.client.config.data["auth.ssl"] = True

        if not Config.JELLYFIN_HOST or not Config.JELLYFIN_USERNAME or not Config.JELLYFIN_PASSWORD:
            print("Warning: Jellyfin credentials not fully set in environment.")
            self.connected = False
            return

        try:
            self.client.auth.connect_to_address(Config.JELLYFIN_HOST)
            self.client.auth.login(Config.JELLYFIN_HOST, Config.JELLYFIN_USERNAME, Config.JELLYFIN_PASSWORD)
            self.connected = True
            print("Successfully connected to Jellyfin.")
        except Exception as e:
            print(f"Failed to connect to Jellyfin: {e}")
            self.connected = False

    def download_poster(self, item_id, tag, destination_path):
        if not self.connected:
            return False

        url = f"{Config.JELLYFIN_HOST}/Items/{item_id}/Images/Primary?tag={tag}"
        headers = {
            "X-Emby-Token": self.client.config.data["auth.token"]
        }

        try:
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            if response.status_code == 200:
                with open(destination_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return True
            else:
                print(f"Failed to download image: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"Error downloading image for {item_id}: {e}")
            return False

    def get_recent_media(self, days_back):
        if not self.connected:
            return []

        # Target date is now - days_back
        # We need to find items older than this date to ensure we have EVERYTHING since then.
        target_date = datetime.now(timezone.utc) - timedelta(days=days_back)

        limit = 50
        max_limit = 2000 # Safety break
        items = []

        while limit <= max_limit:
            print(f"Fetching recently added with limit {limit}...")
            results = self.client.jellyfin.get_recently_added(media=["Movie", "Series"], limit=limit)

            if not results:
                break

            # Check the oldest item in this batch
            oldest_item = results[-1]
            oldest_date_str = oldest_item.get('DateCreated')
            oldest_date = parser.isoparse(oldest_date_str)

            items = results

            if oldest_date < target_date:
                # We have gone back far enough
                break

            if len(results) < limit:
                # We fetched everything available and still didn't reach the target date
                # (Server doesn't have enough history)
                break

            limit += 50

        # Filter strictly by the target date to return only relevant items
        # Note: 'DateCreated' is when it was added to Jellyfin.
        relevant_items = []
        for item in items:
            date_created = parser.isoparse(item.get('DateCreated'))
            if date_created >= target_date:
                relevant_items.append(item)

        # Sort by date created descending (newest first)
        relevant_items.sort(key=lambda x: parser.isoparse(x.get('DateCreated')), reverse=True)

        return relevant_items

    def get_image_url(self, item_id, tag, image_type="Primary"):
        return f"{Config.JELLYFIN_HOST}/Items/{item_id}/Images/{image_type}?tag={tag}"
