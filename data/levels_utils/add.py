import os, sqlite3, discord
import data.config as config

class response_object():
    def __init__(self, status: str, content = None):
        self.status = status
        self.content = content
