import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from django.http import HttpResponse
from django.template import loader
from dbcreater.dynamic_db import save_and_export
import logging

logging.basicConfig(filename='backend.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


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
                output = json.loads(save_and_export(email, url, db, "json").content)
                fulfillment_text = {"status": 200, "fulfillmentText": output["output"]}
            else:
                logging.debug("Method:assistant_hook, Args: action=%s, Message: Unknown Action", action)
                fulfillment_text = {"status": 200, "fulfillmentText": "Sorry can you try again?"}
            return JsonResponse(fulfillment_text, safe=False)
        except Exception as e:
            logging.warning('Method:assistant_hook, Error: %s', e)
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
            email, url, db = request.POST['email'], request.POST["url"], request.POST["typedb"]
            logging.debug("Method:index, Message:POST request, Args: [url=%s, email=%s, db=%s]", url, email, db)
            return save_and_export(email, url, db, "html")
        except Exception as e:
            logging.warning('Method:index, Error: %s', e)
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
            file_path = "dbcreater/edbs/" + request.GET.get('db')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/sql")
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                    return response
            else:
                logging.warning('Method:download, Args:[db=%s], Message: Unable to find this file',
                                request.GET.get('db'))
                return HttpResponse('Invalid Request')
        except Exception as e:
            logging.warning('Method:download, Error: %s', e)
            return HttpResponse('Invalid Request')

    else:
        logging.warning('Method:download, Message: Cannot handle your request')
        return JsonResponse({"status": 400, "message": "Cannot handle your request"})


@csrf_exempt
def create(request):
    if request.method == "POST":
        logging.debug('Method:create, Message: POST request')
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            email, url, db = body["email"], body["url"], body["db"]
            logging.debug("Method:create, Message:POST request, Args: [url=%s, email=%s, db=%s]", url, email, db)
            response = save_and_export(email, url, db, "json")
            return response
        except Exception as e:
            logging.warning('Method:create, Error: %s', e)
            return JsonResponse({"status": 400, "message": e})
    else:
        logging.debug('Method:create, Message: Cannot handle your request')
        return JsonResponse({"status": 400, "message": "Cannot handle your request"})
