import os
from datetime import datetime
from flask import Blueprint, render_template, send_from_directory, redirect, url_for
from config import Config
from app.services.jellyfin import JellyfinService
from app.services.generator import NewsletterGenerator

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Check for existing newsletters
    if not os.path.exists(Config.NEWSLETTER_DIR):
        os.makedirs(Config.NEWSLETTER_DIR)

    files = sorted(os.listdir(Config.NEWSLETTER_DIR), reverse=True)
    newsletters = [f for f in files if f.endswith('.html')]

    newsletter_data = []
    if newsletters:
        for filename in newsletters:
            # expected format: newsletter_YYYY-MM-DD.html
            try:
                date_part = filename.replace('newsletter_', '').replace('.html', '')
                date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                label = date_obj.strftime('%b. %d')
            except ValueError:
                label = filename

            newsletter_data.append({
                'filename': filename,
                'label': label
            })

    if not newsletters:
        return render_template('index.html', newsletters=[], generating=True)

    return render_template('index.html', newsletters=newsletter_data, generating=False)

@main.route('/generate')
def generate():
    # Logic to fetch and generate
    days_back = Config.PERIODICITY_DAYS * Config.INITIAL_HISTORY_PERIODS

    jf_service = JellyfinService()
    if not jf_service.connected:
        return "Failed to connect to Jellyfin. Check logs/config.", 500

    items = jf_service.get_recent_media(days_back)

    generator = NewsletterGenerator()
    generator.generate_newsletters(items, jf_service)

    return redirect(url_for('main.index'))

@main.route('/newsletter/<path:filepath>')
def view_newsletter(filepath):
    return send_from_directory(Config.NEWSLETTER_DIR, filepath)
