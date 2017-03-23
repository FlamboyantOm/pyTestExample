import os,sys

from shutil import copy2
def create_inx(file,path):
    # ini_file = open(file,'r')
    # if os.path.isdir(file):
    #     fileList = os.listdir(file)
    #     filenameArr = []
    #     for fileList in fileList:
    #         filenameArr.append(fileList)
    #
    #     if os.path.exists('D:/webdev/apex/data/inx/'):
    #       #shutil.copy(file,settings.DATA_FOLDER + 'inx/')
    #       for f in filenameArr:
    #           copy2(file+'/'+f, 'D:/webdev/apex/data/inx/')
    #     else:
    #        os.makedirs('D:/webdev/apex/data/inx/', exist_ok=True)
    #        #shutil.copy(file, settings.DATA_FOLDER + 'inx/')
    #        for f in filenameArr:
    #            copy2(file+'/'+f, 'D:/webdev/apex/data/inx/')
    if os.path.isfile(file):
        if not os.path.exists(path):
            os.makedirs(path,exist_ok=True)
        copy2(file,path)


def main():
    create_inx(sys.argv[1],sys.argv[2])

if __name__ == '__main__':
    main()
