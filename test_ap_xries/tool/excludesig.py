#-------------------------------------------------------------------------------
# Name:        excludesig
# Purpose:     This scrip is to exclude records from database.
#
#Usage:
#   To Exclude Records :
#    excludesig.py <modes> <options>

#   Modes:
#   /siglist=   To provide list of sig ids
#   /md5list=   To provide list of MD5s
#   /sha2list=   To provide list of SHAs

#	e.g :
#   excludesig.py  /siglist=D:\todelete\siglistfile.txt
#   excludesig.py  /md5list=D:\todelete\md5listfile.txt
#   excludesig.py  /sha2list=D:\todelete\sha2listfile.txt
#
#   To provide multiple delete options :
#   excludesig.py  /siglist=D:\todelete\siglistfile.txt /sha2list=D:\todelete\sha2listfile.txt
    #excludesig.py  /siglist=D:\todelete\siglistfile.txt /md5list=D:\todelete\md5listfile.txt /sha2list=D:\todelete\sha2listfile.txt
#
#  options :
#	/reason=gc         Detelete reason : GEN COVERED (Covered from other engine.)
#   /reason=ws         Detelete reason : WEAK SIGNATURE
#   /reason=lh         Detelete reason : LESS HIT SIGNATURE
#
#    e.g :
#    excludesig.py  /siglist=D:\\todelete\\siglistfile.txt /reason=ws
#    excludesig.py  /siglist=D:\\todelete\\siglistfile.txt /sha2list=D:\\todelete\\sha2listfile.txt /reason=lh

# Note :
#		1). File path must be full.
#       2). Default delete reason is GEN COVERED
#		2)."Config.ini" file must present at the location of script.
#		3). Schema must be present before running this script.
#	Dependencies : ConfigParser, MySQLdb.

# Author:      Ankur Mathur
#
# Created:     28-12-2015
# Copyright:   (c) "Quick Heal Technologies (P) Ltd." 2015
# Licence:     "Quick Heal Technologies (P) Ltd."
#-------------------------------------------------------------------------------
import os
import sys
import logging
import traceback
from const import *
import configparser
import mysql.connector
from datetime import datetime
from mysql.connector import errorcode
from mysql.connector.constants import ClientFlag

is_delby_sigid = False
is_delby_md5 = False
is_delby_sha = False

#GEN_COVERED=5
NotFound = 0
Failed = 0
Successfull = 0
AlreadyDeleted = 0
SigIDList = []
SigIDListEx = []
SHAlist = []
MD5list = []

config = None
siginfo_cursor = None
siginfo_dbconn = None
apex_cursor = None
apex_dbconn = None
exreason = 0#GEN_COVERED


#=============================================================================================
#   Function to Initialize MySql Server connections
#=============================================================================================
def ServerInit():

    logger = logging.getLogger('ServerInit')
    logger.info("Start.")

    global config
    global siginfo_dbconn
    global apex_dbconn
    global siginfo_cursor
    global apex_cursor

    # read values for update database from a config ini
    try:
        siginfo_db_name = config.get('dbinfo', 'database')
        siginfo_host_name = config.get('dbinfo', 'host')
        siginfo_port = config.get('dbinfo', 'port')
        siginfo_user_name = config.get('dbinfo', 'user')
        siginfo_password = config.get('dbinfo', 'password')

        # read values for update database from a config ini
        apex_db_name = config.get('dbinfo_apex', 'database')
        apex_host_name = config.get('dbinfo_apex', 'host')
        apex_port = config.get('dbinfo_apex', 'port')
        apex_user_name = config.get('dbinfo_apex', 'user')
        apex_password = config.get('dbinfo_apex', 'password')
    except:
        print("No such section name in config file.")
        logger.error("No such section name in config file.")
        return False

     # Connect to signature mysql databaser server
    try:
        siginfo_dbconn = mysql.connector.connect(
                                    user=siginfo_user_name,
                                    password=siginfo_password,
                                    host=siginfo_host_name,
                                    port=siginfo_port,
                                    database=siginfo_db_name
                                    )
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your username or siginfo_password for {} at {}:{}".format(siginfo_db_name,siginfo_host_name,siginfo_port))
        logger.error("Something is wrong with your user name or siginfo_password for {} at {}:{}".format(siginfo_db_name,siginfo_host_name,siginfo_port))
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist : {} at {}:{}".format(siginfo_db_name,siginfo_host_name,siginfo_port))
        logger.error("Database does not exist : {} at {}:{}".format(siginfo_db_name,siginfo_host_name,siginfo_port))
      else:
        print(traceback.format_exc())
        logger.error(traceback.format_exc())

      return False

    # Connection successful for siginfo database. Getting the siginfo_cursor.
    logger.info("Successfully connected to siginfo server {} at {}:{}.".format(siginfo_db_name,siginfo_host_name,siginfo_port))
    siginfo_cursor = siginfo_dbconn.cursor(dictionary=True)

    # Connect to base mysql databaser server
    try:
        apex_dbconn = mysql.connector.connect(
                                    user=apex_user_name,
                                    password=apex_password,
                                    host=apex_host_name,
                                    port=apex_port,
                                    database=apex_db_name
                                    )
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your username or siginfo_password for {} at {}:{}".format(apex_db_name,apex_host_name,apex_port))
        logger.error("Something is wrong with your user name or siginfo_password for {} at {}:{}".format(apex_db_name,apex_host_name,apex_port))
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist : {} at {}:{}".format(apex_db_name,apex_host_name,apex_port))
        logger.error("Database does not exist : {} at {}:{}".format(apex_db_name,apex_host_name,apex_port))
      else:
        print(traceback.format_exc())
        logger.error(traceback.format_exc())

      siginfo_cursor.close()
      siginfo_dbconn.close()
      return False

    # Connection successful for apex data server. Getting the apex_cursor.
    logger.info("Successfully connected to apex data server {} at {}:{}.".format(apex_db_name,apex_host_name,apex_port))
    apex_cursor = apex_dbconn.cursor(dictionary=True)

    logger.info("End.")
    return True


#*****************************************************************
#Function to close mysql server connections
#*****************************************************************
def ServerDeinit():

    global siginfo_cursor
    global siginfo_dbconn
    global apex_cursor
    global apex_dbconn

    if siginfo_dbconn != None:
        siginfo_dbconn.rollback()
    if siginfo_cursor != None:
        siginfo_cursor.close()
    if siginfo_dbconn != None:
        siginfo_dbconn.close()

    if apex_dbconn != None:
        apex_dbconn.rollback()
    if apex_cursor != None:
        apex_cursor.close()
    if apex_dbconn != None:
        apex_dbconn.close()


def MarkExcludeBySigId():

    logger = logging.getLogger('MarkExcludeBySigId')
    logger.info('Start.')

    global apex_cursor
    global siginfo_cursor

    global NotFound
    global Failed
    global Successfull
    global AlreadyDeleted
    global SigIDList
    global exreason

    SigIDList.sort(key=int)

    for SigId in SigIDList:

        boDeletedFromQH = False
        boDeletedFromE2 = False
        responsedict1 = {}
        responsedict2 = {}

        responsedict2['type'] = 'Unknown'
        responsedict2['response'] = 'SigID deleted'
        responsedict2['result'] = '1'

        query = "SELECT SIG_TYPE_FK FROM {} WHERE SIG_ID={} LIMIT 1".format("sig_master",SigId)
        try:
            siginfo_cursor.execute(query)
        except mysql.connector.Error as err:
            logger.error(traceback.format_exc())
            Failed = Failed + 1
            return False

        result = siginfo_cursor.fetchone()
        if siginfo_cursor.rowcount <= 0:
            #print("Sig ID : {} : NOT FOUND".format(SigId));
            logger.info("Sig ID : {} : NOT FOUND".format(SigId));
            NotFound = NotFound + 1
            responsedict2['response'] = 'SigId not found'
            responsedict2['result'] = '2'
            responsedict1[SigId] = responsedict2
            print(responsedict1)
            continue
        else:
            responsedict2['type'] = str(result['SIG_TYPE_FK'])
            currtimestamp =  str(datetime.now())

            # Exclude record from qh_sig_status table
            query = "UPDATE {} SET MARK_DELETED={},UPDATE_FLAG_EXCLUDE=\"{}\",DATE_DELETED=\"{}\",DATE_STATUS_CHANGE=\"{}\",DELETE_REASON={} WHERE SIG_ID_FK={} AND MARK_DELETED=0".format("qh_sig_status",1,"H",currtimestamp,currtimestamp,exreason,SigId)
            try:
                siginfo_cursor.execute(query)
            except mysql.connector.Error as err:
                logger.error(traceback.format_exc())
                Failed = Failed + 1
                return False

            if siginfo_cursor.rowcount > 0:
                boDeletedFromQH = True

            # Exclude record from e2_sig_status table
            query = "UPDATE {} SET MARK_DELETED={},UPDATE_FLAG_EXCLUDE=\"{}\",DATE_DELETED=\"{}\",DATE_STATUS_CHANGE=\"{}\",DELETE_REASON={} WHERE SIG_ID_FK={} AND MARK_DELETED=0".format("e2_sig_status",1,"H",currtimestamp,currtimestamp,exreason,SigId)
            try:
                siginfo_cursor.execute(query)
            except mysql.connector.Error as err:
                logger.error(traceback.format_exc())
                Failed = Failed + 1
                return False

            if siginfo_cursor.rowcount > 0:
                boDeletedFromE2 = True

            if boDeletedFromE2 == False and boDeletedFromQH == False:
                #print("Sig ID : {} : ALREADY DELETED".format(SigId));
                logger.info("Sig ID : {} : ALREADY DELETED".format(SigId));
                AlreadyDeleted = AlreadyDeleted + 1
                responsedict2['response'] = 'SigId already deleted'
                responsedict2['result'] = '3'
                responsedict1[SigId] = responsedict2
                print(responsedict1)
                continue
            else:
                query = "UPDATE {} SET STATUS={},SIG_ID=0,SIG_TYPE=0 WHERE SIG_ID={}".format("malwares",exreason,SigId)
                try:
                    apex_cursor.execute(query)
                except mysql.connector.Error as err:
                    logger.error(traceback.format_exc())
                    Failed = Failed + 1
                    return False

                #print("Sig ID : {} : DELETED".format(SigId));
                logger.info("Sig ID : {} : DELETED".format(SigId));
                Successfull = Successfull + 1
                responsedict1[SigId] = responsedict2
                print(responsedict1)

    logger.info('End.')
    return True


def MarkExcludeBySigIdEx():

    logger = logging.getLogger('MarkExcludeByBySigIdEx')
    logger.info('Start.')

    global apex_cursor
    global siginfo_cursor

    global SigIDListEx
    global Failed
    global exreason

    SigIDListEx.sort(key=int)

    for SigId in SigIDListEx:

        query = "SELECT SIG_TYPE_FK FROM {} WHERE SIG_ID={} LIMIT 1".format("sig_master",SigId)
        try:
            siginfo_cursor.execute(query)
        except mysql.connector.Error as err:
            logger.error(traceback.format_exc())
            Failed = Failed + 1
            return False

        result = siginfo_cursor.fetchone()
        if siginfo_cursor.rowcount <= 0:
            #print("Sig ID : {} : NOT FOUND".format(SigId));
            logger.info("Sig ID : {} : NOT FOUND".format(SigId));
        else:
            currtimestamp =  str(datetime.now())

            # Exclude record from qh_sig_status table
            query = "UPDATE {} SET MARK_DELETED={},UPDATE_FLAG_EXCLUDE=\"{}\",DATE_DELETED=\"{}\",DATE_STATUS_CHANGE=\"{}\",DELETE_REASON={} WHERE SIG_ID_FK={} AND MARK_DELETED=0".format("qh_sig_status",1,"H",currtimestamp,currtimestamp,exreason,SigId)
            try:
                siginfo_cursor.execute(query)
            except mysql.connector.Error as err:
                logger.error(traceback.format_exc())
                Failed = Failed + 1
                return False

            # Exclude record from e2_sig_status table
            query = "UPDATE {} SET MARK_DELETED={},UPDATE_FLAG_EXCLUDE=\"{}\",DATE_DELETED=\"{}\",DATE_STATUS_CHANGE=\"{}\",DELETE_REASON={} WHERE SIG_ID_FK={} AND MARK_DELETED=0".format("e2_sig_status",1,"H",currtimestamp,currtimestamp,exreason,SigId)
            try:
                siginfo_cursor.execute(query)
            except mysql.connector.Error as err:
                logger.error(traceback.format_exc())
                Failed = Failed + 1
                return False


    logger.info('End.')
    return True


def MarkExcludeBySHA():

    logger = logging.getLogger('MarkExcludeBySHA')
    logger.info('Start.')

    global apex_cursor
    global siginfo_cursor

    global NotFound
    global Failed
    global Successfull
    global AlreadyDeleted

    global SigIDListEx
    global SHAlist
    global exreason

    for SHA in SHAlist:
        query = "SELECT SIG_ID FROM {} WHERE SHA2=\"{}\" LIMIT 1".format("malwares",SHA)
        try:
            apex_cursor.execute(query)
        except mysql.connector.Error as err:
            logger.error(traceback.format_exc())
            Failed = Failed + 1
            return False

        result = apex_cursor.fetchone()
        if apex_cursor.rowcount <= 0:
            print("SHA : \"{}\" : NOT FOUND".format(SHA));
            logger.info("SHA : \"{}\" : NOT FOUND".format(SHA));
            NotFound = NotFound + 1
        else:
            SigID = result['SIG_ID']
            if (SigID == 0):
                print("SHA : \"{}\" : ALREADY DELETED".format(SHA));
                logger.info("SHA : \"{}\" : ALREADY DELETED".format(SHA));
                AlreadyDeleted = AlreadyDeleted + 1
                continue
            else:
                query = "SELECT COUNT(*) FROM {} WHERE SIG_ID={}".format("malwares",SigID)
                try:
                    apex_cursor.execute(query)
                except mysql.connector.Error as err:
                    logger.error(traceback.format_exc())
                    Failed = Failed + 1
                    return False

                result = apex_cursor.fetchone()
                SigIDCount = result['COUNT(*)']
                if SigIDCount == 1:
                    SigIDListEx.append(SigID)

                query = "UPDATE {} SET STATUS={},SIG_ID=0,SIG_TYPE=0 WHERE SHA2=\"{}\"".format("malwares",exreason,SHA)
                try:
                    apex_cursor.execute(query)
                except mysql.connector.Error as err:
                    logger.error(traceback.format_exc())
                    Failed = Failed + 1
                    return False

                print("SHA : \"{}\" : OK".format(SHA));
                logger.info("SHA : \"{}\" : OK".format(SHA));
                Successfull = Successfull + 1

    return True


def MarkExcludeByMD5():

    logger = logging.getLogger('MarkExcludeByMD5')
    logger.info('Start.')

    global apex_cursor
    global siginfo_cursor

    global NotFound
    global Failed
    global Successfull
    global AlreadyDeleted

    global SigIDList
    global MD5list
    global exreason

    for MD5 in MD5list:
        query = "SELECT SIG_ID FROM {} WHERE FILE_MD5=\"{}\" LIMIT 1".format("malwares",MD5)
        try:
            apex_cursor.execute(query)
        except mysql.connector.Error as err:
            logger.error(traceback.format_exc())
            Failed = Failed + 1
            return False

        result = apex_cursor.fetchone()
        if apex_cursor.rowcount <= 0:
            print("MD5 : \"{}\" : NOT FOUND".format(MD5));
            logger.info("MD5 : \"{}\" : NOT FOUND".format(MD5));
            NotFound = NotFound + 1
        else:
            SigID = result['SIG_ID']
            if (SigID == 0):
                print("MD5 : \"{}\" : ALREADY DELETED".format(MD5));
                logger.info("MD5 : \"{}\" : ALREADY DELETED".format(MD5));
                AlreadyDeleted = AlreadyDeleted + 1
                continue
            else:
                query = "SELECT COUNT(*) FROM {} WHERE SIG_ID={}".format("malwares",SigID)
                try:
                    apex_cursor.execute(query)
                except mysql.connector.Error as err:
                    logger.error(traceback.format_exc())
                    Failed = Failed + 1
                    return False

                result = apex_cursor.fetchone()
                SigIDCount = result['COUNT(*)']
                if SigIDCount == 1:
                    SigIDListEx.append(SigID)

                query = "UPDATE {} SET STATUS={},SIG_ID=0,SIG_TYPE=0 WHERE FILE_MD5=\"{}\"".format("malwares",exreason,MD5)
                try:
                    apex_cursor.execute(query)
                except mysql.connector.Error as err:
                    logger.error(traceback.format_exc())
                    Failed = Failed + 1
                    return False

                print("MD5 : \"{}\" : OK".format(MD5));
                logger.info("MD5 : \"{}\" : OK".format(MD5));
                Successfull = Successfull + 1

    return True



def usage():
    print ("\n--------------------------| Usage |----------------------------")
    print ("\nAbout :\tThis scrip is to exclude/delete records from the database.\n")
    print ("\n\texcludesig.py <modes> <exclusion_reason>\n")

    print ("\tModes : ")
    print ("\t/h            Help and usage")
    print ("\t/help         Help and usage\n")

    print ("\t/siglist=     To remove signatres by Sig Ids")
    print ("\t/md5list=     To remove signatres by Md5s")
    print ("\t/sha2list=    To remove signatres by SHAs")

    print ("\n\texclusion_reason : ")
    print ("\t/reason=gc         Detelete reason : GEN COVERED (Covered from other engine.)")
    print ("\t/reason=ws         Detelete reason : WEAK SIGNATURE")
    print ("\t/reason=lh         Detelete reason : LESS HIT\n")

    print ("\te.g : ")
    print ("\texcludesig.py  /siglist=D:\\todelete\\siglistfile.txt /reason=gc")
    print ("\texcludesig.py  /md5list=D:\\todelete\\md5listfile.txt /reason=gc")
    print ("\texcludesig.py  /sha2list=D:\\todelete\\sha2listfile.txt /reason=gc")
    print ("\texcludesig.py  /siglist=D:\\todelete\\siglistfile.txt /reason=ws")
    print ("\texcludesig.py  /siglist=D:\\todelete\\siglistfile.txt /sha2list=D:\\todelete\\sha2listfile.txt /reason=lh")

    print ("\n\tNote :\n\t\t1). File path must be full.")
    print ("\t\t2). Default delete reason is gen covered.")
    print ("\t\t3).\"Config.ini\" file must present at the location of script.")
    print ("\t\t4). Schema must be present before running this script.")
    print ("\n\tDependencies : ConfigParser, MySQLdb.")
    print ("----------------------------------------------------------------\n")
    return

def main():

    logdir = os.path.join(os.path.dirname(sys.argv[0]),"logs")
    try:
        os.stat(logdir)
    except:
        os.mkdir(logdir)

    logfile = datetime.now().strftime('excludesig_%d%m%Y_%H%M%S.log')
    logfile = os.path.join(os.getcwd(),logdir,logfile)

    logging.basicConfig(filename=logfile,
    							filemode='a',
    							format='%(asctime)s,%(msecs)3s %(lineno)3s %(name)20s %(levelname)5s %(message)s',
    							datefmt='%H:%M:%S',
    							level=logging.DEBUG)

    logger = logging.getLogger('main')

    logger.info('Start.')
    startTime = datetime.now()


    if len(sys.argv) < 3 or (len(sys.argv) ==2 and (sys.argv[1] == "/?" or sys.argv[1] == "/help")):
        if len(sys.argv) < 3:
            print("\nInvalid arguments!!!")
            logger.error("Invalid arguments: {}".format(sys.argv))
        usage()
        return False

    global SigIDList
    global SigIDListEx
    global MD5list
    global SHAlist
    global NotFound
    global Failed
    global Successfull
    global AlreadyDeleted

    global config
    global siginfo_dbconn
    global apex_dbconn
    global siginfo_cursor
    global apex_cursor
    global exreason


    try:

        is_delby_sigid = False
        is_delby_md5 = False
        is_delby_sha = False
        ReasonPresent = False

        for params in sys.argv[1:]:
            token = params.find("=")
            delBy = params[1:token].lower()
            if delBy == "siglist":
                is_delby_sigid = True
                siglistfile = params[token+1:]

                if False == os.path.isfile(siglistfile):
                    print ("\nList file \"{}\" does not exist.".format(siglistfile))
                    logger.error("List file \"{}\" does not exist.".format(siglistfile))
                    return False

            elif delBy == "md5list":
                is_delby_md5 = True
                md5listfile = params[token+1:]

                if False == os.path.isfile(md5listfile):
                    print ("\nList file \"{}\" does not exist.".format(md5listfile))
                    logger.error("List file \"{}\" does not exist.".format(md5listfile))
                    return False

            elif delBy == "sha2list":
                is_delby_sha = True
                sha2listfile = params[token+1:]

                if False == os.path.isfile(sha2listfile):
                    print ("\nList file \"{}\" does not exist.".format(sha2listfile))
                    logger.error("List file \"{}\" does not exist.".format(sha2listfile))
                    return False

            elif delBy == "reason":
                ReasonPresent = True
                if params[token+1:] == "ws":
                    exreason = WEAK_SIG
                elif params[token+1:] == "lh":
                    exreason = LESS_HIT_COUNT
                elif params[token+1:] == "gc":
                    exreason = GEN_COVERED
                else:
                    print("\nInvalid exclude reason.")
                    logger.error("Invalid exclude reason.")
                    usage()
                    return False

            else:
                print("\nNo such type exclude option/reason : \"{}\".".format(delBy))
                logger.error("No such type exclude option/reason : \"{}\".".format(delBy))
                usage()
                return True

        if ReasonPresent == False:
            print("\nExclusion reason not found.")
            usage()
            return False

        # config parser initialization
        config = configparser.ConfigParser()
        retval = config.read(os.path.join(os.path.dirname(sys.argv[0]),'config.ini'))
        if len(retval) != 1:
            print ("\nError : could not find config.ini at current location.")
            print ("Aborting program......")
            logger.error("Error : could not find config.ini at current location.")
            logger.error("Aborting program......")
            return False

        # Initializing Mysql server configuration
        if False == ServerInit():
           print("There is something wrong with server configuration.")
           print("Server cannot be connected.\nPlease check the server configuration and try connecting again.")
           logger.error("There is something wrong with server configuration.")
           logger.error("Server cannot be connected.")
           return False

        TotalRecords = 0

        if is_delby_sigid == True:
            with open(siglistfile, 'r') as listfile:
                for line in listfile.readlines():
                    line = line.rstrip()
                    if line == "":
                        continue
                    SigIDList.append(line)
                    TotalRecords = TotalRecords + 1

            # Remove duplicate signature ids (if any)
            SigIDList = list(set(SigIDList))
            if False == MarkExcludeBySigId():
                print("MarkExcludeBySigId : Failed")
                logger.error("MarkExcludeBySigId : Failed")
                ServerDeinit()
                return False


        if is_delby_md5 == True:
            with open(md5listfile, 'r') as listfile:
                for line in listfile.readlines():
                    line = line.rstrip()
                    if line == "":
                        continue
                    MD5list.append(line)
                    TotalRecords = TotalRecords + 1

            # Remove duplicate MD5s (if any)
            MD5list = list(set(MD5list))
            if False == MarkExcludeByMD5():
                print("MarkExcludeByMD5 : Failed")
                logger.error("MarkExcludeByMD5 : Failed")
                ServerDeinit()
                return False


        if is_delby_sha == True:
            with open(sha2listfile, 'r') as listfile:
                for line in listfile.readlines():
                    line = line.rstrip()
                    if line == "":
                        continue
                    SHAlist.append(line)
                    TotalRecords = TotalRecords + 1

            # Remove duplicate SHA2s (if any)
            SHAlist = list(set(SHAlist))
            if False == MarkExcludeBySHA():
                print("MarkExcludeBySHA : Failed")
                logger.error("MarkExcludeBySHA : Failed")
                ServerDeinit()
                return False

        # finalize step only in case of MD5 and SHA2
        if is_delby_sha == True or is_delby_md5 == True:
            # Remove duplicate signature ids (if any)
            SigIDListEx = list(set(SigIDListEx))
            if False == MarkExcludeBySigIdEx():
                print("MarkExcludeByBySigIdEx : Failed")
                logger.error("MarkExcludeByBySigIdEx : Failed")
                ServerDeinit()
                return False

        status = "COMPLETED"
        updated_sig_count = Successfull
        excluded_sig_count = Successfull
        total_signatures = 0
        total_samples_processed = 0
        samples_covered = 0
        module_name = SIG_EXLUDE

        JobDetailCol = "status,updated_sig_count,excluded_sig_count,total_signatures,total_samples_processed,samples_covered,module_name"
        JobDetailValue = "\"{}\",{},{},{},{},{},\"{}\"".format(status,updated_sig_count,excluded_sig_count,total_signatures,total_samples_processed,samples_covered,module_name)
        query = "INSERT INTO {} ({}) VALUES ({})".format("job_details",JobDetailCol,JobDetailValue)
        try:
            siginfo_cursor.execute(query)
        except mysql.connector.Error as err:
            print(traceback.format_exc())
            logger.erro(traceback.format_exc())
            ServerDeinit()
            return False

    except:
        print("Unexpected error:{}".format(traceback.format_exc()))
        logger.error("Unexpected error:{}".format(traceback.format_exc()))
        ServerDeinit()
        return False


    siginfo_dbconn.commit()
    siginfo_cursor.close()
    siginfo_dbconn.close()

    apex_dbconn.commit()
    apex_cursor.close()
    apex_dbconn.close()

##    print("\nRecords to exclude : {}".format(TotalRecords))
##    print("Records excluded successfully : {}".format(Successfull))
##    print("Records not found : {}".format(NotFound))
##    print("Records already excluded : {}".format(AlreadyDeleted))
##    print("Records failed to exclude : {}".format(Failed))

    logger.info("Records to exclude : {}".format(TotalRecords))
    logger.info("Records excluded successfully : {}".format(Successfull))
    logger.info("Records not found : {}".format(NotFound))
    logger.info("Records already excluded : {}".format(AlreadyDeleted))
    logger.info("Records failed to exclude : {}".format(Failed))

    #print ("\nTotal time taken : ", datetime.now() - startTime)
    logger.info("Total time taken : {}" .format(datetime.now() - startTime))

    logger.info('End.')
    return True


if __name__ == '__main__':
    if True == main():
        exit(0)
    else:
        exit(1)
