import logging
import re
import subprocess
import urllib.request
from collections import OrderedDict
from io import BytesIO
from zipfile import ZipFile

import pandas
from django.core.management import call_command
from django.db import models
from django.http import HttpResponse
from django.http import JsonResponse

from cloudbackend import settings

mysql_status = settings.mysql_status
mysql_username = settings.mysql_username
mysql_password = settings.mysql_password
server_url = settings.server_url
cursor = settings.cursor
export_file_path = settings.export_file_path
logging.basicConfig(filename='backend.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


def save_and_export(email, url, db, returntype):
    if mysql_status:
        logging.debug('Method:save_and_export, Args:[email=%s, url=%s, db=%s, returntype=%s]', email, url, db,
                      returntype)
        dbname = "".join(" ".join(re.findall("[a-zA-Z]+", email.split("@")[0])).split())
        createDB(dbname)
        connectDBtoDjango(dbname)
        try:
            tables_dataframe_list = read(url)
            logging.debug('Method:save_and_export, Args:[url=%s], Message: Num of tables=%s', url, len(tables_dataframe_list))
            for table in tables_dataframe_list:
                create_and_save_table(dbname, url, db, table)
            exportDB(dbname, tables_dataframe_list)
            deleteDB(dbname)
            if returntype == "json":
                return JsonResponse(
                    {"status": 200, "output": server_url + "/download?db=" + dbname + ".sql"})
            else:
                return HttpResponse(server_url + "/download?db=" + dbname + ".sql")
        except Exception as e:
            logging.debug('Method:save_and_export,  Error: %s', e)
            deleteDB(dbname)
            if returntype == "json":
                return JsonResponse({"status": 400, "output": "Unable to fullfill your request", "error": e})
            else:
                return HttpResponse("you can create error page and render it")
    elif returntype == "html":
        logging.debug('Method:save_and_export,  Error: Database Status False')
        return HttpResponse("Cannot handle your request")
    else:
        logging.debug('Method:save_and_export,  Error: Database Status False')
        return JsonResponse({"status": 400, "output": "Cannot handle your request"})


def create_and_save_table(dbname, url, database, csv_df):
    logging.debug('Method:create_and_save_table, Args:[dbname=%s, url=%s, database=%s, len(csv_df)=%s], Message: Create and Save Table', dbname,url,database,len(csv_df))
    columns = csv_df.columns
    data_types = csv_df.dtypes
    attrs = OrderedDict({'__module__': 'dbcreater.models'})
    columns_dic = OrderedDict()
    table_name = "".join(" ".join(re.findall("[a-zA-Z]+", url.split("/")[-1])).split())
    for i, val in enumerate(columns):
        column_type = getDynamicType(str(data_types[i]))
        attrs.update({val.lower(): column_type})
        columns_dic.update({val.lower(): ""})
    dynamic_table = type(table_name, (models.Model,), attrs)
    call_command('makemigrations', '--name=' + dbname)
    call_command('migrate', '--database=' + dbname)
    df = csv_df.to_dict(orient='records')
    for val in df:
        model = dynamic_table(**val)
        model.save(using=dbname)


def read(url):
    if "zip" in url:
        logging.debug('Method:read, Args:[url=%s], Message: ZIP File', url)
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
        return result
    else:
        logging.debug('Method:read, Args:[url=%s], Message: CSV File', url)
        csv_df = pandas.read_csv(url)
        csv_df.columns = [c.lower() for c in csv_df.columns]
        return [csv_df]


def connectDBtoDjango(dbname):
    logging.debug('Method:connectDBtoDjango, Args:[dbname=%s], Message: Connect DB to Django', dbname)
    new_database = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': dbname,
        'USER': mysql_username,
        'PASSWORD': mysql_password,
        'HOST': 'localhost',
        'PORT': '3306',
    }
    settings.DATABASES[dbname] = new_database


def exportDB(dbname, tables):
    logging.debug('Method:exportDB, Args:[dbname=%s], Message: Export DB', dbname)
    file = open(export_file_path + "%s.sql" % dbname, 'w+')
    p1 = subprocess.Popen(["mysqldump", "-u", mysql_username, "-p" + mysql_password, dbname], stdout=file,
                          stderr=subprocess.STDOUT)
    p1.communicate()
    file.close()


def createDB(dbname):
    logging.debug('Method:createDB, Args:[dbname=%s], Message: Drop and Create DB', dbname)
    cursor.execute("DROP DATABASE IF EXISTS " + dbname)
    cursor.execute("CREATE DATABASE " + dbname)
    cursor.execute("USE " + dbname)


def deleteDB(dbname):
    logging.debug('Method:deleteDB, Args:[dbname=%s], Message: Delete DB', dbname)
    cursor.execute("Drop DATABASE IF EXISTS " + dbname)
    del settings.DATABASES[dbname]


def getDynamicType(type):
    logging.info('Method:getDynamicType, Args:[type=%s]', type)
    if type == "int64":
        return models.IntegerField(default=None, blank=True, null=True)
    elif type == "float64":
        return models.FloatField(default=None, blank=True, null=True)
    elif type == "bool":
        return models.BooleanField()
    else:
        return models.CharField(max_length=100, blank=True, null=True)
