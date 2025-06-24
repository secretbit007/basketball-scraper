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

def get_col_index(table: Tag, col: str, left: bool = True):
    thead = table.find('thead')
    cells = thead.find_all('tr')[-1].find_all('th')

    if left:
        for cell in cells:
            if cell.get_text() == col:
                return cells.index(cell)
    else:
        for cell in reversed(cells):
            if cell.get_text() == col:
                return cells.index(cell)
        
    return 0
