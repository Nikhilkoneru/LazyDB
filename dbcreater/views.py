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
from django.template import loader
from django.shortcuts import render
import mysql.connector


mysql_status = False
mysql_username = "diamondnikhil"
mysql_password = "diamondnikhil"
try:
    mydb = mysql.connector.connect(
        host="localhost",
        user=mysql_username,
        passwd=mysql_password,
    )
    mysql_status = True
    cursor = mydb.cursor()
except mysql.connector.errors as error:
    mysql_status = False
    print("Connection to MySQL failed: {}".format(error))


def index(request):
    if request.method == "POST":
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            email = body["email"]
            url = body["url"]
            db = body["db"]
            #daimond check this out  -> no need to call create on form submit method I added one more parameter to save_and_export if the type is html it will return html
            return save_and_export(email, url, db, "html")
        except Exception as e:
            return HttpResponse("error page")
    # daimond check this out  -> else part is get request
    else:
        # daimond check this out  -> you need to render html form page here :-) and set onaction to the same index url no need to set it to create
        # when you do post it will go to the post thing and ask save_and_export to return html response
        #return HttpResponse("show form page here")
        context = {
        }
        return HttpResponse("show form page here")

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
    if mysql_status and request.method == "POST":
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            email = body["email"]
            url = body["url"]
            db = body["db"]
            # daimond check this out -> I added one more parameter to save_and_export if it is json it will return json else html page.
            response = save_and_export(email, url, db, "json")
            return response
        except Exception as e:
            return JsonResponse({"status": 400, "message": e})
    else:
        return JsonResponse({"status": 400, "message": "Incorrect Request"})

#daimond check this out -> one more parameter return type
def save_and_export(email, url, database, returntype):
    dbname = "".join(" ".join(re.findall("[a-zA-Z]+", email.split("@")[0])).split())
    createDB(dbname)
    connectDBtoDjango(dbname)
    try:
        tables = read(url)
        for table in tables:
            create_and_save_table(dbname, url, database, table)
        exportDB(dbname, tables)
        deleteDB(dbname)
        # daimond check this out
        if returntype == "json":
            return JsonResponse({"status": 200, "dblink": "http://127.0.0.1:8000/dbcreater/download/" + dbname + ".sql"})
        else:
            return HttpResponse("when user submits form -> this is the page you can show using above link")
    except Exception as e:
        deleteDB(dbname)
        #daimond check this out
        if returntype == "json":
            return JsonResponse({"status": 400, "message": e})
        else:
            #you can render html error page
            return HttpResponse("you can create error page and render it")




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
        'USER': 'vaidehi',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
    settings.DATABASES[dbname] = newDatabase


def exportDB(dbname, tables):
    file = open("dbcreater/edbs/%s.sql" % dbname, 'w+')
    p1 = subprocess.Popen(["mysqldump", "-u", mysql_username, dbname], stdout=file, stderr=subprocess.STDOUT)
    p1.communicate()
    file.close()


def createDB(email):
    cursor.execute("DROP DATABASE IF EXISTS " + email)
    cursor.execute("CREATE DATABASE " + email)
    cursor.execute("USE univDB;")


def deleteDB(dbname):
    cursor.execute("Drop DATABASE IF EXISTS " + dbname)
    del settings.DATABASES[dbname]


def getDynamicType(type):
    if (type == "int64"):
        return models.IntegerField(default=None, blank=True, null=True)
    elif (type == "float64"):
        return models.FloatField(default=None, blank=True, null=True)
    elif (type == "bool"):
        return models.BooleanField()
    else:
        return models.CharField(max_length=100, blank=True, null=True)
