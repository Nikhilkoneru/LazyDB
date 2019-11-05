# Welcome to LazyDB!

A Django Backend Service which can convert CSV's or Zip of CSV's to a **Database** of your choice.

>  Developed by **Nikhil K** and **Vaidehi Barevadia**.


# Steps to run the backend 

## Git Clone

Clone the project 

## Requirements
1) Python3
2) MySQL Server

## Install requirements.txt
```
pip install -r requirements.txt
```

## Edit Settings.py
Change databases username, password and change the DEBUG, PRODUCTION boolean values based upon your requirements.
```
sudo vi cloudbackend/settings.py
```
## Permissions 
This backend service writes files to the project. So we need to give appropriate permissions to the project
```
sudo chmod -R 755 *
```

## Run Manage.py
```
python3 manage.py runserver
```

## Navigate to the URL

Index page will be load once you open this link in browser 127.0.0.1:8000 


## License

MIT License

Copyright (c) 2019 Vaidehi Barevadia and Nikhil Koneru

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
> EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
> MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
> IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
> CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
> TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
> SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

