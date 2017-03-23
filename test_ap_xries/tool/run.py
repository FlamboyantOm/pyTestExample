import sys,os
TOOL_PATH = ''
print('___________Run AddGen Tool_______________')
print(sys.argv)
command = 'addgendb.exe /add '+str(sys.argv[1])+' AgeDBConfig.ini'
os.system('dir')
#os.system(command)
#print(command)
