#-------------------------------------------------------------------------------
# Name:        verify_release.py
# Purpose:
#
# Author:      manoj.raut
#
# Created:     22/09/2016
# Copyright:   (c) manoj.raut 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import sys
import shlex
import shutil
import logging
import traceback
import subprocess
import urllib.request
import mysql.connector
sys.path.append(sys.path[0].replace('script\\verify_release','build_manage'))
#print(sys.path[0].replace('script\\verify_release','build_manage'))
#print(sys.path)
import build_manage.settings as settings

from ctypes import *

E2_ENGN_VER = "e2engver.cnf"
QH_ENGN_VER = "qhengver.cnf"

#E2_UPDT_ID_LIST = [4,5]
#QH_UPDT_ID_LIST = [778,779,780,781,782,783,784,785,786,787]

SERVER_PATH = settings.RELEASE_SERVER_PATH
DOWNLOAD_PATH = settings.RELEASE_DOWNLOAD_PATH

#
# EngineType Values
#
QH = 1
E2 = 2

#OneClickUpdate details






#
# This function connects to OneClickUpdate database server.
# Returns (cursor, dbconn) tuple in case of successful connection.
# Returns (0, 0) in case of failure.
#
def connect_to_update_db():

    #
    # Read values for update database from a config ini
    #
    db_name = settings.OCD_DB
    host_name = settings.OCD_URL
    port = 3306
    user_name = settings.OCD_USER
    password = settings.OCD_PASS

    #
    # Connect to update database server
    #
    try:
        dbconn = mysql.connector.connect(
										user=settings.OCD_USER,
										password=settings.OCD_PASS,
										host=settings.OCD_URL,
										port=3306,
										database=settings.OCD_DB
										)
    except mysql.connector.Error as err:
      #if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        #logger.error("Something is wrong with your user name or password for {} at {}:{}".format(db_name,host_name,port))
      #elif err.errno == errorcode.ER_BAD_DB_ERROR:
        #logger.error("Database does not exist : {} at {}:{}".format(db_name,host_name,port))
      #else:
        #logger.error(traceback.format_exc())

      return (0,0)

    #
    # Connection successful for one click update database. Getting the cursor.
    #
    cursor = dbconn.cursor()

    return (cursor, dbconn)


#
# Deinitialization of the database server.
#
def server_deinit(cursor,dbconn):

    if cursor != None:
        cursor.close()
    if dbconn != None:
        dbconn.close()


def get_available_updtid_list(job_id):

    temp_updtid_list = []

    #
    # Connect to database.
    #
    cursor, dbconn = connect_to_update_db()
    if (0 == cursor or 0 == dbconn):
        return []

    try:
        query = "select UpdateID from enginemaster where JobID=" + str(job_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        if rows == []:
            server_deinit(cursor, dbconn)
            return []

        for row in rows:
            temp_updtid_list.append(row[0])

    except mysql.connector.Error as err:
        server_deinit(cursor, dbconn)
        return []

    server_deinit(cursor, dbconn)

    return temp_updtid_list


#
# This function calls extractdef tool to extract def file.
#
def run_extractdef(dat_file_path, dest_path):

    ret_val = 0

    cmd = "./extractdef" + ' ' + \
          dat_file_path + ' ' + \
          dest_path
    try:
        args = shlex.split(cmd)
        ret_val = subprocess.call(args)
        if 0 != ret_val :
            return False

    except Exception as e:
        return False

    return True


def delete_dir(dir_path):

    is_dir_present = False

    try:
        is_dir_present = os.path.exists(dir_path)
        if (True == is_dir_present):
            shutil.rmtree(dir_path)

    except Exception as exc:
        return False

    return True


#*******************************************************************
#
#	Function:
#		verify_release.
#
#	Parameters:
#		job_id
#		Job ID to be verified.
#
#		engine_type
#		Type of engine for which update is created.(QH:1, E2:2)
#
#	Description:
#		This function verifies if given Job ID matches with the
#		Job ID in enginever file.
#
#	Returns:
#       Tuple (error_code, status)
#		error_code: 0 if function is successful.
#                   1 if function fails.
#       status:     0 if job id is verified.
#                   1 if job id is not verified.
#                   2 for other failure.
#-
#*******************************************************************
def verify_release(job_id, engine_type):

    update_id_list = get_available_updtid_list(job_id)
    if [] == update_id_list:
        return (1,2)

    try:
        os.stat(DOWNLOAD_PATH)
    except:
        os.makedirs(DOWNLOAD_PATH)

    for update_id in update_id_list:

        #
        # Download required dat file.
        #
        dat_file_name = "%(num1)08x_%(num2)08x.dat" % {'num1':update_id, 'num2':1}

        dat_file_path_server = os.path.join(settings.RELEASE_SERVER_PATH, dat_file_name)
        dat_file_path_local = os.path.join(settings.RELEASE_DOWNLOAD_PATH, dat_file_name)

        try:
            file_name, header = urllib.request.urlretrieve(dat_file_path_server, filename = dat_file_path_local)
            print(file_name)
            print(header)

        except Exception as exc:
            print("error in urlretrieve:{}".format(traceback.format_exc()))
            delete_dir(DOWNLOAD_PATH)
            return (1,2)

        #
        # Extract downloaded dat file.
        #
        extract_dir_path = os.path.join(DOWNLOAD_PATH, "ext")

        ret_val = run_extractdef(dat_file_path_local, extract_dir_path)
        if False == ret_val:
            print("run_extractdef failed")
            delete_dir(DOWNLOAD_PATH)
            return (1,2)

        if QH == engine_type:
            engver_path = os.path.join(extract_dir_path, QH_ENGN_VER)
        else:
            engver_path = os.path.join(extract_dir_path, E2_ENGN_VER)

        #
        # Verify current jobid with jobid in downloaded engver.cnf
        #
        is_verified = c_int(0)
        encoded_engver_path = engver_path.encode('utf-8')

        print (engver_path)
        print("default is_verified = {}".format(is_verified.value))

        try:
            ocauto_handle = cdll.LoadLibrary("ocauto.so")
        except Exception as exc:
            print("error in LoadLibrary:{}".format(traceback.format_exc()))
            delete_dir(DOWNLOAD_PATH)
            return (1,2)

        verify_jobid_fun = ocauto_handle.VerifyJobID

        ret_val = verify_jobid_fun(job_id, encoded_engver_path, byref(is_verified))
        if 0 != ret_val:
            print("verify_jobid_fun failed")
            delete_dir(DOWNLOAD_PATH)
            return (1,2)

        if 0 == is_verified.value:
            print("not verified = {}".format(is_verified.value))
            delete_dir(DOWNLOAD_PATH)
            return (0,1)

        #
        # Delete extracted folder and dat file.
        #
        ret_val = delete_dir(extract_dir_path)
        if False == ret_val:
            return (1,2)

        os.remove(dat_file_path_local)

        print("verified for update ID = {}".format(update_id))

    print("verified all update IDs = {}".format(is_verified.value))
    delete_dir(DOWNLOAD_PATH)
    return (0,0)

def get_release_status(JobId,EngineType):
    import os
    if os.name == 'nt':
        return {'error_code':0,'status':1}
    else:
         err_code,status = verify_release(JobId,EngineType)
         return {'error_code':err_code,'status':status}

    #if 1 == err_code:
    #    delete_dir(DOWNLOAD_PATH)


    #print("result : {} {}".format(err_code,status))

