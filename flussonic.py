#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from zeep import Client, Settings

logins=[]
fs_logins={}

#Result log file
r_log = '/var/log/billing/flussonic.log'

#---------------------------------------Lanbilling---------------------------------------

#LB accounting data
agent_id = '5'
lbuser = 'admin'
lbpasswd = 'pass'
lbapi = 'http://127.0.0.1:34012/?wsdl'


#Lanbilling API
settings = Settings(strict=False, xml_huge_tree=True)
client = Client(lbapi, settings=settings)

flt = {'login': 'admin', 'pass': ''}
response = client.service.Login(lbuser, lbpasswd)


# Lanbilling Get accounts by ID
flt = client.get_type('ns0:soapFilter')
flt = flt(agentid=agent_id)
response = client.service.getVgroups(flt)

#Lanbilling Prepare a list of users and statuses
for i in range(len(response)):
   if response[i]['blocked'] == 0:
      logins.append([response[i]['login'],True])
   else:
      logins.append([response[i]['login'],False])

#---------------------------------------Flussonic---------------------------------------

#Flussonic accounting data
file = 'flussonic.log'
sysargv_auth = {"login": "admin", "password": "pass"}
url = 'https://127.0.0.1/vsaas/api/v2/'

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

if os.path.isfile(file):
   file_auth = open(file, 'r')
   session_id = file_auth.read()
else:
   print('no file')
   session_id = get_session()

#Flussonic Get accounts
headers = {'x-vsaas-session': session_id, 'X-Page-Limit':'99'}
r = requests.get(url + 'users', headers=headers)

#Flussonic Prepare a list of users and statuses
for el in r.json():
    read = {str(el["login"]):(str(el["id"]), bool(el["enabled"]))}
    fs_logins.update(read)

for i in logins:
   if fs_logins.get(i[0]) == None:
      continue
   elif fs_logins.get(i[0])[1] != i[1]:
      with open(r_log, 'a') as file:
         if i[1] == True:
            file.write(i[0] + ' '  + 'Enable\n')
         else:
           file.write(i[0] + ' '  + 'Disable\n')
           #file.write(i[0] + ' ' + str(fs_logins.get(i[0])[1]) + ' ' +  str(i[1]) + '\n')

      status = i[1]
      payload = {"enabled":status}
      user_id = 'users/{0}'.format(fs_logins.get(i[0])[0])
      r = requests.put(url + user_id, data=payload, headers=headers)
      if r.status_code == 403:
         print('error 403')