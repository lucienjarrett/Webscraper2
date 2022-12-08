from datetime import datetime, timedelta
import zipfile
import scrapy
import sqlalchemy
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import requests
import os
from dotenv import load_dotenv, dotenv_values
import wget
import ssl
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import math
from selenium.webdriver.common.keys import Keys
import pandas as pd
import os
import dbcontext
import csv
from numba import njit
import logging



load_dotenv()
config = dotenv_values(".env")

# fix certificate error
ssl._create_default_https_context = ssl._create_unverified_context

user_name = config['USERNAME']
password = config['PASSWORD']
web_url = config['URL']


#TODO this needs to prompt for date..
def set_date_range(start=None, end=None):
    startdate = '12/1/2022'
    enddate = '12/6/2022'
    if start ==None and end == None:
        start = startdate#datetime.strftime(datetime.today() - timedelta(days=3), '%m/%d/%Y')
        end = enddate#datetime.strftime(datetime.today(), '%m/%d/%Y')

    else:
        start = input("Enter start date here: ")
        end = input("Enter end date here: ")

    return (start, end)

# startdate = '11/1/2022'
# enddate = '11/1/2022'


# row_data = []
#columns for excel file.


def get_latest_chrome_driver():
    # get the latest chrome driver version number
    url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
    response = requests.get(url)
    version_number = response.text
    # build the donwload url
    download_url = "https://chromedriver.storage.googleapis.com/" + version_number + "/chromedriver_mac64.zip"
    # # download the zip file using the url built above
    latest_driver_zip = wget.download(download_url, 'chromedriver.zip')
    # # extract the zip file
    with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
        zip_ref.extractall()  # you can specify the destination folder path here
    # delete the zip file downloaded above
    os.remove(latest_driver_zip)


def get_web_driver(headless=True):
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver



def go_to_url(url, driver):
    driver.get(url=url)
    time.sleep(10)


def get_all_terminals(driver):
    print("Getting terminals........")
    locations = []
    terminal_count = driver.find_element(By.ID, "ContentPlaceHolder1_TermGrid_RecordCount")
    val = [i for i in terminal_count.text if i.isdigit()]
    count_of_terminals = int(''.join(val))

    for i in range(0, count_of_terminals):
        terminal = driver.find_element(By.ID, "ContentPlaceHolder1_TermGrid_TerminalId_" + str(i))
        locations.append(terminal.text)
    print(locations)
    # pd.to_csv(locations+".csv")

    return sorted(locations)


def login_to_web(driver, username=user_name, password=password):

    driver.get(url=web_url)
    # web username
    driver.find_element(By.ID, "UserName").send_keys(username)
    # # # web password
    driver.find_element(By.ID, "Password").send_keys(password)
    # # # click the submit button
    driver.find_element(By.ID, "Login").click()
    driver.implicitly_wait(10)  #


def set_params_for_report_page(Location, start_date, end_date, driver):
    # input the start date parameter
    driver.find_element(By.ID, "ContentPlaceHolder1_StartDatetxt").send_keys(start_date)
    # input the end date parameter
    driver.find_element(By.ID, "ContentPlaceHolder1_EndDatetxt").send_keys(end_date)
    # click the select button
    driver.find_element(By.ID, "ContentPlaceHolder1_selectbtn").click()
    time.sleep(3)
    driver.find_element(By.ID, "ContentPlaceHolder1_ModalPopupExtender3_foregroundElement")
    # input the terminal id
    driver.find_element(By.ID, "ContentPlaceHolder1_Search_tb").send_keys(Location)
    time.sleep(3)
    # click the search button
    driver.find_element(By.ID, "ContentPlaceHolder1_modalSearchBtn").click()
    time.sleep(3)
    # select the location name from the dropdown list
    driver.find_element(By.ID, "ContentPlaceHolder1_selectDropDownDDL").send_keys(Location)
    time.sleep(3)
    # click the select button
    driver.find_element(By.ID, "ContentPlaceHolder1_modalSelectBtn").click()
    time.sleep(3)
    # click the search button to display the table of data.
    driver.find_element(By.ID, "ContentPlaceHolder1_Searchbtn").click()
    time.sleep(5)

def calculate_page_count(num):
    page = 1
    for idx, i in enumerate(range(50, num)):
        if idx % 50 == 0:
            page += 1
    return page
#//*[@id="ContentPlaceHolder1_ReportGrid"]/tbody/tr[1]/td[1]/table/tbody/tr/td[11]/a
#document.querySelector("#ContentPlaceHolder1_ReportGrid > tbody > tr:nth-child(1) > td.GridPager > table > tbody > tr > td:nth-child(11) > a")
def pages_with_no_click_link(num):
    return True if num % 11 == 0 else False


##
def get_last_location(location = None):
    if location is not None:
        return location[-1]



def read_data_from_table(location, driver):
    print(f"reading html table. {location}......")
    driver.implicitly_wait(10)
    no_transactions = driver.find_element(By.XPATH, "//*[@id='ContentPlaceHolder1_ReportGrid']/tbody/tr/td").text
    if not no_transactions == "No transactions to display":
        try:
            record_count = driver.find_element(By.XPATH,"//*[@id='ContentPlaceHolder1_ReportGrid_itemCountlbl']").get_attribute(
                'innerHTML')
            val = [i for i in record_count if i.isdigit()]
            pages = calculate_page_count(int(''.join(val)))
            # row_data.clear()

            for page in range(1, pages +1):
                html_content = driver.find_element(By.XPATH, "//*[@id='ContentPlaceHolder1_ReportGrid']").get_attribute(
                        'innerHTML')
                if page == 1:
                    get_html_table_content(html_content, location)
                elif page > 1 and page <12:

                    links = "//*[@id='ContentPlaceHolder1_ReportGrid']/tbody/tr[1]/td[1]/table/tbody/tr/td[{}]/a".format(page)
                    time.sleep(3)
                    driver.find_element(By.XPATH, links).click()
                    time.sleep(3)
                    html_content = driver.find_element(By.XPATH,"//*[@id='ContentPlaceHolder1_ReportGrid']").get_attribute(
                        'innerHTML')
                    get_html_table_content(html_content, location)
                    time.sleep(3)
                elif page >=12:
                    page = page - 2
                    links = "//*[@id='ContentPlaceHolder1_ReportGrid']/tbody/tr[1]/td[1]/table/tbody/tr/td[{}]/a".format(
                        page)
                    time.sleep(3)
                    driver.find_element(By.XPATH, links).click()
                    time.sleep(3)
                    html_content = driver.find_element(By.XPATH,
                                                       "//*[@id='ContentPlaceHolder1_ReportGrid']").get_attribute(
                        'innerHTML')
                    get_html_table_content(html_content, location)
                    time.sleep(3)
            print(f" end reading html table. {location}......")


        except Exception as e:
            print(e)
        finally:
            # driver.refresh()
            if location == get_last_location(location):
                driver.close()
            else:
                driver.refresh()
    else:
        driver.refresh()


def check_date(dt):
    a = dt.split(' ')
    tran_date = a[0].replace('.', '')
    tran_date = datetime.strptime(tran_date, '%Y%m%d').strftime('%Y-%m-%d')
    tran_time = a[1]

    if tran_time >= '16:00:00' and tran_time <= '23:59:59':
        tran_date = datetime.strptime(tran_date, '%Y-%m-%d') + timedelta(days=1)
        # print(type(tran_date))
        return tran_date
    else:
        tran_date = datetime.strptime(tran_date, '%Y-%m-%d')
        # print(type(tran_date))
        return tran_date

'''
Adds rows to a list that has been declared globally.
parameter: 
    a - html content 

'''
def get_html_table_content(contents, location):
    soup = BeautifulSoup(contents, 'lxml')
    # get rows
    table_body = soup.find('tbody')
    rows = table_body.find_all('tr')
    # get headers
    columns = table_body.find_all('th')
    # table_header(columns)
    table_rows(rows, location)


'''
add rows to declared empty list
parameters: gets rows from html table
'''
row_data = []
def table_rows(rows, location):
    for i, row in enumerate(rows[3:]):
        cols = row.find_all('td')
        cols = [x.text.strip() for x in cols]
        if i <= 49 and len(cols) >= 19:
            row_data.append(cols)

    make_file_pandas(location, row_data)

def replace_value(value, char="$"):
    return value.replace(char, "")

def make_file_pandas(location, data):

    print(f"Creating pandas dataframe {location}")
    columns = ['Sequence Num', 'Trans Time', 'Type', 'FromAcct', 'FromAcct1', 'BatchID', 'PAN', 'Requested Amount',
               'Dispensed Amount', 'Cash Back', 'Surcharge Amount', 'Convenience Amount', 'Authorized Amount',
               'AuthCode', 'AuthMsg', 'RevCode', 'RevReason', 'Channel', 'Card Type']
    df = pd.DataFrame(data=data, columns=columns)
    df["Terminal_id"] = location
    df["TransDate"] = df['Trans Time'].apply(lambda x: check_date(x))
    df['Requested Amount'] = df['Requested Amount'].apply(lambda x: x.replace("$", ""))
    df['Dispensed Amount'] = df['Dispensed Amount'].apply(lambda x: x.replace("$", ""))
    df['Surcharge Amount'] = df['Surcharge Amount'].apply(lambda x: x.replace("$", ""))
    df['Convenience Amount'] = df['Convenience Amount'].apply(lambda x: x.replace("$", ""))
    df['Authorized Amount'] = df['Authorized Amount'].apply(lambda x: x.replace("$", ""))
    df['Cash Back'] = df['Cash Back'].apply(lambda x: x.replace("$", ""))
    df.to_csv(location+".csv")
    # post_records_to_database(df)


def remove_exist_file(file_name):
    try:
        if os.path.exists(file_name) and file_name.endswith(".csv"):
            print(f"removing previous file.....{file_name}")
            os.remove(file_name)
    except Exception as e:
        print(f"Error {e}")

def read_csv(file_name):
    print(f"Posting data {file_name}")

    file_name = file_name +".csv"
    records = pd.read_csv(f"//Users//lucienjarrett//PycharmProjects//pythonProject//{file_name}")
    conn = dbcontext.get_conn_string_pymssql()
    cursor = conn.cursor()
    try:
        for index, row in records.iterrows():
            seq = row["Sequence Num"]
            tran_date_time = row['Trans Time']
            type = row['Type']
            from_acct = row['FromAcct']
            batch_id = None #str(row['BatchID'].apply(lambda x: None if isna(x) else x))
            pan = row['PAN']
            req_amount = row['Requested Amount']
            dispense_amount = row['Dispensed Amount']
            cash_back = row['Cash Back']
            surcharge_amt = row['Surcharge Amount']
            conv_amt = row['Convenience Amount']
            auth_amt = row['Authorized Amount']
            auth_code = row['AuthCode']
            auth_message = row['AuthMsg']
            rev_code = float(row['RevCode'])
            rev_reason = str(row['RevReason'])
            terminal_id = row['Terminal_id']
            tran_date_conv = row["TransDate"]
            channel = row['Channel']
            card_type = row['Card Type']


            cursor.callproc("sp_ImportTransactionHistoryTest",
                            (seq, tran_date_time, type, from_acct, batch_id, pan, req_amount, dispense_amount, \
                             cash_back, surcharge_amt, conv_amt, auth_amt, auth_code, auth_message, \
                             rev_code, rev_reason, terminal_id, tran_date_conv, channel, card_type,))

        conn.commit()
        conn.close()
    except Exception  as e:
        print(f"Error is {e}")


def main():

    time_start = time.time()
    #####################################################################
    get_latest_chrome_driver()
    driver_val = get_web_driver(headless=True)
    login_to_web(driver=driver_val)
    go_to_url(url="https://sibisystems.com/SecurePages/TerminalManagement.aspx", driver=driver_val)
    locations = get_all_terminals(driver=driver_val)
    go_to_url(url="https://sibisystems.com/SecurePages/SIBI_Reports.aspx", driver=driver_val)
    go_to_url(url="https://sibisystems.com/SecurePages/Reporting/ReportPages/TransactionHistoryLookupReport.aspx",
               driver=driver_val)
    start, end = set_date_range()

    locations = ['EX030220', 'EX030221', 'EX030225', 'EX030226', 'EX030227', 'EX030228', 'EX03022C', 'EX03022D', 'EX03022E', 'EX03023D', 'EX03023E', 'EX03023F', 'EX030241', 'EX030242', 'EX030782', 'EX030784', 'EX035087', 'EX035088', 'EX035158', 'EX036072', 'EX036358', 'EX036838']

    for l in locations:
        row_data.clear()
        remove_exist_file(l+".csv")
        print(l, start, end)
        set_params_for_report_page(Location = l, start_date=start, end_date=end, driver=driver_val)
        read_data_from_table(l, driver=driver_val)
        read_csv(l)

    time_end = time.time()
    print("Time taken is {:.2f} mins ".format((time_end - time_start)/60))


if __name__ == "__main__":
    main()



