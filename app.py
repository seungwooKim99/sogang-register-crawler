#!/usr/bin/env python
# encoding=utf-8

from bot.service.current_semester import Crawler
from bot.service.sub.department_crawler import Crawler as department_crawler
from bot.service.sub.past_semester import Crawler as past_semester_crawler
from bot.util.mailer_service import mail_sender
import time

if __name__ == '__main__':
  start = time.time()
  Crawler()
  #department_crawler()
  #past_semester_crawler()
  print("Total WorkingTime: {} sec".format(time.time()-start))
