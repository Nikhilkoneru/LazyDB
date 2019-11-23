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
from django.apps import apps
mysql_status = settings.mysql_status
mysql_username = settings.mysql_username
mysql_password = settings.mysql_password
server_url = settings.server_url
cursor = settings.cursor
export_file_path = settings.export_file_path
mango_client = settings.mango_client
logging.basicConfig(filename=settings.logging_file_path, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')


def get_export_type(db_type):
        return "sql"


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))


def save_and_export(email, url, db_type):
    if mysql_status:
        logging.debug('Method:save_and_export, Args:[email=%s, url=%s, db=%s]', email, url, db_type)
        dbname = "".join(" ".join(re.findall("[a-zA-Z]+", email.split("@")[0])).split())
        createDB(dbname, db_type)
        connectDBtoDjango(dbname, db_type)
        try:
            call_command('migrate', 'mysql_support', 'zero', '--database=' + dbname, '--noinput')
            call_command('makemigrations', '--no-input', '--name', dbname)
            call_command('migrate', '--database=' + dbname, '--noinput')
        except Exception as e:
            logging.debug('Method:save_and_export, Error:%s', e)
            pass
        try:
            output = read(url, db_type)
            tables_dataframe_list, table_names = output["dataframes"], output["table_names"]
            logging.debug('Method:save_and_export, Args:[url=%s], Message: Num of tables=%s', url,
                          len(tables_dataframe_list))
            model_names = []
            for table, name in zip(tables_dataframe_list, table_names):
                try:
                    model_names.append(create_and_save_table(dbname, url, db_type, table, name))
                except Exception as e:
                    logging.debug('Method:save_and_export, Error:%s, Message: Error with csv=%s', e, name)
                    pass

            exportDB(dbname, table_names, db_type)
            deleteFiles()
            deleteDB(dbname, db_type)
            return JsonResponse({"status": 200, "db_name": dbname, "file_type": get_export_type(db_type)})
        except Exception as e:
            logging.debug('Method:save_and_export,  Error: %s', e)
            deleteDB(dbname, db_type)
            return JsonResponse({"status": 400, "db_name": dbname, "file_type": get_export_type(db_type), "error": e})
    else:
        logging.debug('Method:save_and_export, output:error, Database Status False')
        return JsonResponse({"status": 400, "output": "error"})


def create_and_save_table(dbname, url, database, csv_df, table_name):
    logging.debug(
        'Method:create_and_save_table, Args:[dbname=%s, url=%s, database=%s, len(csv_df)=%s], Message: Create and '
        'Save Table',
        dbname, url, database, len(csv_df))
    columns = csv_df.columns
    data_types = csv_df.dtypes

    class Meta:
        db_table = table_name

    attrs = OrderedDict({'__module__': 'mysql_support.models', 'Meta': Meta})
    columns_dic = OrderedDict()
    for i, val in enumerate(columns):
        column_type = getDynamicType(str(data_types[i]))
        attrs.update({val.lower(): column_type})
        columns_dic.update({val.lower(): ""})
    try:
        dynamic_table = apps.get_model("mysql_support."+table_name)
    except Exception as e:
        dynamic_table = type(table_name, (models.Model,), attrs)
        call_command('makemigrations', 'mysql_support', '--no-input', '--name', dbname)
        call_command('migrate', 'mysql_support', '--database=' + dbname, '--noinput')
    df = csv_df.to_dict(orient='records')
    for val in df:
        model = dynamic_table(**val)
        model.save(using=dbname)
    return dynamic_table


def read(url, dbtype):
    if "zip" in url:
        logging.debug('Method:read, Args:[url=%s], Message: ZIP File', url)
        result = []
        url_m = urllib.request.urlopen(url)
        table_names = []
        with ZipFile(BytesIO(url_m.read())) as my_zip_file:
            for contained_file in my_zip_file.namelist():
                if not Path(contained_file).stem.startswith('.'):
                    try:
                        csv_df = pandas.read_csv(my_zip_file.open(contained_file))
                        if not csv_df.empty:
                            csv_df = csv_df.where(pd.notnull(csv_df), None)
                            csv_df.columns = [c.lower() for c in csv_df.columns]
                            result.append(csv_df)
                            table_names.append(
                                "".join(" ".join(re.findall("[a-zA-Z]+", Path(
                                    contained_file).stem)).split()))
                    except Exception as e:
                        pass
        return {"dataframes": result, "table_names": table_names}
    else:
        logging.debug('Method:read, Args:[url=%s], Message: CSV File', url)
        csv_df = pandas.read_csv(url)
        csv_df = csv_df.where(pd.notnull(csv_df), None)
        csv_df.columns = [c.lower() for c in csv_df.columns]
        table_name = [
            "".join(" ".join(re.findall("[a-zA-Z]+", Path(url).stem)).split())]
        return {"dataframes": [csv_df], "table_names": table_name}


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


def connectDBtoDjango(dbname, db_type):
    logging.debug('Method:connectDBtoDjango, Args:[dbname=%s,db_type=%s], Message: Connect DB to Django', dbname,
                  db_type)
    new_database = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': dbname,
        'USER': mysql_username,
        'PASSWORD': mysql_password,
        'HOST': 'localhost',
        'PORT': '3306',
    }
    settings.DATABASES[dbname] = new_database


def exportDB(dbname, tables, db_type):
    logging.debug('Method:exportDB, Args:[dbname=%s], Message: Export DB', dbname)
    file = open(export_file_path + "%s.sql" % dbname, 'w+')
    p1 = subprocess.Popen(["mysqldump", "-u", mysql_username, "-p" + mysql_password, dbname] + tables, stdout=file,
                          stderr=subprocess.STDOUT)
    p1.wait()
    p1.communicate()
    file.close()


def createDB(dbname, db_type):
    logging.debug('Method:createDB, Args:[dbname=%s,db_type=%s], Message: Drop and Create DB', dbname, db_type)
    if db_type == "mysql":
        cursor.execute("DROP DATABASE IF EXISTS " + dbname)
        cursor.execute("CREATE DATABASE " + dbname)
        cursor.execute("USE " + dbname)


def deleteDB(dbname, db_type):
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
        return models.CharField(max_length=1000, blank=True, null=True, default=None)


def deleteMigrations():
    logging.info('Method:deleteMigrations, Message: Deleting')
    folder = os.getcwd() + '/mysql_support/migrations/'
    try:
        shutil.rmtree(folder + '__pycache__/')
    except Exception as e:
        pass
    for the_file in os.listdir(folder):
        if the_file != "__init__.py":
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)


def deleteFiles():
    folder = os.getcwd() + '/filedownloads/'
    for the_file in os.listdir(folder):
        if the_file != "README.txt":
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
