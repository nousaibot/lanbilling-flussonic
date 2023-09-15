#!/usr/bin/env python3

import os
import sys
import requests
import pymysql

#Flusssonic accounting data
file = 'flussonic.log'
sysargv_auth = {"login": "admin", "password": "pass"}
url = 'https://127.0.0.1/vsaas/api/v2/'

def db_connect():
    try:
        db = pymysql.connect(host="localhost", user="billing", password="billing", db="billing", autocommit=True, charset="utf8",
                             connect_timeout=20)
        cursor = db.cursor()
        return db, cursor
    except UnboundLocalError as error:
        print(error)
    except pymysql.err.OperationalError as error:
        print(error)

def db_query():
    try:
        db, cursor = db_connect()
        sql = "SELECT login, blocked FROM vgroups where id = 5 AND archive=0"
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        db.close()
        return results
    except UnboundLocalError as error:
       print(error)
    except pymysql.err.OperationalError as error:
       print(error)


def get_session():
    r = requests.post(url + 'auth/login', json=sysargv_auth)
    print(r)
    if r.status_code == 200:
        session_id = r.json()['session']
        file_auth = open(file, 'w+')
        file_auth.write(session_id)
        file_auth.close()
        return session_id
    else:
        print('Get session: delete file')
        os.remove(file)
        exit(1)

def get_func():
    result = {}

    if os.path.isfile(file):
        print('Is file')
        file_auth = open(file, 'r')
        session_id = file_auth.read()
    else:
        print('no file')
        session_id = get_session()

    headers = {'x-vsaas-session': session_id, 'X-Page-Limit':'99'}
    r = requests.get(url + 'users', headers=headers)


    for el in r.json():
        read = {str(el["login"]):(str(el["id"]), bool(el["enabled"]))}
        result.update(read)
    return result

def put_func():
    db_result = db_query()
    result = get_func()

    if os.path.isfile(file):
        print('Is file')
        file_auth = open(file, 'r')
        session_id = file_auth.read()
    else:
        print('no file')
        session_id = get_session()

    headers = {'x-vsaas-session': session_id, 'X-Page-Limit':'99'}


    for i in db_result:
        if result.get(i[0]) != None:
            print(i[0], not bool(i[1]), result.get(i[0])[1])
            status = str(not bool(i[1]))
            if (not bool(i[1])) != result.get(i[0])[1]:
                payload = {"enabled":status}
                user_id = 'users/{0}'.format(result.get(i[0])[0])
                r = requests.put(url + user_id, data=payload, headers=headers)
                if r.status_code == 403:
                    os.remove(file)
                    exit(1)

put_func()
