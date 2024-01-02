from django.shortcuts import render


def show_statistic(request):
    return render(request, 'app01/statistic.html')
