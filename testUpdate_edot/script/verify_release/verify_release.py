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
from datetime import datetime
import build_manage.settings as settings

from ctypes import *

E2_ENGN_VER = "e2engver.cnf"
QH_ENGN_VER = "qhengver.cnf"

SERVER_PATH = settings.RELEASE_SERVER_PATH

#
# Error codes for verify_release return tuple.
#
ERROR_SUCCESS = 0
ERROR_FAILED = 1

#
# Status codes for verify_release return tuple.
#
STATUS_VERIFIED = 0
STATUS_NOT_VERIFIED = 1
STATUS_FAILED = 2

#
# EngineType Values
#
QH = 1
E2 = 2


#
# This function connects to OneClickUpdate database server.
# Returns (cursor, dbconn) tuple in case of successful connection.
# Returns (0, 0) in case of failure.
#
def connect_to_update_db():

    logger = logging.getLogger('connect_to_update_db')
    logger.info('Start.')

    #
    # Read values for update database from a config ini
    #
    db_name = settings.OCD_DB
    host_name = settings.OCD_URL
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
    except Exception as exc:
        logger.error("error in mysql.connector.connect :{}".format(traceback.format_exc()))
        return (0,0)

    #
    # Connection successful for one click update database. Getting the cursor.
    #
    cursor = dbconn.cursor()

    logger.info('End.')
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

    logger = logging.getLogger('get_available_updtid_list')
    logger.info('Start.')

    temp_updtid_list = []

    #
    # Connect to database.
    #
    cursor, dbconn = connect_to_update_db()
    if (0 == cursor or 0 == dbconn):
        logger.error('connect_to_update_db failed.')
        return []

    try:
        query = "select UpdateID from enginemaster where JobID=" + str(job_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        if rows == []:
            logger.error('rows == []')
            server_deinit(cursor, dbconn)
            return []

        for row in rows:
            temp_updtid_list.append(int(row[0]))

    except Exception as exc:
        logger.error("error in executing query {}".format(traceback.format_exc()))
        server_deinit(cursor, dbconn)
        return []

    server_deinit(cursor, dbconn)

    logger.info('Returning list : {}'.format(temp_updtid_list))
    logger.info('End.')
    return temp_updtid_list


#
# This function calls extractdef tool to extract def file.
#
def run_extractdef(dat_file_path, dest_path):

    logger = logging.getLogger('run_extractdef')
    logger.info('Start.')

    ret_val = 0

    tool_path = os.path.join(settings.VERIFY_RELEASE_PATH, "extractdef")
    cmd = tool_path + ' ' + \
          dat_file_path + ' ' + \
          dest_path

    logger.info("cmd : {}".format(cmd))

    try:
        args = shlex.split(cmd)
        ret_val = subprocess.call(args)
        if 0 != ret_val :
            logger.error("subprocess.call returned : {}".format(ret_val))
            return False

    except Exception as exc:
        logger.error("error in subprocess.call {}".format(traceback.format_exc()))
        return False

    logger.info('End.')
    return True


def delete_dir(dir_path):

    logger = logging.getLogger('delete_dir')

    is_dir_present = False

    try:
        is_dir_present = os.path.exists(dir_path)
        if (True == is_dir_present):
            shutil.rmtree(dir_path)

    except Exception as exc:
        logger.error("error in deleting dir {}".format(traceback.format_exc()))
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

    logger = logging.getLogger('verify_release')
    logger.info('Start.')

    is_vdb_fetched = False

    update_id_list = get_available_updtid_list(job_id)
    if [] == update_id_list:
        logger.info("No update ids available")
        return (ERROR_FAILED, STATUS_FAILED, None)

    download_path = os.path.join(settings.VERIFY_RELEASE_PATH, "ocauto")

    try:
        os.stat(download_path)
    except:
        os.makedirs(download_path)

    for update_id in update_id_list:

        #
        # Download required dat file.
        #
        dat_file_name = "%(num1)08x_%(num2)08x.dat" % {'num1':update_id, 'num2':1}

        dat_file_path_server = os.path.join(settings.RELEASE_SERVER_PATH, dat_file_name)
        dat_file_path_local = os.path.join(download_path, dat_file_name)

        logger.info("dat_file_path_server: {}".format(dat_file_path_server))
        logger.info("dat_file_path_local: {}".format(dat_file_path_local))

        try:
            file_name, header = urllib.request.urlretrieve(dat_file_path_server, filename = dat_file_path_local)
            logger.info("Downloaded file path: {}".format(file_name))

        except Exception as exc:
            logger.error("error in dat file download:{}".format(traceback.format_exc()))
            delete_dir(download_path)
            return (ERROR_FAILED, STATUS_FAILED, None)

        #
        # Extract downloaded dat file.
        #
        extract_dir_path = os.path.join(download_path, "ext")

        ret_val = run_extractdef(dat_file_path_local, extract_dir_path)
        if False == ret_val:
            logger.info("run_extractdef failed")
            delete_dir(download_path)
            return (ERROR_FAILED, STATUS_FAILED, None)

        if QH == engine_type:
            engver_path = os.path.join(extract_dir_path, QH_ENGN_VER)
        else:
            engver_path = os.path.join(extract_dir_path, E2_ENGN_VER)

        #
        # Verify current jobid with jobid in downloaded engver.cnf
        #
        is_verified = c_int(0)
        encoded_engver_path = engver_path.encode('utf-8')

        logger.info("engver_path : {}".format(encoded_engver_path))

        try:
            is_engver_present = os.path.exists(encoded_engver_path)
            if (False == is_engver_present):
                logger.error("engver file not present")
                return (ERROR_FAILED, STATUS_FAILED, None)

        except Exception as exc:
            logger.error("error in os.path.exists:{}".format(traceback.format_exc()))
            return (ERROR_FAILED, STATUS_FAILED, None)

        ocauto_lib_path = os.path.join(settings.VERIFY_RELEASE_PATH, "ocauto.so")
        logger.info("ocauto_lib_path : {}".format(ocauto_lib_path))

        try:
            ocauto_handle = cdll.LoadLibrary(ocauto_lib_path)

        except Exception as exc:
            logger.error("error in LoadLibrary:{}".format(traceback.format_exc()))
            delete_dir(download_path)
            return (ERROR_FAILED, STATUS_FAILED, None)

        try:
            verify_jobid_fun = ocauto_handle.VerifyJobID

            ret_val = verify_jobid_fun(job_id, encoded_engver_path, byref(is_verified))
            if 0 != ret_val:
                logger.error("verify_jobid_fun failed")
                delete_dir(download_path)
                return (ERROR_FAILED, STATUS_FAILED, None)

        except Exception as exc:
            logger.error("error in calling function VerifyJobID :{}".format(traceback.format_exc()))
            delete_dir(download_path)
            return (ERROR_FAILED, STATUS_FAILED, None)

        if 0 == is_verified.value:
            logger.error("Not verified for Update ID = {}".format(update_id))
            delete_dir(download_path)
            return (ERROR_SUCCESS, STATUS_NOT_VERIFIED, None)

        if False == is_vdb_fetched:
            vdb_datetime = get_vdb(ocauto_handle, encoded_engver_path)
            if None == vdb_datetime:
                logger.error("get_vdb failed")
                delete_dir(download_path)
                return (ERROR_SUCCESS, STATUS_NOT_VERIFIED, None)

            is_vdb_fetched = True

        #
        # Delete extracted folder and dat file.
        #
        ret_val = delete_dir(extract_dir_path)
        if False == ret_val:
            logger.error("delete_dir failed for : {}".format(extract_dir_path))
            return (ERROR_FAILED, STATUS_FAILED, None)

        os.remove(dat_file_path_local)

        logger.info("verified for update ID = {}".format(update_id))

    logger.info("verified all update IDs")
    logger.info('End.')

    delete_dir(download_path)
    return (ERROR_SUCCESS, STATUS_VERIFIED, vdb_datetime)

def get_release_status(JobId,EngineType):
    import datetime,pytz
    vdb =  str(datetime.datetime.strftime(datetime.datetime.now(pytz.timezone('Asia/Calcutta')), '%Y-%m-%d %H:%M:%S'))
    return {'error_code':ERROR_SUCCESS,'status':STATUS_VERIFIED,'vdb':vdb}

    # ==========================================================================
    # +
    # Logs configuration

    log_dir_path = os.path.join(settings.VERIFY_RELEASE_PATH, "logs")
    try:
        os.stat(log_dir_path)
    except:
        os.makedirs(log_dir_path)

    log_file = 'verify_release_' + str(JobId) + datetime.now().strftime('_%d%m%Y_%H%M%S.log')
    log_file = os.path.join(log_dir_path, log_file)

    logging.basicConfig(filename=log_file,
    							filemode='w',
    							format='%(asctime)s,%(msecs)3s %(lineno)3s %(name)20s %(levelname)5s %(message)s',
    							datefmt='%H:%M:%S',
    							level=logging.DEBUG)

    logger = logging.getLogger('get_release_status')
    logger.info('Start.')

    # Logs configuration
    # -
    # ==========================================================================

    if os.name == 'nt':
        vdb_str = "2016-09-30 11:11:11"
        vdb = datetime.strptime(vdb_str, "%Y-%m-%d %H:%M:%S")
        logger.info("returning - error_code : {} status : {} vdb : {}".format(ERROR_SUCCESS, STATUS_VERIFIED, vdb))
        return {'error_code':ERROR_SUCCESS,'status':STATUS_VERIFIED,'vdb':vdb}
    else:
         err_code,status,vdb = verify_release(JobId,EngineType)
         logger.info("returning - error_code : {} status : {} vdb : {}".format(err_code, status, vdb))
         return {'error_code':err_code,'status':status,'vdb':vdb}


#*******************************************************************
#
#	Function:
#		get_vdb.
#
#	Parameters:
#		ocauto_handle
#		Handle to ocauto.so.
#
#		engver_path
#		File path of engver.cnf
#
#	Description:
#		This function verifies if given Job ID matches with the
#		Job ID in enginever file.
#
#	Returns:
#		if function is successful returns vdb in datetime format("%Y-%m-%d %H:%M:%S").
#       if function fails returns None.
#-
#*******************************************************************
def get_vdb(ocauto_handle, engver_path):

    logger = logging.getLogger('get_vdb')
    logger.info('Start.')

    vdb_from_engver = (c_char * 256)(0)

    try:
        get_vdb_from_engver = ocauto_handle.GetVDBFromEngver

        ret_val = get_vdb_from_engver(engver_path, vdb_from_engver)
        if 0 != ret_val:
            logger.error("get_vdb_from_engver failed. Return value: {}".format(ret_val))
            return None

    except Exception as exc:
        logger.error("error in getting vdb from engver {}".format(traceback.format_exc()))
        return None

    vdb_str = vdb_from_engver.value.decode(encoding='utf-8')

    logger.info("vdb string : {}".format(vdb_str))

    vdb_datetime = datetime.strptime(vdb_str, "%Y-%m-%d %H:%M:%S")

    logger.info('End.')
    return vdb_datetime

