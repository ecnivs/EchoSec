import requests
import socks
import socket
from bs4 import BeautifulSoup

# Use Tor as a proxy
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket

DARK_WEB_SEARCH_URL = "http://ahmiafi7t2aurl.onion/search/"  # Example search engine

def dark_web_scan(query, limit=5):
    """Scans the dark web for leaked data related to a given query."""
    url = f"{DARK_WEB_SEARCH_URL}?q={query}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return "Failed to fetch dark web results."

        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True)][:limit]

        return links if links else "No results found on the dark web."

    except requests.exceptions.RequestException as e:
        return f"Error accessing dark web: {e}"

# Example usage
print(dark_web_scan("example@gmail.com"))

