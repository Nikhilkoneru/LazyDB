import json

from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
from dbcreater.dynamic_db import save_and_export, download_helper
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
def assistant_hook(request):
    if request.method == "POST":
        logging.debug('Method:assistant_hook, Message: POST Request')
        try:
            req = json.loads(request.body.decode('utf-8'))
            action = req.get('queryResult').get('action')
            parameters = req.get('queryResult').get('parameters')
            if action == "CreateDB":
                email, url, db = parameters["email"], parameters["url"], parameters["db"]
                logging.debug(
                    "Method:assistant_hook, Message: POST request, Args: [action=%s, url=%s, email=%s, db=%s]", action,
                    url, email,
                    db)
                output = json.loads(save_and_export(email, url, db).content.decode('utf-8'))
                output_url = "%s/downloads?db=%s.%s" % (server_url, output["db_name"], output["file_type"])
                fulfillment_text = {"status": 200, "fulfillmentText": output_url}
            else:
                logging.debug("Method:assistant_hook, Args: action=%s, Message: Unknown Action", action)
                fulfillment_text = {"status": 200, "fulfillmentText": "Sorry can you try again?"}
            return JsonResponse(fulfillment_text, safe=False)
        except Exception as e:
            logging.error('Method:assistant_hook, Error: %s', e)
            return JsonResponse({"status": 400, "fulfillmentText": "Sorry cannot convert your file."},
                                safe=False)
    else:
        logging.debug('Method:assistant_hook, Args=[method=%s], Message: Cannot handle your request',
                      request.method)
        return JsonResponse({"status": 400, "fulfillmentText": "Sorry cannot convert your file."},
                            safe=False)


@csrf_exempt
def index(request):
    if request.method == "POST":
        logging.debug('Method:index, Message: POST Request')
        try:
            email, db = request.POST['email'], request.POST["db"]
            if "url" in request.POST and request.POST['url'] != "":
                url = request.POST['url']
                r = requests.get(url, allow_redirects=True)
                if "Content-Disposition" in r.headers.keys():
                    fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
                else:
                    fname = url.split("/")[-1]
                open(media_root+fname, 'wb').write(r.content)
                url = server_url+media_url+fname
            elif "file" in request.FILES:
                file = request.FILES['file']
                fs = FileSystemStorage()
                filename = fs.save(file.name, file)
                url = server_url + fs.url(filename)
            logging.debug("Method:index, Message:POST request, Args: [url=%s, email=%s, db=%s]", url, email, db)
            output = json.loads(save_and_export(email, url, db).content.decode('utf-8'))
            return download_helper(output["db_name"], output["file_type"])
        except Exception as e:
            logging.error('Method:index, Error: %s', e)
            return HttpResponse("error page")
    else:
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
