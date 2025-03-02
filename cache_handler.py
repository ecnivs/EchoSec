# Cache Handler
from collections import OrderedDict

class LRUCache:
    """
    Implements a Least Recently Used (LRU) cache using an OrderedDict.
    When the cache reaches its capacity, the least recently used item is removed.
    """
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        """
        Retrieves the value associated with the given key if it exists in the cache.
        Moves the acceseed item to mark it as recently used.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        """
        Adds a key-value pair to the cache.
        If the key already exists, it moves it to the end to mark it as recently used.
        If the cache is at capacity, it removes the least recently used item.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

    def to_dict(self):
        """Returns the cache as a dictionary."""
        return dict(self.cache)

    def load(self, data):
        """Loads cache data from a dictionary."""
        self.cache = OrderedDict(data)


class LFUCache:
    """
    Implements a Least Frequently Used (LFU) cache.
    Tracks usage frequency and removes the least frequently used item when full.
    """
    def __init__(self, capacity):
        self.cache = {}
        self.freq = {}
        self.capacity = capacity

    def get(self, key):
        """
        Retrieves the value associated with the given key if it exists in the cache.
        Increases the access frequency of the key.
        """
        if key in self.cache:
            self.freq[key] += 1
            return self.cache[key]
        return None

    def put(self, key, value):
        """
        Adds a key-value pair to the cache.
        If the key exists, increments its frequency.
        If the cache is at capacity, removes the least frequently used item before adding a new one.
        """
        if key in self.cache:
            self.freq[key] += 1
        else:
            if len(self.cache) >= self.capacity:
                least_used = min(self.freq, key=self.freq.get, default=None)
                if least_used:
                    del self.cache[least_used]
                    del self.freq[least_used]
            self.cache[key] = value
            self.freq[key] = 1

    def to_dict(self):
        """Returns the cache and frequency data as a dictionary."""
        return {'cache': self.cache, 'freq': self.freq}

    def load(self, data):
        """Loads cache and frequency data from a dictionary."""
        self.cache = dict(data.get('cache', {}))
        self.freq = dict(data.get('freq', {}))

