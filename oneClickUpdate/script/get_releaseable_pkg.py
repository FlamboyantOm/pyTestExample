#-------------------------------------------------------------------------------
# Name:        get_releaseable_pkg
# Purpose:     It will return the list of packages available for
#              release with full URL path and path name.
#              It returns status, pkg_list, pkg_list_with_url where
#              status can have following values :
#              0 : Success
#              1 : Error
#              2 : No records found
#
# Dependency:  This script is dependent on mysql.connector python library
#              and setting.py
#
# Author:      sushant.arya
#
# Created:     14/09/2016
# Modified:    23/09/2016
#-------------------------------------------------------------------------------

import os
import sys
import logging
import traceback
import mysql.connector
from datetime import datetime
sys.path.append(sys.path[0].replace('script','build_manage'))
import build_manage.settings as cnf

dbcon  = None
cursor = None


def RetrieveToBeReleasePkgListInternal(pkg_list, pkg_list_with_url, job_urllist):
    logger = logging.getLogger('RetrieveToBeReleasePkgListInternal')
#    logger.info('Start.')

    #
    #   Retrieving pkg_list and pkg_url of qa_complete or detection_verification promoted packages from jenkins db
    #
    sql_query = """select pkg.pkg_url, pkg.pkg_name, bld.job_url from package_info pkg, build_info bld where (pkg.pkg_id, bld.build_id) IN
    (select pkg_id, build_id from build_info where job IN ('engine_trunk', 'trr_trunk', 'update_trunk') and status_id IN
    (select status_id from build_status_info where status_name in
    ('qa_complete', 'detection_verification'))) order by pkg_name;"""

    #
    #   Executing sqlquery to fetch package list with their url
    #
    try:
        cursor.execute(sql_query)
    except:
        #print('\'{}\' query failed!'.format(sql_query))
        logger.error('\'{}\' query failed!'.format(sql_query))
        logger.error(traceback.format_exc())
        return 1

    try:
        bRecord = False
        row = cursor.fetchone()
        if row is not None:
            bRecord = True
            while row is not None:
                #print ("Name => {}, URL => {}".format(row[1], row[0]))
                pkg_list_with_url.append(row[0])
                pkg_list.append(row[1])
                job_urllist.append(row[2])

                row = cursor.fetchone()

    except:
        logger.error(traceback.format_exc())
        return 1

    if False == bRecord:
        #print("No records found for query \'{}\'".format(sql_query))
        logger.error("No records found for query \'{}\'".format(sql_query))
        return 2

#    logger.info('Exit.')
    return 0


def RetrieveToBeReleasePkgList():

    #
    #   Initializations
    #
    log_dir  = CWD = os.getcwd()

    #
    #   Preparing log file.
    #
    log_dir = os.path.join(log_dir, "logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except:
            log_dir = os.path.join(CWD, "logs")

    logfile = datetime.now().strftime('get_releaseable_pkg_%d%m%Y_%H%M%S.log')
    logfile = os.path.join(log_dir,logfile)

    logging.basicConfig(
        filename=logfile,
		filemode='a',
		format='%(asctime)s, %(lineno)3s %(name)20s %(levelname)5s %(message)s',
		datefmt='%H:%M:%S',
		level=logging.DEBUG
        )

    logger = logging.getLogger('main')

#    logger.info('Start.')

    global dbcon
    global cursor

    #
    #   Open database connection
    #
    try:
        dbcon = mysql.connector.connect(host=cnf.BUILDDB_HOSTNAME, user=cnf.BUILDDB_USERNAME, password=cnf.BUILDDB_PASSWORD, database=cnf.BUILDDB_DATABASE)
    except:
        #print(traceback.format_exc())
        logger.error('Connection failed! host \'{}\', user \'{}\', database \'{}\''.format(cnf.BUILDDB_HOSTNAME, cnf.BUILDDB_USERNAME, cnf.BUILDDB_DATABASE))
        logger.error(traceback.format_exc())
        logging.shutdown()
        return 1, None, None

#    logger.info('Connection established! host \'{}\', user \'{}\', database \'{}\''.format(cnf.BUILDDB_HOSTNAME, cnf.BUILDDB_USERNAME, cnf.BUILDDB_DATABASE))

    #
    #   prepare a cursor object using cursor() method
    #
    cursor = dbcon.cursor()

    iRet = 0
    pkg_list = list()
    job_urllist = list()
    pkg_list_with_url = list()
    iRet = RetrieveToBeReleasePkgListInternal(pkg_list, pkg_list_with_url, job_urllist)
    if 0 != iRet:
        #print("RetrieveToBeReleasePkgListInternal failed!")
        logger.error("RetrieveToBeReleasePkgListInternal failed!")
#    else:
        #print("pkg_list = {}".format(pkg_list))
#        logger.info("pkg_list = {}".format(pkg_list))

    #
    #   disconnect from server
    #
    cursor.close()
    dbcon.close()

#    logger.info("Exit.")
    logging.shutdown()

    if 0 == iRet:
        return iRet, pkg_list, pkg_list_with_url, job_urllist
    else:
        return iRet, None, None, None


def main():
    status, pkg_list1, pkg_list_with_url1, job_urllist = RetrieveToBeReleasePkgList()
    #print(pkg_list_with_url1)
    sys.exit(0)


if __name__ == '__main__':
    main()
