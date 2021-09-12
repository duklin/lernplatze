from argparse import ArgumentParser
from datetime import date, timedelta
from .lernplatze import get_slots_for_day


def main(args):
    sess = auth()

    get_slots_for_day(sess, date.today() - timedelta(1))

    # free_slots = {}

    # for day in [date.today() + timedelta(i) for i in range(8)]:
    #     day_str = day.strftime("%a, %d-%b")
    #     free_slots[day_str] = get_info(sess, day, args.min_timespan, args.until)

    # with open("status.json", "w", encoding="utf-8") as fout:
    #     json.dump(free_slots, fout, indent=4)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--min-timespan", default=5, type=int)
    parser.add_argument("--until", default=20, type=int)
    args = parser.parse_args()

    main(args)

