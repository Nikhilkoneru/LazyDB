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
import ssl
import mysql
from django.apps import apps

mysql_status = settings.mysql_status
mysql_username = settings.mysql_username
mysql_password = settings.mysql_password
server_url = settings.server_url
export_file_path = settings.export_file_path
file_download_path = settings.file_downloads_path
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


class MysqlSupport:
    def __init__(self):
        self.connection = None
        try:
            logging.debug('Method:__init__, output:Connecting')
            self.connection = mysql.connector.connect(
                host="localhost",
                user=mysql_username,
                passwd=mysql_password,
            )
        except Exception as error:
            logging.debug('Method:__init__, Error:%s', error)
            self.connection = None

    def save_and_export(self, email, url, db_type):
        if self.connection is not None:
            logging.debug('Method:save_and_export, Args:[email=%s, url=%s, db=%s]', email, url, db_type)
            dbname = "".join(" ".join(re.findall("[a-zA-Z]+", email.split("@")[0])).split())
            self.create_db(dbname, db_type)
            self.connectDBtoDjango(dbname, db_type)
            try:
                call_command('migrate', 'mysql_support', 'zero', '--database=' + dbname, '--noinput')
                call_command('makemigrations', '--no-input', '--name', dbname)
                call_command('migrate', '--database=' + dbname, '--noinput')
            except Exception as e:
                logging.debug('Method:save_and_export, Error:%s', e)
                pass
            try:
                output = self.read(url)
                tables_dataframe_list, table_names = output["dataframes"], output["table_names"]
                logging.debug('Method:save_and_export, Args:[url=%s], Message: Num of tables=%s', url,
                              len(tables_dataframe_list))
                model_names = []
                for table, name in zip(tables_dataframe_list, table_names):
                    try:
                        model_names.append(self.create_and_save_table(dbname, url, db_type, table, name))
                    except Exception as e:
                        logging.debug('Method:save_and_export, Error:%s, Message: Error with csv=%s', e, name)
                        pass

                self.exportDB(dbname, table_names)
                self.deleteFiles()
                self.delete_db(dbname)
                self.connection.close()
                return JsonResponse({"status": 200, "db_name": dbname, "file_type": "sql"})
            except Exception as e:
                logging.debug('Method:save_and_export,  Error: %s', e)
                self.delete_db(dbname)
                self.connection.close()
                return JsonResponse({"status": 400, "db_name": dbname, "file_type": "sql", "error": e})
        else:
            logging.debug('Method:save_and_export, output:error, Database Status False')
            return JsonResponse({"status": 400, "output": "Database Connection Issue"})

    def create_and_save_table(self, dbname, url, database, csv_df, table_name):
        logging.debug(
            'Method:create_and_save_table, Args:[dbname=%s, url=%s, database=%s, len(csv_df)=%s], Message: Create and '
            'Save Table',
            dbname, url, database, len(csv_df))
        columns = csv_df.columns
        data_types = csv_df.dtypes

        class Meta:
            db_table = table_name

        attrs = OrderedDict({'__module__': 'mysql_support.models', 'Meta': Meta})
        for i, val in enumerate(columns):
            column_type = self.getDynamicType(str(data_types[i]))
            attrs.update({val.lower(): column_type})
        try:
            dynamic_table = apps.get_model("mysql_support." + table_name)
        except Exception as e:
            dynamic_table = type(table_name, (models.Model,), attrs)
            call_command('makemigrations', 'mysql_support', '--no-input', '--name', dbname)
            call_command('migrate', 'mysql_support', '--database=' + dbname, '--noinput')
        df = csv_df.to_dict(orient='records')
        for val in df:
            model = dynamic_table(**val)
            model.save(using=dbname)
        return dynamic_table

    def read(self, url):
        if "zip" in url:
            logging.debug('Method:read, Args:[url=%s], Message: ZIP File', url)
            result = []
            context = ssl._create_unverified_context()
            url_m = urllib.request.urlopen(url, context=context)
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

    def connectDBtoDjango(self, dbname, db_type):
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

    def exportDB(self, dbname, tables):
        logging.debug('Method:exportDB, Args:[dbname=%s], Message: Export DB', dbname)
        file = open(export_file_path + "%s.sql" % dbname, 'w+')
        p1 = subprocess.Popen(["mysqldump", "-u", mysql_username, "-p" + mysql_password, dbname] + tables, stdout=file,
                              stderr=subprocess.STDOUT)
        p1.wait()
        p1.communicate()
        file.close()

    def create_db(self, dbname, db_type):
        logging.debug('Method:createDB, Args:[dbname=%s,db_type=%s], Message: Drop and Create DB', dbname, db_type)
        if db_type == "mysql":
            self.connection.cursor().execute("DROP DATABASE IF EXISTS " + dbname)
            self.connection.cursor().execute("CREATE DATABASE " + dbname)
            self.connection.cursor().execute("USE " + dbname)

    def delete_db(self, dbname):
        logging.debug('Method:deleteDB, Args:[dbname=%s], Message: Delete DB', dbname)
        self.connection.cursor().execute("Drop DATABASE IF EXISTS " + dbname)
        del settings.DATABASES[dbname]

    def getDynamicType(self, type):
        logging.info('Method:getDynamicType, Args:[type=%s]', type)
        if type == "int64":
            return models.IntegerField(default=None, blank=True, null=True)
        elif type == "float64":
            return models.FloatField(default=None, blank=True, null=True)
        elif type == "bool":
            return models.BooleanField()
        else:
            return models.CharField(max_length=1000, blank=True, null=True, default=None)

    def deleteFiles(self):
        folder = file_download_path
        for the_file in os.listdir(folder):
            if the_file != "README.txt":
                file_path = os.path.join(folder, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
