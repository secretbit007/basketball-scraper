import os
import re
import requests
import json
import feedparser
import locale
import pandas as pd
from time import sleep
from typing import List
from slugify import slugify
from math import ceil
from urllib.parse import urlparse, parse_qs, unquote
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from bs4 import BeautifulSoup, Tag
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_col_index(table: Tag, col: str, left: bool = True):
    thead = table.find('thead')
    cells = thead.find_all('tr')[-1].find_all('th')

    if left:
        index = 0
        while True:
            if cells[index].get_text() == col:
                return index
            
            index += 1

            if index == len(cells):
                break
    else:
        index = len(cells) - 1
        while True:
            if cells[index].get_text() == col:
                return index
            
            index -= 1

            if index < 0:
                break
        
    return 0
