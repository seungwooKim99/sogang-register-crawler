from bot.config import driver_path, target_url, options, MYSQL_DATABASE_URI, MYSQL_DATABASE_TEST_URI, server_driver_path
from selenium import webdriver
from time import sleep
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from bot.util.xpaths import searchOption, contentTable, contentTableBodyId
from bot.util.columns import columns
from bot.util.departments import departments, departments_text_list
from bot.util.alert_service import compare_data

#days = []
#start_time = []
#end_time = []
# classrooms = []

firstDays = []
secondDays = []
firstStartTime = []
secondStartTime = []
firstEndTime = []
secondEndTime = []
firstTotalTime = []
secondTotalTime = []
classrooms = []

def lxmlToDataframe(index, html, isTotal, mid_df):
  '''
  크롤링한 데이터를 스크래핑하여 DataFrame으로 저장
  '''
  soup = BeautifulSoup(html, 'lxml')
  res = soup.find("tbody", id=contentTableBodyId)
  trs = res.find_all('tr')
  
  crawled_data = [[] for _ in range(26)]
  
  for tr in trs:
    tds = tr.find_all('td')
    for idx, td in enumerate(tds):
        if not td.find('span') == None:
            crawled_data[idx].append(td.find('span').text)
        else:
            crawled_data[idx].append(' ')
  print('Data Length : ' + str(len(crawled_data[0])))
  
  df = pd.DataFrame()
  
  for i in range(26):
    df[columns[i]] = crawled_data[i]
  
  subject_ids = []
  for i in range(len(crawled_data[0])):
      subject_ids.append('21-2-'+crawled_data[4][i]+'-'+crawled_data[5][i])
  
  if isTotal:
    df['subject_id'] = subject_ids
    df['department'] = ''
    return df
  else:
    for i in range(len(subject_ids)):
      if mid_df[mid_df['subject_id'] == subject_ids[i]]['department'].values == '':
        mid_df.loc[mid_df['subject_id'] == subject_ids[i],'department'] = departments[departments_text_list[index]]
      else:
        mid_df.loc[mid_df['subject_id'] == subject_ids[i],'department'] += ' {}'.format(departments[departments_text_list[index]])
    print('department id : {}'.format(departments[departments_text_list[index]]))
    return mid_df

'''
# old version
def split_day_time_classroom(x):
    arr = x.split(" ")
    if arr[0] == '' or arr[0] == '\xa0':
        days.append('')
        start_time.append('')
        end_time.append('')
        classrooms.append('')
    else:
        days.append(arr[0])
        start_end_time = arr[1].split('~')
        start_time.append(start_end_time[0])
        end_time.append(start_end_time[1])
        if len(arr) == 3 and arr[2] != '':
            classrooms.append(arr[2])
        else:
            classrooms.append('')
'''

def split_day_time_classroom(x):
    arr = x.split(" / ")
    if arr[0] == '' or arr[0] == '\xa0':
        firstDays.append('')
        secondDays.append('')
        firstStartTime.append('')
        secondStartTime.append('')
        firstEndTime.append('')
        secondEndTime.append('')
        firstTotalTime.append('')
        secondTotalTime.append('')
        classrooms.append('')
    else:
        if len(arr) == 2:
            arr1 = arr[0].split(' ')
            arr2 = arr[1].split(' ')
            firstDays.append(arr1[0])
            secondDays.append(arr2[0])
            
            firstTotalTime.append(arr1[1])
            secondTotalTime.append(arr2[1])
            
            firstStartTime.append(arr1[1].split('~')[0])
            firstEndTime.append(arr1[1].split('~')[1])
            
            secondStartTime.append(arr2[1].split('~')[0])
            secondEndTime.append(arr2[1].split('~')[1])
            
            if len(arr2) == 3 and arr2[2] != '':
                classrooms.append(arr2[2])
            else:
                classrooms.append('')
            
        else:
            arr = x.split(' ')
            firstDays.append(arr[0])
            secondDays.append(arr[0])
            
            firstTotalTime.append(arr[1])
            secondTotalTime.append(arr[1])
            
            firstStartTime.append(arr[1].split('~')[0])
            firstEndTime.append(arr[1].split('~')[1])
            
            secondStartTime.append(arr[1].split('~')[0])
            secondEndTime.append(arr[1].split('~')[1])
            
            if len(arr) == 3 and arr[2] != '':
                classrooms.append(arr[2])
            else:
                classrooms.append('')


def preprocessor(df):
  '''
  일부 컬럼 추가 및 수정을 위한 데이터 전처리기
  1. 학점 Int로 변형
  2. 수업 요일, 시작시간, 종료시간, 강의실 분리
  3. 대면 여부 추가
  4. 강의 언어 추가
  '''

  # 1. 학점 Int로 변형
  #df.loc[:, '학점'] = df.loc[:, '학점'].map(lambda x : int(float(x)))
  df.loc[:, '학점'] = df.loc[:, '학점'].map(lambda x : int(float(x)) if x in ['1.0', '2.0', '3.0'] else 0)
  
  # 2. 수업 요일, 시작시간, 종료시간, 강의실 분리
  df['수업시간_강의실'].map(lambda x : split_day_time_classroom(x))
  # old version
  #df['요일'] = days
  #df['시작시간'] = start_time
  #df['종료시간'] = end_time
  #df['강의실'] = classrooms
  
  # new version
  df['요일1'] = firstDays
  df['요일2'] = secondDays

  df['시간1'] = firstTotalTime
  df['시간2'] = secondTotalTime

  df['시작시간1'] = firstStartTime
  df['종료시간1'] = firstEndTime

  df['시작시간2'] = secondStartTime
  df['종료시간2'] = secondEndTime

  df['강의실'] = classrooms
  
  # 3. 대면 여부 추가
  df['대면여부'] = '미정'
  df.loc[df['비고'].map(lambda x : x.startswith('[비대면]')), '대면여부'] = '비대면'
  df.loc[df['비고'].map(lambda x : x.startswith('[대면]')), '대면여부'] = '대면'
  
  # 4. 강의 언어 추가
  df['강의언어'] = '한국어'
  df.loc[df['영어강의'] == 'O', '강의언어'] = '영어'
  df.loc[df['중국어강의'] == 'O', '강의언어'] = '중국어'
  
  # 5. 비고 에서 [대면], [비대면] 제거
  df.loc[:, '비고'] = df['비고'].map(lambda x: x.replace("[대면]", ""))
  df.loc[:, '비고'] = df['비고'].map(lambda x: x.replace("[비대면]", ""))
  df.loc[:, '비고'] = df['비고'].map(lambda x: x[1:] if len(x) > 0 and x[0] == ' ' else x)
  
  #6. updatedAt 추가
  df['updated_at'] = time.strftime('%Y년 %m월 %d일 %H시 %M분', time.localtime(time.time()))
  return df


def set_departments(df):
  # print('Sub Crawling start')
  for idx, department in enumerate(departments_text_list):
    start = time.time()
    print(' ')
    print('Processing step [ {} / 56 ]'.format(idx+2))
    print('{} crawling start'.format(departments_text_list[idx]))
    department_xpath = '//*[@id="{}"]'.format(departments[departments_text_list[idx]])
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    driver.get(target_url)
    driver.implicitly_wait(30)
    print('Entering Target Page...')
    
    # 대분류 Form 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['대분류']).click()

    # 학부 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['학부']).click()
    
    # 배경 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['배경']).click()

    # 소분류 Form 클릭
    sleep(0.5)
    driver.find_element_by_xpath(searchOption['소분류']).click()
    
    # 소분류 선택
    sleep(0.5)
    driver.find_element_by_xpath(department_xpath).click()

    # 검색 클릭
    sleep(1.0)
    driver.find_element_by_xpath(searchOption['검색']).click()
    
    print('Resource fetching...')
    html = None
    try:
      WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, contentTable)))
      print('Resource fetching done')
      print('Saving data...')
      
      html = driver.page_source
      df = lxmlToDataframe(idx, html, isTotal=False, mid_df=df)
      print("{} crawling done".format(departments_text_list[idx]))
    except:
      print('Resource fetching done. Nothing fetched.')
    finally:
      driver.close()
      
      # 중간 크롤링 결과 임시 테이블에 저장
      print('Saving data to DB...')
      engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
      conn = engine.connect()
      SQL = "SELECT * FROM s21_2_t"
      db_df = pd.read_sql(SQL, conn) 
      db_df.loc[:, 'department'] = df.loc[:, 'department']
      db_df.iloc[:, 1:].to_sql(name='s21_2_t', if_exists='replace', con=conn, index=True, index_label='id')
      conn.close()
      print('Saving done')
      print("WorkingTime: {} sec".format(time.time()-start))
      sleep(1)
  
  return df

def Crawler():
  '''
  학부 전체 테이블에 대해서 모든 정보를 크롤링 하는 함수
  '''
  
  print('Processing step [ 1 / 56 ]')
  print('Main Crawling start')
  driver = webdriver.Chrome(executable_path=driver_path, options=options)
  driver.get(target_url)
  driver.implicitly_wait(30)
  print('Entering Target Page...')
  
  # 대분류 Form 클릭
  sleep(0.5)
  driver.find_element_by_xpath(searchOption['대분류']).click()

  # 학부 클릭
  sleep(0.5)
  driver.find_element_by_xpath(searchOption['학부']).click()

  # 검색 클릭
  sleep(1.0)
  driver.find_element_by_xpath(searchOption['검색']).click()

  print('Resource fetching...')
  print(contentTable)
  element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, contentTable)))
  print('Resource fetching done')
  print('Saving data...')

  # 스크래핑
  html = driver.page_source
  result_df = lxmlToDataframe(0, html, isTotal=True, mid_df=None)
  print('Initial Main Crawling done.')
  driver.close()
  
  # 몇가지 컬럼 전처리
  result_df_ = preprocessor(result_df)

  # 초반 크롤링 결과 임시 테이블에 저장
  print('Saving data to DB...')
  engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
  conn = engine.connect()
  result_df_.to_sql(name='s21_2_t', if_exists='replace', con=conn, index=True, index_label='id')
  conn.close()
  print('Saving done')
  
  
  # 소분류(학부) 컬럼을 위한 추가 크롤링
  total_result_table = set_departments(result_df_)
  
  
  
  print(' ')
  print('Saving data to Main DB...')
  engine = create_engine(MYSQL_DATABASE_URI, encoding='utf-8')
  conn = engine.connect()
  SQL = "SELECT * FROM s21_2_t"
  total_db = pd.read_sql(SQL, conn) 
  total_db.iloc[:,1:].to_sql(name='s21_2', if_exists='replace', con=engine, index=True, index_label='id')
  conn.close()
  

  # alert_service
  compare_data(result_df_)


  print('Total Logic Done :)')
  return True