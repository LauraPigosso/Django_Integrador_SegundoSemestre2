from dateutil.relativedelta import relativedelta
import datetime

if __name__ == "__main__":


    for i in range(5):
        due_date = datetime.datetime.now() + relativedelta(months=+i)
        due_date = datetime.datetime.combine( due_date , datetime.datetime.min.time())

        print(due_date.replace(day=5))