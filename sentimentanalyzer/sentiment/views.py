from django.shortcuts import render
from textblob import TextBlob

def home(request):
    return render(request, 'home.html')

def result(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if polarity > 0:
            result = "Positive 😊"
        elif polarity < 0:
            result = "Negative 😟"
        else:
            result = "Neutral 😐"

    return render(request, 'result.html', {
        'text' : text,
        'result': result,
        'polarity': polarity,
        'subjectivity': subjectivity
    })