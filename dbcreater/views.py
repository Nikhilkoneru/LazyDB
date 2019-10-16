import json
import re
import subprocess
import urllib.request
from collections import OrderedDict
from io import BytesIO
from zipfile import ZipFile
import pandas
from django.core.management import call_command
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from cloudbackend import settings
import os
from django.http import HttpResponse, Http404
@csrf_exempt
def download(request):
    if request.method == "GET":
        file_path = "dbcreater/edbs/"+request.GET.get('db')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/sql")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        raise Http404
    return JsonResponse({"status": 400, "message": "Use Post Request"})


@csrf_exempt
def create(request):
    if request.method == "POST":
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            email = body["email"]
            url = body["url"]
            db = body["db"]
            response = save_and_export(email, url, db)
            return response
        except Exception as e:
            return JsonResponse({"status": 400, "message": e})
    else:
        return JsonResponse({"status": 400, "message": "Use Post Request"})


def save_and_export(email, url, database):
    dbname = "".join(" ".join(re.findall("[a-zA-Z]+", email.split("@")[0])).split())
    createDB(dbname)
    connectDBtoDjango(dbname)
    try:
        tables = read(url)
        for table in tables:
            create_and_save_table(dbname, url, database, table)
        exportDB(dbname, tables)
        deleteDB(dbname)
        return JsonResponse({"status": 200, "dblink": "http://127.0.0.1:8000/dbcreater/download/" + dbname + ".sql"})
    except Exception as e:
        deleteDB(dbname)
        return JsonResponse({"status": 400, "message": e})


def create_and_save_table(dbname, url, database, csv_df):
    columns = csv_df.columns
    dataTypes = csv_df.dtypes
    attrs = OrderedDict({'__module__': 'dbcreater.models'})
    columnsDic = OrderedDict()
    tableName = "".join(" ".join(re.findall("[a-zA-Z]+", url.split("/")[-1])).split())
    for i, val in enumerate(columns):
        columnType = getDynamicType(str(dataTypes[i]))
        attrs.update({val.lower(): columnType})
        columnsDic.update({val.lower(): ""})
    dynamicTable = type(tableName, (models.Model,), attrs)
    call_command('makemigrations', '--name=' + dbname)
    call_command('migrate', '--database=' + dbname)
    df = csv_df.to_dict(orient='records')
    for val in df:
        model = dynamicTable(**val)
        model.save(using=dbname)



def read(url):
    if "zip" in url:
        result = []
        url_m = urllib.request.urlopen(url)
        with ZipFile(BytesIO(url_m.read())) as my_zip_file:
            for contained_file in my_zip_file.namelist():
                try:
                    csv_df = pandas.read_csv(my_zip_file.open(contained_file))
                    if not csv_df.empty:
                        csv_df.columns = [c.lower() for c in csv_df.columns]
                        result.append(csv_df)
                except Exception as e:
                    pass
        return result if len(result) > 0 else "invalid"
    else:
        csv_df = pandas.read_csv(url)
        csv_df.columns = [c.lower() for c in csv_df.columns]
        return [csv_df]


def connectDBtoDjango(dbname):
    newDatabase = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': dbname,
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
    settings.DATABASES[dbname] = newDatabase


def exportDB(dbname, tables):
    file = open("dbcreater/edbs/%s.sql" % dbname, 'w+')
    p1 = subprocess.Popen(["mysqldump", "-u", "root", dbname], stdout=file, stderr=subprocess.STDOUT)
    p1.communicate()
    file.close()


def createDB(email):
    subprocess.check_call(['mysql', '-u', 'root', '-e', 'DROP DATABASE IF EXISTS ' + email])
    subprocess.check_call(['mysql', '-u', 'root', '-e', 'CREATE DATABASE ' + email])


def deleteDB(dbname):
    subprocess.check_call(['mysql', '-u', 'root', '-e', 'DROP DATABASE IF EXISTS ' + dbname])
    del settings.DATABASES[dbname]


def getDynamicType(type):
    return models.CharField(max_length=100)
