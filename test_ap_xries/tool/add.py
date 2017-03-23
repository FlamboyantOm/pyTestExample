
from django.shortcuts import *

def formdisplay(request):

        return render(request, 'addition.html')


def addnum(request):
    n1,n2 = 0,0
    if request.method == 'POST':
        print("in addnum")
        n1 = request.POST.get('num1', '')
        n2 = request.POST.get('num2', '')
        print(n1,n2)
    sum = 0

    sum = int(n1 )+ int(n2)

    return HttpResponse(sum)


