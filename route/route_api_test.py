from flask import Blueprint, request, jsonify, render_template
from tool.crawler import crawl_masothue
from models.model_tax_info import save_to_db, get_db_connection, save_data_error_to_db, update_crawler_status
from models.model_callback import CallbackInfo
from datetime import datetime
import traceback
import threading
import math
import requests
import json
import time

from tool.crawler import *

# Tạo Blueprint cho các route
bp = Blueprint('route_api_test', __name__)