# -*- coding: utf-8 -*-
"""
Created on Sat May  2 02:28:03 2020

@author: Antiochian

This script is able to automatically navigate through the various authentification
checks and cookie requirements of Panopto, and dig through the source code in order
to extract the raw .mp4 files of a whole folder of videos, before saving them to disk
in a specified folder.

This version of the scraper relies on a user/password stored in a plaintext 
file called SECRET.py and so may not be suitable for others, if they are 
nervous about password security

The install location can be changed by altering the "path" variable on line 38
"""
import SECRET

import os
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import string
import unicodedata

print("\n --- RUNNING --- ")

global USER,PASSWORD, DL_STATE
USER = SECRET.USER
PASSWORD = SECRET.PASSWORD
path = r"D:/Lectures/"
print("User credentials imported")

def download_file(session,url,output_filename):
    # Stream video into file, in chunks of 8.192KB at a time (avoid memory overflow)
    with session.get(url, stream=True) as r:
        r.raise_for_status()
        i = 0
        with open(output_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                print("\r",int(8.192*i)," KB downloaded...",end="")
                f.write(chunk)
                i += 1
    return

def fix_filename(filename):
    whitelist = "-_.() %s%s" % (string.ascii_letters, string.digits)
    char_limit = 200
    blacklist = "/"
    for r in blacklist: #replace blacklist chars with underscore
        filename = filename.replace(r,'-')
    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    return cleaned_filename[:char_limit]

def strip_title(innerHTML):
    target = "span>"
    landmarks = []
    for i in range(len(innerHTML)-5):
        if innerHTML[i:i+5] == target:
            landmarks.append(i)
    res = innerHTML[landmarks[0]+5:landmarks[1]-2]
    #strip illegal characters etc
    res = fix_filename(res) 
    return res

def navigate_shibboleth(driver, shibboleth_URL):
    global USER,PASSWORD
    driver.get(shibboleth_URL)
    driver.find_element_by_xpath('//*[@title="Oxford Account page"]').click()

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'loginForm')))
    driver.find_element_by_id("username").send_keys(USER)
    driver.find_element_by_id ("password").send_keys(PASSWORD)
    driver.find_element_by_name("Submit").click()
    
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'confirmPage')))
    driver.find_element_by_xpath('//*[@title="https://idp.shibboleth.ox.ac.uk"]').click()
    return driver

def initialise_driver():
    options = Options()
    options.add_argument("--mute-audio")
    
    driver = webdriver.Chrome(options=options)
    return driver
    
def main():
    #target URL (folder of videos)
    hijack = input("Enter folder URL: ")
    
    driver = initialise_driver()
    print("Driver initialised")
    
    dummy = "https://weblearn.ox.ac.uk/access/basiclti/site/850080a2-a7d7-43cf-acd5-4940b3089790/content:737"
    driver = navigate_shibboleth(driver,dummy)
    print("Shibboleth navigated")

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'resultsDiv'))) #wait for page to load
    driver.get(hijack)
    print("Course hijacked")
    time.sleep(1)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'resultsDiv')))
    listresults = driver.find_element_by_id("resultsDiv")
    #print(listresults.find_element_by_id("contentHeaderText").get_attribute("span"))

    #Get folder name, check with user to confirm
    A = listresults.find_element_by_css_selector("a.folder-link.non-featured-folder-link.redundant-folder-link")
    folder = A.get_attribute("innerHTML")
    folder = fix_filename(folder)
    choice = input("Folder '"+folder+"' found. Continue? (Y/N): ")
    
    #Set up output folder
    if choice.lower() != "y":
        print("Cancelled.")
        return
    try:
        os.mkdir(path+folder)    
    except:
        print("Folder already exists.")
    else:
        print("Folder created")
        
    #generate job queue
    vid_links = listresults.find_elements_by_css_selector("a.detail-title")
    total = len(vid_links)
    print(total," videos found.")
    queue = []
    for vid in vid_links:
        vid_link = vid.get_attribute("href")
        vid_title = path+folder+"/"+strip_title(vid.get_attribute("innerHTML"))+".mp4"
        queue.append((vid_link, vid_title))
    
    #start downloading
    t0 = time.time()
    i = 0
    for item in queue:
        i += 1
        (vid_link, vid_title) = item
        driver.get(vid_link)
        direct_URL = driver.find_element_by_name("twitter:player:stream").get_attribute("content")
        driver.get(direct_URL)
        refined = driver.current_url
        print("Downloading video ",i,"/",total,": ",vid_title)

        #load acquired cookies into requests.session object
        cookies = driver.get_cookies()
        s = requests.Session()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])
            
        #get mp4 file
        download_file(s,refined,vid_title)
        print("\tFile outputted to ", vid_title)
    
    print("Completed in", (time.time()-t0)//60,"min.")
    driver.quit()
    return

main()


