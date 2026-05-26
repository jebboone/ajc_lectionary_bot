from datetime import date
from lectionary import Lectionary

lectionary = Lectionary("data/movable.csv", "data/non_movable.csv")

for target in [date(2026, 1, 6), date(2026, 2, 22), date(2026, 4, 5), date(2026, 5, 31)]:
    print(target)
    for reading in lectionary.readings_for_date(target):
        print(" -", reading.kind, reading.title)
    print()
