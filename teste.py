from datetime import date

year, month, initDay, finalDay = (2017, 8, 1, 28)

def getWeeks(year, month, initDay, finalDay):

    weekCount = None
    week = 1

    for day in range(initDay+1, finalDay+1):
        data = date(year, month, day)

        if weekCount == 6 or day == finalDay:
            print('Semana {}'.format(week))
            week = week + 1

        weekCount = data.weekday()

getWeeks(year, month, initDay, finalDay)
