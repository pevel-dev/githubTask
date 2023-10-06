import time
from enum import Enum

from pydantic import BaseModel


class ErrorObj:
    def __init__(self, text: str, status: int):
        self.text = text
        self.status = status

    def __str__(self):
        return f"Api error! Status: {self.status}\nText:{self.text}"


class LimitTypes(Enum):
    core = "Core"


class RateLimit(BaseModel):
    limit_type: LimitTypes
    limit: int
    used: int
    remaining: int
    reset: int

    def get_time_left_to_reset(self) -> float:
        """
        Get time left to reset current rate limit
        :return: time in minutes
        """
        return (self.reset - time.time()) / 60

    def __str__(self):
        return f"{self.limit_type.value} limit. {self.used}/{self.limit} used. {self.remaining} left. Reset via {round(self.get_time_left_to_reset(), 2)} minutes"


class Organization(BaseModel):
    login: str
    public_repos: int
    followers: int


class Repo(BaseModel):
    id: int
    full_name: str
    commits_url: str
    contributors_url: str
    fork: bool
