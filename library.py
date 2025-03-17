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
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from bs4 import BeautifulSoup, Tag
from concurrent.futures import ThreadPoolExecutor