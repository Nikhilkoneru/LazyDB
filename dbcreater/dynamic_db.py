import logging
import re
import subprocess
import urllib.request
from collections import OrderedDict
from io import BytesIO
from zipfile import ZipFile
import os
import pandas
from django.core.management import call_command
from django.db import models
from django.http import HttpResponse
from django.http import JsonResponse
import pandas as pd
from cloudbackend import settings
from pathlib import Path
import time
import shutil
import tarfile
import random
import string
server_url = settings.server_url
export_file_path = settings.export_file_path
logging.basicConfig(filename=settings.logging_file_path, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')





def download_helper(db, file_type):
    logging.debug('Method:download_helper, Args:[db=%s]', db)
    file_path = "%s%s.%s" % (export_file_path, db, file_type)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/sql")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    else:
        logging.error('Method:download, Args:[db=%s], Message: Unable to find this file', file_path)
        return HttpResponse('Invalid Request')


