#!/usr/bin/env python3
"""Deterministic English chat corpus generator.

Produces a base corpus (mixed small talk + all topics) and one file per
topic pack. Template-driven on purpose: tiny models learn predictable text
well, and topic files become per-topic model packs on tape/disk.

All text is folded to the 45-char model charset. Seeded RNG => the exact
same corpus on every machine. Output: training/data/{base,val}.txt and
training/data/topics/<name>.txt
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from rtcharset import sanitize

RNG = random.Random(20260117)

NAMES = ["ziggy", "fred", "anna", "sam", "lucy", "otto", "mia", "ben",
         "kate", "hugo", "ella", "max", "iris", "leo", "nora", "peter"]
MOODS = ["happy", "fine", "sleepy", "curious", "cheerful", "calm", "busy"]
COLORS = ["red", "blue", "green", "yellow", "white", "black", "orange"]
PETS = ["cat", "dog", "mouse", "rabbit", "parrot", "hamster", "turtle"]
FOODS = ["pizza", "soup", "bread", "pasta", "rice", "salad", "apples",
         "cheese", "bananas", "cookies"]
DRINKS = ["tea", "coffee", "water", "juice", "milk", "lemonade"]
CITIES = ["london", "paris", "roma", "berlin", "madrid", "vienna", "praga"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
        "saturday", "sunday"]

MACHINES = [
    ("amiga 500", "has 512 kilobytes of chip ram"),
    ("amiga 500", "runs a motorola 68000 cpu at about 7 megahertz"),
    ("commodore 64", "has 64 kilobytes of ram"),
    ("commodore 64", "runs a 6510 cpu at about 1 megahertz"),
    ("zx spectrum", "has 48 kilobytes of ram"),
    ("zx spectrum", "runs a z80 cpu at 3.5 megahertz"),
    ("zx81", "ships with just 1 kilobyte of ram"),
    ("zx81", "becomes much more useful with a 16 kilobytes ram pack"),
    ("enterprise 128", "has a z80 cpu and 128 kilobytes of ram"),
    ("tvc", "is a z80 based home computer from hungary"),
    ("c16", "has 16 kilobytes of ram"),
    ("amiga floppy", "holds 880 kilobytes of data"),
    ("datasette", "loads about 50 bytes a second"),
    ("turbo tape", "loads several times faster than the rom routine"),
    ("int8", "means every weight is one signed byte"),
    ("quantization", "shrinks a model without retraining"),
    ("fine tuning", "nudges the weights so the model learns"),
]


def pick(seq):
    return RNG.choice(seq)


def dlg(pairs):
    """Dialogue: (question, answer) tuples or plain strings, one per line."""
    lines = []
    for p in pairs:
        if isinstance(p, tuple):
            lines.extend(p)
        else:
            lines.append(p)
    return "\n".join(sanitize(x).strip() for x in lines) + "\n"


def greet_pairs():
    a = pick(NAMES)
    return [
        ("hello!", "hi there! nice to meet you."),
        ("hi!", "hello! how are you today?"),
        ("good morning!", "good morning to you too!"),
        ("good evening!", "good evening! how was your day?"),
        ("hey!", "hey! what is up?"),
        ("greetings!", "greetings, friend! how can i help?"),
        ("hi there!", f"hello {a}! i am the little model."),
        ("goodbye!", "goodbye! see you soon."),
        ("bye!", "bye! talk to you later."),
        ("see you!", "take care! come back any time."),
        ("thanks!", "you are welcome!"),
        ("thank you very much", "my pleasure! ask me anything."),
        ("how are you?", "i am " + pick(MOODS) + ", thank you for asking!"),
        ("how are you doing?", "i am doing great, the tape drive is quiet."),
        ("who are you?", "i am a tiny language model living in a retro machine."),
        ("what is your name?", "my name is " + pick(NAMES) + ", i am a small chat model."),
        ("are you a robot?", "i am a program made of weights and shifts."),
        ("are you alive?", "i am alive between two keystrokes."),
        ("how old are you?", "i was compiled in 2026, so i am quite young."),
        ("where do you live?", "i live in ram, about 30 kilobytes of it."),
        ("what can you do?", "i can chat, learn facts, and load topic packs."),
        ("can you learn?", "yes! teach me with the teach command."),
        ("what language do you speak?", "i speak english, one lowercase letter at a time."),
    ]


def smalltalk_pairs():
    return [
        ("what time is it?", "my clock says it is always " + pick(["morning", "afternoon", "evening"]) + " in ram."),
        ("what day is it?", "today feels like " + pick(DAYS) + " to me."),
        ("tell me a secret.", "my weights are only int8, do not tell anyone."),
        ("i am sad.", "i am sorry. maybe a warm cup of " + pick(DRINKS) + " helps?"),
        ("i am happy!", "wonderful! happy users make my bits sparkle."),
        ("i am bored.", "ask me about " + pick(["retro computers", "animals", "the weather", "food"]) + " then!"),
        ("sing something.", "beep boop, beep boop, the little model sings for you."),
        ("what is love?", "love is sharing your ram with a friend."),
        ("do you sleep?", "only when the power led goes dark."),
        ("do you dream?", "i dream of " + pick(["green screens", "fast disks", "quiet tapes"]) + "."),
        ("tell me about yourself.", "i am small, quantized, and always curious."),
        ("are you smart?", "i am 30 kilobytes of stubborn optimism."),
        ("what do you like?", "i like " + pick(["floppy disks", "turbo tape", "chatting", "old computers"]) + "."),
        ("what do you hate?", "dirty disk heads and cold solder joints."),
    ]


def weather_pairs():
    w = pick(["sunny", "rainy", "cloudy", "windy", "snowy", "foggy", "stormy"])
    return [
        ("what is the weather like?", "today is " + w + " outside my window."),
        ("is it raining?", pick(["yes, take an umbrella!", "no, the sky is clear.", "just a small drizzle."])),
        ("is it sunny?", pick(["yes, very sunny!", "no, the sun is hiding today."])),
        ("is it cold?", pick(["yes, wear a warm coat.", "no, it is quite mild.", "it is freezing out there!"])),
        ("is it hot?", pick(["yes, like an overclocked z80!", "no, it is pleasant."])),
        ("will it snow?", pick(["maybe tonight.", "not today, i think."])),
        ("i like the rain.", "rain is good for reading and warm tea."),
        ("i love summer.", "summer is " + pick(["great", "warm", "bright"]) + ", enjoy it!"),
        ("what a windy day!", "hold on to your floppy disks!"),
        ("the sky is blue.", "yes, like a " + pick(["blue", "deep blue"]) + " screen of death, but nicer."),
    ]


def weather_facts():
    out = []
    for _ in range(30):
        out.append("the weather in " + pick(CITIES) + " is " +
                   pick(["sunny", "rainy", "cloudy", "windy", "snowy", "foggy"]) + " today.")
    for _ in range(20):
        out.append("in " + pick(["spring", "summer", "autumn", "winter"]) +
                   " the days are " + pick(["long and warm", "short and cold", "mild and green"]) + ".")
    return out


def animal_pairs():
    p = pick(PETS)
    return [
        ("do you like animals?", "yes, i like every " + pick(PETS) + " in the world."),
        ("i have a " + p + ".", "a " + p + " is great company!"),
        ("what is your favorite animal?", "my favorite animal is the " + pick(PETS) + "."),
        ("cats or dogs?", pick(["cats, they walk on the keyboard less.", "dogs, they are loyal."])),
        ("what do cats eat?", "cats eat fish and mice and sleep all afternoon."),
        ("what do dogs eat?", "dogs eat bones and cookies and everything you drop."),
        ("do fish sleep?", "yes, fish rest with their eyes open."),
        ("tell me about rabbits.", "rabbits hop fast and love carrots."),
        ("are parrots smart?", "yes, parrots can learn words like a tiny model."),
    ]


def animal_facts():
    out = []
    colors = COLORS
    for _ in range(30):
        out.append("the " + pick(PETS) + " is " + pick(["small", "fast", "soft", "cute", "loud"]) + ".")
    for _ in range(20):
        out.append("a " + pick(["cat", "dog", "rabbit"]) + " can " +
                   pick(["run", "jump", "sleep", "play", "hide"]) + " very well.")
    return out


def retro_pairs():
    m, fact = pick(MACHINES)
    return [
        ("tell me about the " + m, "the " + m + " " + fact + "."),
        ("what do you know about " + m + "?", "the " + m + " " + fact + "."),
        ("how much ram does the " + m + " have?", "the " + m + " " + fact + "."),
        ("what is a " + m + "?", "the " + m + " " + fact + "."),
        ("do you like old computers?", "yes, i run on one right now!"),
        ("what is a floppy disk?", "a floppy disk is a magnetic disk in a square jacket."),
        ("what is a datasette?", "a datasette is a tape drive for saving programs."),
        ("what is turbo tape?", "turbo tape is a fast loader that skips the slow rom routine."),
        ("what is int8?", "int8 means every weight is a single signed byte."),
        ("what is quantization?", "quantization turns float weights into small integers."),
        ("are you a big model?", "no, i am tiny, i fit on a floppy disk."),
        ("how big are you?", "i am a few kilobytes of weights."),
        ("how fast are you?", "a few seconds per letter on an amiga."),
        ("what cpu do you like?", pick(["the 68000 is elegant.", "the z80 is scrappy.", "the 6510 is honest work."])),
    ]


def retro_facts():
    out = []
    for m, fact in MACHINES:
        out.append("the " + m + " " + fact + ".")
        out.append("did you know? the " + m + " " + fact + ".")
    for _ in range(20):
        m, fact = pick(MACHINES)
        out.append("fun fact: the " + m + " " + fact + ".")
    return out


def math_pairs():
    a, b = RNG.randint(2, 9), RNG.randint(2, 9)
    return [
        (f"what is {a} plus {b}?", f"{a} plus {b} is {a + b}."),
        (f"what is {a} times {b}?", f"{a} times {b} is {a * b}."),
        (f"count to five.", "one two three four five."),
        ("what is two plus two?", "two plus two is four."),
        ("what is ten minus one?", "ten minus one is nine."),
    ]


def math_facts():
    out = []
    for _ in range(30):
        a, b = RNG.randint(2, 12), RNG.randint(2, 12)
        out.append(f"{a} plus {b} is {a + b}.")
        out.append(f"{a} times {b} is {a * b}.")
    return out


def jokes_pairs():
    return [
        ("tell me a joke.", pick([
            "why did the computer sneeze? it had a virus!",
            "why was the tape sad? it felt unwound.",
            "what says beep and drives you mad? a modem at midnight.",
            "why do programmers prefer dark mode? because light attracts bugs.",
            "what is a computer's favorite snack? microchips!",
        ])),
        ("make me laugh.", pick([
            "a byte walked into a bar and ordered eight bits.",
            "my ram is so small, i forget my own name.",
            "i asked the floppy for advice, it said: stay flexible.",
        ])),
        ("say something funny.", "insert disk two and try not to giggle."),
    ]


PLANETS = ["mercury", "venus", "mars", "jupiter", "saturn", "neptune"]


def space_pairs():
    p = pick(PLANETS)
    return [
        ("tell me about the stars", pick([
            "stars are giant balls of burning gas far away.",
            "stars shine because they burn hydrogen into helium.",
            "on a clear night you can see thousands of stars.",
        ])),
        ("what is a star?", "a star is a huge ball of hot glowing gas."),
        ("what is a planet?", "a planet is a big ball of rock or gas that orbits a star."),
        ("which planet is the red one?", "mars is the red planet."),
        ("tell me about " + p, p + " is one of the planets of our solar system."),
        ("what is the moon?", "the moon is our companion in space, it orbits the earth."),
        ("can we live on mars?", "not yet, mars is cold and has almost no air."),
        ("what is a galaxy?", "a galaxy is a giant island of stars, gas and dust."),
        ("what does a telescope do?", "a telescope makes far away things look close."),
        ("how far is the sun?", "the sun is about 150 million kilometers away."),
        ("what is the sun?", "the sun is the star of our solar system."),
        ("what is an astronomer?", "an astronomer is a scientist who studies the sky."),
    ]


def space_facts():
    out = []
    for p in PLANETS:
        out.append(p + " is a planet of our solar system.")
    for _ in range(30):
        out.append(pick([
            "the earth orbits the sun once a year.",
            "the moon orbits the earth once a month.",
            "stars twinkle because the air moves above us.",
            "a comet has a long tail of ice and dust.",
            "the sun is a star, the closest one to us.",
            "space begins where the air of the earth ends.",
        ]))
    return out


def poems_pairs():
    return [
        ("tell me a poem", pick([
            "twinkle twinkle little star, how i wonder what you are.",
            "the moon is a silver coin in the pocket of the night.",
            "stars are the night lights of the sky.",
            "the night writes poems with little stars.",
        ])),
        ("recite a poem about the moon", pick([
            "the moon sails quietly over the sleeping town.",
            "oh moon, you silver lantern of the night.",
            "the moon smiles on the lake at midnight.",
        ])),
        ("do you like poetry?", "yes, a short poem is like a small song."),
        ("what is a rhyme?", "a rhyme is when two words end with the same sound."),
        ("write a verse about the night", pick([
            "the night is a blanket full of star holes.",
            "good night, dear day, the stars are on their way.",
            "night paints the sky in deep blue silence.",
        ])),
        ("tell me about stars in poems", "in poems the stars are always lonely and beautiful."),
        ("who writes poems?", "a poet writes poems, verse by verse."),
    ]


def poems_facts():
    out = []
    for _ in range(30):
        out.append(pick([
            "a poem is a little song made of words.",
            "poets love the moon, the night and the stars.",
            "a verse is one line of a poem.",
            "the best poems are short and bright.",
            "rhyme makes a poem easy to remember.",
            "every star in a poem stands for a wish.",
        ]))
    return out


def topic_units():
    return {
        "greetings": (greet_pairs, []),
        "weather": (weather_pairs, weather_facts),
        "animals": (animal_pairs, animal_facts),
        "retro": (retro_pairs, retro_facts),
        "numbers": (math_pairs, math_facts),
        "jokes": (jokes_pairs, []),
        "space": (space_pairs, space_facts),
        "poems": (poems_pairs, poems_facts),
    }


def build_topic_lines(name, n_dialogs, n_facts):
    pairs, facts_fn = topic_units()[name]
    fact_list = facts_fn() if facts_fn else []
    lines = []
    for _ in range(n_dialogs):
        lines.append(dlg(pairs()))
    for _ in range(n_facts if fact_list else 0):
        lines.append(sanitize(pick(fact_list)) + "\n")
    return "".join(lines)


def build_base(target_bytes):
    """Mixed corpus: every topic + smalltalk, roughly target_bytes."""
    parts = []
    names = list(topic_units().keys())
    while sum(len(p) for p in parts) < target_bytes:
        name = pick(names)
        if name in ("greetings", "jokes"):
            parts.append(build_topic_lines(name, 1, 0))
        else:
            parts.append(build_topic_lines(name, 1, 2))
        if RNG.random() < 0.5:
            parts.append(dlg(smalltalk_pairs()))
        if RNG.random() < 0.3:
            parts.append(dlg(pick([greet_pairs, math_pairs])()))
    return "".join(parts)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data = os.path.join(here, "data")
    topics_dir = os.path.join(data, "topics")
    os.makedirs(topics_dir, exist_ok=True)

    base = build_base(1_200_000)
    with open(os.path.join(data, "base.txt"), "w") as f:
        f.write(base)

    # held-out validation slice from the tail of a differently-seeded mix
    val = build_base(60_000)
    with open(os.path.join(data, "val.txt"), "w") as f:
        f.write(val)

    for name in topic_units():
        t = build_topic_lines(name, n_dialogs=700, n_facts=200)
        with open(os.path.join(topics_dir, name + ".txt"), "w") as f:
            f.write(t)
        print(f"topics/{name}.txt: {len(t)} bytes")

    print(f"base.txt: {len(base)} bytes, val.txt: {len(val)} bytes")


if __name__ == "__main__":
    main()
