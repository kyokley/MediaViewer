import random

interjections = [
    "Hip Hop Hooray!",
    "Yeah Yeah!",
    "Wazzzzzzzup!",
    "Woot Woot!",
    "Who do you love?",
    "It's a celebration!",
    "I give this two thumbs up!",
    "Just for you...",
    "Holla!",
    "Hollaback y'all!",
    "You're welcome...",
    "I'm a boss...",
]

failures = [
    "Sorry.",
    "I failed.",
    "I give up.",
]


def getInterjection():
    return random.choice(interjections)  # nosec


def getFailures():
    return random.choice(failures)  # nosec
