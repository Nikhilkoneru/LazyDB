import json

from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
from dbcreater.dynamic_db import download_helper
import logging
import requests
from cloudbackend import settings
import re

server_url = settings.server_url
media_url = settings.MEDIA_URL
media_root = settings.MEDIA_ROOT
logging.basicConfig(filename=settings.logging_file_path, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')



@csrf_exempt
def index(request):
        template = loader.get_template('dbcreater/index.html')
        logging.debug("Method:index, Message: render index page")
        return HttpResponse(template.render({}, request))


@csrf_exempt
def download(request):
    if request.method == "GET":
        try:
            logging.debug('Method:download, Args:[db=%s], Message: GET Request', request.GET.get('db'))
            db_file = request.GET.get('db').split(".")
            return download_helper(db_file[0], db_file[1])
        except Exception as e:
            logging.error('Method:download, Error: %s', e)
            return HttpResponse('Invalid Request')
    else:
        logging.error('Method:download, Message: Cannot handle your request')
        return JsonResponse({"status": 400, "message": "Cannot handle your request"})
