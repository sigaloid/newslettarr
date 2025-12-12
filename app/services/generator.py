import os
import re
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from config import Config
from dateutil import parser
from app.services.ai import AIService

class NewsletterGenerator:
    def __init__(self):
        self.template_env = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), 'app', 'templates')))
        self.ai_service = AIService()

    def _convert_trailer_url(self, url):
        if not url:
            return None
        # Basic YouTube conversion
        youtube_regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
        match = re.search(youtube_regex, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"
        return None

    def _process_item(self, item, jf_service=None, images_dir=None, relative_prefix=None):
        # Process trailer
        trailers = item.get('RemoteTrailers', [])
        trailer_url = None
        if trailers:
            trailer_url = self._convert_trailer_url(trailers[0].get('Url'))

        # Process Poster
        poster_url = None
        image_tags = item.get('ImageTags', {})
        primary_tag = image_tags.get('Primary')

        if primary_tag and jf_service and images_dir and relative_prefix:
            image_filename = f"{item['Id']}.jpg"
            destination_path = os.path.join(images_dir, image_filename)
            if not os.path.exists(destination_path):
                jf_service.download_poster(item['Id'], primary_tag, destination_path)

            if os.path.exists(destination_path):
                poster_url = f"{relative_prefix}/{image_filename}"

        # Clone item to avoid modifying original in place if used elsewhere
        processed = item.copy()
        processed['trailer_url'] = trailer_url
        processed['poster_url'] = poster_url
        return processed

    def generate_newsletters(self, all_items, jf_service):
        if not all_items:
            print("No items to generate newsletters for.")
            return

        # Ensure newsletter directory exists
        os.makedirs(Config.NEWSLETTER_DIR, exist_ok=True)

        # 1. Define periods
        # We start from NOW and go back in chunks of PERIODICITY_DAYS
        # until we exceed the oldest item's date or hit the INITIAL_HISTORY_PERIODS limit.

        now = datetime.now()
        period_days = Config.PERIODICITY_DAYS

        # We want to generate for the last N periods.
        # e.g., Period 0 (current/just finished): [now - 7 days, now]
        # Period 1: [now - 14 days, now - 7 days]

        generated_files = []

        for i in range(Config.INITIAL_HISTORY_PERIODS):
            end_date = now - timedelta(days=i * period_days)
            start_date = end_date - timedelta(days=period_days)

            date_folder_name = end_date.strftime('%Y-%m-%d')
            images_dir = os.path.join(Config.NEWSLETTER_DIR, date_folder_name)

            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            # Filter items for this period
            period_items = []
            for item in all_items:
                created_date = parser.isoparse(item.get('DateCreated'))

                # Make start/end date offset-aware if created_date is
                if created_date.tzinfo is not None:
                    if start_date.tzinfo is None:
                        start_date = start_date.astimezone(created_date.tzinfo)
                    if end_date.tzinfo is None:
                        end_date = end_date.astimezone(created_date.tzinfo)

                if start_date <= created_date < end_date:
                    period_items.append(self._process_item(item, jf_service, images_dir, date_folder_name))

            if not period_items:
                continue

            # Sort into Movies and Series
            movies = [item for item in period_items if item.get('Type') == 'Movie']
            series = [item for item in period_items if item.get('Type') == 'Series']

            # Generate Headline
            headline = self.ai_service.generate_headline(period_items)

            # Render HTML
            template = self.template_env.get_template('newsletter_template.html')
            date_range_str = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

            html_content = template.render(
                headline=headline,
                date_range=date_range_str,
                movies=movies,
                series=series
            )

            # Save file
            filename = f"newsletter_{date_folder_name}.html"
            filepath = os.path.join(Config.NEWSLETTER_DIR, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            generated_files.append(filename)
            print(f"Generated {filename}")

        return generated_files
