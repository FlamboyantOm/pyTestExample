jenkins_url = 'http://10.10.10.236:8080'
jenkins_username = 'kamesh'
jenkins_password = 'kamesh'

import pymysql as mdb

try:
   databse = mdb.connect('10.10.10.236', 'root', 'root', 'build_manage')

except Exception as e:
   print(e)


