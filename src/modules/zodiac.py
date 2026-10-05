from datetime import datetime
from monsterui import all as mui

SIGNS = {
    "Aries": ((3, 21), (4, 19)),
    "Taurus": ((4, 20), (5, 20)),
    "Gemini": ((5, 21), (6, 20)),
    "Cancer": ((6, 21), (7, 22)),
    "Leo": ((7, 23), (8, 22)),
    "Virgo": ((8, 23), (9, 22)),
    "Libra": ((9, 23), (10, 22)),
    "Scorpio": ((10, 23), (11, 21)),
    "Sagittarius": ((11, 22), (11, 28)),
    "Ophiuchus": ((11, 29), (12, 17)),
    "Sagittarius_": ((12, 18), (12, 21)),
    "Capricorn": ((12, 22), (1, 19)),
    "Aquarius": ((1, 20), (2, 18)),
    "Pisces": ((2, 19), (3, 20)),
}


def sun_sign(dt: datetime) -> str:
    for sign, ranges in SIGNS.items():
        start, end = ranges
        start_month, start_day = start
        end_month, end_day = end
        if (start_month == dt.month and start_day <= dt.day) or (dt.month == end_month and dt.day <= end_day):
            return sign.replace("_", "")


NAMES = {
    "Aries": "Baran",
    "Taurus": "Byk",
    "Gemini": "Bliźnięta",
    "Cancer": "Rak",
    "Leo": "Lew",
    "Virgo": "Panna",
    "Libra": "Waga",
    "Scorpio": "Skorpion",
    "Sagittarius": "Strzelec",
    "Ophiuchus": "Wężownik",
    "Capricorn": "Koziororzec",
    "Aquarius": "Wodnik",
    "Pisces": "Ryby",
}

ELEMENTS = {
    "Aries": "Ogień",
    "Taurus": "Ziemia",
    "Gemini": "Powietrze",
    "Cancer": "Woda",
    "Leo": "Ogień",
    "Virgo": "Ziemia",
    "Libra": "Powietrze",
    "Scorpio": "Woda",
    "Sagittarius": "Ogień",
    "Ophiuchus": "Eter",
    "Capricorn": "Ziemia",
    "Aquarius": "Powietrze",
    "Pisces": "Woda",
}

MODALITIES = {
    "Aries": "Kardynalna",
    "Taurus": "Stała",
    "Gemini": "Zmienna",
    "Cancer": "Kardynalna",
    "Leo": "Stała",
    "Virgo": "Zmienna",
    "Libra": "Kardynalna",
    "Scorpio": "Stała",
    "Sagittarius": "Zmienna",
    "Ophiuchus": "Nieznana",
    "Capricorn": "Kardynalna",
    "Aquarius": "Stała",
    "Pisces": "Zmienna",
}


def get_zodiac(date: datetime):
    sign = sun_sign(date)
    return mui.Card(
        mui.DivCentered(
            mui.DivCentered(NAMES[sign], header="Znak Słoneczny"),
            mui.DivCentered(ELEMENTS[sign], header="Żywioł"),
            mui.DivCentered(MODALITIES[sign], header="Jakość"),
        )
    )
