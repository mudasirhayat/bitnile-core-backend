from django.shortcuts import render
import pytz
from django.core.paginator import Paginator
from django.db.models.functions import Trunc
from django.db.models import Count
from .models import User
from rest_framework import status
import requests
import json
from django.db.models import Sum
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from django.http import HttpResponse
from django.core.mail import send_mail
from twilio.rest import Client
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import csv
import urllib
import io
import os
from django.core.mail import EmailMultiAlternatives
import rebrand
from django.template.loader import render_to_string
from rest_framework.decorators import api_view




def send_emails(email,s3link):
    context = {'url': f"https://{s3link}"}
    email_template = '../templates/email.html'
    subject = 'A message from the BITNILE Racing Team'
    html_message = render_to_string(email_template, {"context": context})
    # plain_message=strip_tags(html_message)
    msg = EmailMultiAlternatives(
        subject,
        html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    msg.mixed_subtype = 'related'
    msg.attach_alternative(html_message, "text/html")
    # file_path=os.path.join(settings.BASE_DIR,'bitnile_api','static','images','logo.png')
    # with open(file_path, 'rb') as f:
    #         img = MIMEImage(f.read())
    #         img.add_header('Content-ID', '<{name}>'.format(name='logo.png'))
    #         img.add_header('Content-Disposition', 'inline', filename='logo.png')    
    # msg.attach(img)
    msg.send()




def send_SMS(phone_number,s3link,url):
    account_sid =settings.ACCOUNT_SID
    auth_token = settings.AUTH_TOKEN
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
        to=phone_number,
        from_='+13178540143',
        media_url=url,
        body=f'Thanks for visiting the https://BITNILE.COM display at the Portland International Raceway. Enjoy this digital memory of the INDYCAR SERIES BITNILE.COM Grand Prix of Portland, courtesy of the BITNILE Racing Team. \n Click here to see your memory: {s3link}\n #Bitnile #BitnileRacing'
        )
        print(message.sid)
    except Exception as e:
        print(f"SMS sending error : {e}")



def metrics(request):
    tz = pytz.timezone('America/Chicago')
    user_count = User.objects.filter(
        is_uploaded=True
    ).annotate(
        date=Trunc('created_at', 'day', tzinfo=tz),
    ).values(
        'date'
    ).annotate(
        user_count=Count('id'),
        facebook_share=Sum('facebook_share'),
        twitter_share=Sum('twitter_share'),
        visits=Sum('visits'),
        downloads=Sum('downloads'),
    ).order_by('date')
    response_data = {
        'id': 0,
        'data': [],
        'total': {
            'user_count': 0,
            'visits': 0,
            'fb_share': 0,
            'twitter_share': 0,
            'downloads': 0,
        }
    }
    id_count = 0
    for item in user_count:
        id_count += 1
        date = item['date']
        user_count_on_date = item['user_count']
        animations = User.objects.filter(
            is_uploaded=True,
            created_at__date=date,
        ).values_list('url', flat=True)
        total_downloads_on_date = item['downloads']
        response_data['data'].append({
            'id': id_count,
            'date': date.strftime('%d, %B %Y'),
            'user_count': user_count_on_date,
            's3_urls': list(animations),
            'visits': item['visits'],
            'fb_share': item['facebook_share'],
            'twitter_share': item['twitter_share'],
            'downloads': total_downloads_on_date,
        })
        response_data['total']['user_count'] += user_count_on_date
        response_data['total']['visits'] += item['visits']
        response_data['total']['fb_share'] += item['facebook_share']
        response_data['total']['twitter_share'] += item['twitter_share']
        response_data['total']['downloads'] += total_downloads_on_date
    return render(request, 'metrics.html', response_data)

class DownloadStatView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=stats.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Name','Email','Phone Number','URL', 'Views', 'Downloads',
                         'Facebook Shares', 'Twitter Shares','Total Shares'])

        print(writer)
        animations = User.objects.all()
        users_sorted = sorted(animations, key=lambda a: a.created_at)
        for user in users_sorted:  
            utc_date = user.created_at
            chicago_tz = pytz.timezone('America/Chicago')
            chicago_date = utc_date.astimezone(chicago_tz)
            chicago_date_str = str(chicago_date.strftime('%d %B %Y'))
            writer.writerow([chicago_date_str,user.first_name+" "+user.last_name , user.email , user.phone , user.url , user.visits,
                             user.downloads, user.facebook_share, user.twitter_share,int(user.facebook_share)+int(user.twitter_share)])
        print(response)
        return response


class ShareFacebookView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = kwargs['user_id']
        user = User.objects.get(pk=user_id)
        user.facebook_share+=1
        user.save()
        return HttpResponse({status: 200})


class ShareTwitterView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = kwargs['user_id']
        user = User.objects.get(pk=user_id)
        user.twitter_share += 1
        user.save()
        return HttpResponse({status: 200})
    


class DownloadPhotoView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        user_id = kwargs['user_id']
        record = User.objects.get(pk=user_id)

        print(record.url)
        r = urllib.request.urlopen(record.url)

        data = io.BytesIO(r.read())
        print(data)
        print("done with data")
        response = FileResponse(data)
        print("done with response")
        response['Content-Type'] = 'image/jpeg'
        filename = f'{record.first_name}.jpeg'
        response['Content-Disposition'] = "attachment; filename=%s" % filename

        record.downloads += 1
        record.save()
        return response    
    

class Download(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        url = request.GET.get('arg')
        name, key = url.split('/', 3)[2:]
        r = urllib.request.urlopen(url)
        data = io.BytesIO(r.read())
        response = FileResponse(data)
        response['Content-Type'] = 'image/png'
        filename = key
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response


def show_photo_by_id(request, user_id):
    try:
        record = User.objects.get(pk=user_id)
        record.visits += 1
        record.save()

        return render(request, "fan_experience.html", {"link": record.url, "user_id": record.pk,"title":record.first_name ,
                                                       "page_link": f"https://bitnile-backend.herokuapp.com/api/show_photo/{record.pk}",
                                                       "faceboook_link": f"https://www.facebook.com/sharer/sharer.php?u=https://bitnile-backend.herokuapp.com/api/show_photo/{record.pk}",
                                                       "twitter_link": f"http://twitter.com/share?url=https://bitnile-backend.herokuapp.com/api/show_photo/{record.pk}",
                                                       })
    except:
        return render(request, "not_found.html")
    



def show_stats(request):
    context = {}
    user_list = User.objects.all()
    paginator = Paginator(user_list, 10)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    return render(request, 'show_stats.html', {'users': users})


def link_shortner(link):
    rebrand.api_key = 'your-api-key'
    try:
        short_url = rebrand.shorten_url(link)
        print(short_url)
        return short_url
    except Exception as e:
        print(f'Link Shortner Error {e}')


def shorten_link(destination):
    linkRequest = {
    "destination": f"{destination}"
    , "domain": { "fullName": "rebrand.ly" }
    # , "slashtag": "A_NEW_SLASHTAG"
    # , "title": "Rebrandly YouTube channel"
    }
    apikey=settings.APIKEY
    workspace=settings.WORKSPACE
    requestHeaders = {
    "Content-type": "application/json",
    "apikey": apikey,
    "workspace": workspace
    }

    r = requests.post("https://api.rebrandly.com/v1/links", 
        data = json.dumps(linkRequest),
        headers=requestHeaders)

    if (r.status_code == requests.codes.ok):
        link = r.json()
        print("Long URL was %s, short URL is %s" % (link["destination"], link["shortUrl"]))
        return link["shortUrl"]




@api_view(['POST'])
def user_saving_view(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    email = request.data.get('email')
    phone = request.data.get('phone')
    try:
        # url=link_shortner(request.data.get('url'))
        url=request.data.get('url')
        is_uploaded=True
    except Exception as e:
        url=''
        is_uploaded=False
        print(f"S3 URL error {e}")
    try:
        user=User(first_name=first_name,last_name=last_name,email=email,phone=phone,url=url,is_uploaded=is_uploaded)
        user.save()
        s3_link=shorten_link(f"https://bitnile-backend.herokuapp.com/api/show_photo/{user.pk}/")
        # s3_link=shorten_link(f"http://localhost:8000/api/show_photo/{user.pk}/")
        send_emails(user.email,s3_link)
        send_SMS(user.phone,s3_link,user.url)
        return Response(status=status.HTTP_201_CREATED)
    except Exception as e:
        print(e)
        return Response(status=status.HTTP_400_BAD_REQUEST)



