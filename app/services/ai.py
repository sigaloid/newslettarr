import requests
from config import Config

class AIService:
    def __init__(self):
        self.host = Config.OLLAMA_HOST
        self.model = Config.OLLAMA_MODEL

    def generate_headline(self, media_items):
        if not self.host:
            return "New this week on Jellyfin!"

        # Prepare context
        # We need a summarized list of items
        # Title, Genres, Overview (truncated)

        prompt_items = []
        for item in media_items[:15]: # Limit context size
            title = item.get('Name', 'Unknown Title')
            genres = ", ".join(item.get('Genres', []))
            overview = item.get('Overview', '')[:100] + "..." if item.get('Overview') else "No overview"
            prompt_items.append(f"- {title} ({genres}): {overview}")

        context_str = "\n".join(prompt_items)

        system_prompt = (
            "You are a friendly newsletter editor. "
            "Your job is to write a catchy, welcoming, human-sounding headline (1-2 sentences) "
            "summarizing the new movies and TV shows added this week. "
            "Highlight specific genres or titles if they stand out. "
            "Do not use colons or 'Subject:' format. Just the text."
        )

        user_prompt = (
            f"Here is the list of recently added media:\n{context_str}\n\n"
            "Write the headline:"
        )

        try:
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            }

            response = requests.post(f"{self.host}/api/generate", json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            headline = data.get('response', '').strip()
            # Remove quotes if the AI added them
            if headline.startswith('"') and headline.endswith('"'):
                headline = headline[1:-1]
            return headline

        except Exception as e:
            print(f"AI Generation failed: {e}")
            return "New additions to your library!"
