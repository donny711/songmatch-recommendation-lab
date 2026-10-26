"""External search links for copyrighted songs; no recording is copied or streamed."""
from urllib.parse import urlencode

def listening_links(title, artist):
    query = f"{title} {artist}"
    return {
        "YouTube": "https://www.youtube.com/results?" + urlencode({"search_query":query+" official audio"}),
        "Apple Music": "https://music.apple.com/us/search?" + urlencode({"term":query}),
    }
