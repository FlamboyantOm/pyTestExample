#-------------------------------------------------------------------------------
# Name:        const.py
# Purpose:     It defines the constants required in OnClickUpdate.
#
# Author:      manoj.raut
#
# Created:     04/04/2016
# Copyright:   (c) "Quick Heal Technologies Ltd." 2016
# Licence:     "Quick Heal Technologies Ltd."
#-------------------------------------------------------------------------------


from sys import platform as _platform

if _platform == "linux" or _platform == "linux2":

    DNE2UPDT_APP_NAME = './dne2updt'
    DNQHUPDT_APP_NAME = './dnqhupdt'
    GNSOLOUPDT_APP_NAME = './gnsolodf'
    GNUPGUPDT_APP_NAME = './gnupgdef'
    GENDIFFUPDATE_APP_NAME = './gendiffupdt'
    DIFFTEST_APP_NAME = './difftest'
    UPDATEINDEXDAT_APP_NAME = './updateindexdat'
    REVERTE2UPDATE_APP_NAME = './reverte2updt'
    PYTHON_NAME = 'python3.4'
    PATH_SEP = '/'

elif _platform == "win32":

    DNE2UPDT_APP_NAME = 'dne2updt.exe'
    DNQHUPDT_APP_NAME = 'dnqhupdt.exe'
    GNSOLOUPDT_APP_NAME = 'gnsolodf.exe'
    GNUPGUPDT_APP_NAME = 'gnupgdef.exe'
    GENDIFFUPDATE_APP_NAME = 'gendiffupdt.exe'
    DIFFTEST_APP_NAME = 'difftest.exe'
    UPDATEINDEXDAT_APP_NAME = 'updateindexdat.exe'
    REVERTE2UPDATE_APP_NAME = 'reverte2updt.exe'
    PYTHON_NAME = 'python'
    PATH_SEP = '\\'


#
# Constants for update ID
#
UPDT_ID_E2_32 = 4
UPDT_ID_E2_64 = 5

#
# Constants for update ID string
#
UPDT_ID_E2_32_STR = '4'
UPDT_ID_E2_64_STR = '5'

LOGS_DIR_NAME = 'logs'

#
# INI file names.
#
CONFG_DB_INI_NAME = 'config.ini'
CONFG_PATHS_INI_NAME = 'configpaths.ini'

#
# Dir names
#
PLUGINS_DIR_NAME = 'Plugins'
DEF_DIR_NAME = 'def'
DIFF_DIR_NAME = 'diff'
TEST_DEF_DIR_NAME = 'test_def'
TEST_DIFF_DIR_NAME = 'test_diff'

#
# Engine types
#
ENGN_TYPE_E2 = 'e2'
ENGN_TYPE_QH = 'qh'

#
# Update types
#
UPDT_TYPE_TEST = 'test'
UPDT_TYPE_RELEASE = 'release'

#
# Diff version list file name
#
DIFF_VER_LIST_FILE_NAME = 'diff_ver_list.txt'

#
# Patch file extension
#
PATCH_FILE_EXT = '.patch'

#
# Limits for differential updates.
#


E2_RELEASE_DIFF_LIMIT = {4:30, 5:30, 6:30}
E2_BUILD_DIFF_LIMIT = {4:30, 5:30, 6:30}

QH_RELEASE_DIFF_LIMIT = {778:30, 779:30, 780:30, 781:30, 782:30, 783:30, 784:30, 785:30, 786:30, 787:30, 860:30}
QH_BUILD_DIFF_LIMIT = {778:30, 779:30, 780:30, 781:30, 782:30, 783:30, 784:30, 785:30, 786:30, 787:30, 860:30}





#
# Limit to keep Jobs data other than window size (Above limits)
#
CUSTOM_JOBS_LIMIT = 10

#
# Limit to keep latest Failed jobs
#
KEEP_FAILED_JOBS_LIMIT = 10

#
# App names
#
CREATE_E2_UPDATE_PY = 'create_e2_update.py'

#
# User Names
#
USER_NAME_JENKINS = 'script'

#
# JobState Values
#
START = 1
DOWNLOADED = 2
TEST_UP_CREATED = 3
MARK_VERIFED = 4
REL_UP_CREATED = 5
MARK_RELEASED = 6
FAILED = 7

#
# FailedReason Values
#
NO_UPDATE_AVAILABLE	= 1
TEST_FAILED	= 2
OTHER = 3

#
# EngineType Values
#
QH = 1
E2 = 2

#
# Flag Values
#
NORMAL = 1
MANUAL = 2

#
# Table Names used in OneClickUpdate
#
JOB_INFO_TABLE = 'jobinfo'
RELEASE_INFO_TABLE = 'releaseinfo'
DOWNLOAD_DETAILS_TABLE = 'downloaddetails'
JOB_STATE_DETAILS_TABLE = 'jobstatedetails'
FAILED_JOB_INFO = 'failedjobinfo'
PROGRESS_LOG_TABLE = 'progresslog'
QH_PACKAGE_DETAILS_TABLE = 'qhpackagedetails'

#
# Column names for jobinfo table
#
COLUMN_NAMES_JOBINFO_TABLE = 'JobID, JobState, DateCreated, EngineType, Flag, UserName'

COLUMN_NAMES_DOWNLOADDETAILS_TABLE = 'JobID, UpdateID'

COLUMN_NAMES_JOBSTATEDETAILS_TABLE = 'JobID, JobState, TimeTaken, StartTime, PercentDone'

COLUMN_NAMES_FAILEDJOBINFO_TABLE = 'JobID, FailedReason, Notes, UserName'

COLUMN_NAMES_PROGRESSLOG_TABLE = 'JobID, Msg, PercentDone, NodeID, UpdateID' # Not included LogTime as default is NOW()

COLUMN_NAMES_QHPACKAGEDETAILS_TABLE = 'JobID, PackageID, PackageState'

#
# Progress log messages.
#
DOWNLOAD_STARTED = 'Download started for Update ID {}'
DOWNLOAD_COMPLETED = 'Download completed for Update ID {}'
CREATE_SOLO_UPDT_STARTED = 'Create solo update started for update ID {}'
CREATE_SOLO_UPDT_COMPLETED = 'Create solo update completed for Update ID {}'
CREATE_UPG_UPDT_STARTED = 'Create upg update started for update ID {}'
CREATE_UPG_UPDT_COMPLETED = 'Create upg update completed for Update ID {}'
CREATE_DIFF_UPDT_STARTED = 'Create differential update started for Version {} to {} for Update ID {}'
CREATE_DIFF_UPDT_COMPLETED = 'Create differential update completed for Version {} to {} for Update ID {}'
NO_DIFF_FILES_FOUND = 'No different files found for Version {} to {} for Update ID {}'
DIFF_TEST_STARTED = 'Difftest started for Patch file {}'
DIFF_TEST_COMPLETED = 'Difftest completed for Patch file {}'
UPDATE_INDEX_DAT_COMPLETED = 'Updated index dat for Update ID {}'
REVERT_STARTED = 'Revert Update started for Update ID {} from Previous Job ID {}'
REVERT_COMPLETED = 'Revert Update completed for Update ID {} from Previous Job ID {}'

DOWNLOAD_STARTED_QH = 'Download started for Package list : {}'
DOWNLOAD_COMPLETED_QH = 'Download completed for Package list : {}'

#
# Worker Thread counts
#
MAX_WORKER_GENDIFF = 16
MAX_WORKER_GNSOLO_E2 = 2
MAX_WORKER_GNSOLO_QH = 3

#
# Flags to set if difftest, gendiffupdt to be run or not.
#
RUN_DIFFTEST = 1
RUN_GENDIFFUPDT = 1

#
# Test server and release server path.
#
TEST_DEF_PATH = "/mnt/test_def"
RELEASE_DEF_PATH = "/mnt/release_def"

#
# Path at which ini file for automation will be generated.
#
AUTOMATION_DIR_PATH = "/mnt/test_def/automation"

#
# Make upg feture on
#
MAKE_UPG_SECTION="makeupg_info"
ISMAKUPGON="ismakeupgon"

#
# Update ID lists and code dir path.
# Used in cleanup scripts delete_outdated_jobs.py and delete_failed_jobs.py
#
CODE_DIR_PATH = "/mnt/code"
E2_UPDT_ID_LIST = ["4","5"]
QH_UPDT_ID_LIST = ["778","779","780", "781","782","783","784","785","786","787"]
QH_SIG_TYPE_LIST =["APEX","RtfDB","SMLDB"]