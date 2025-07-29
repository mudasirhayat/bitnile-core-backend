
from django.urls import path
from . import views

urlpatterns = [
    path('show_stats/',views.show_stats,name='show_statisics_for_admin'),
    path('save_data/',views.user_saving_view,name='save_user_data_view'),
    path('show_metrics/',
     views.metrics, name='metric'),
    path('show_photo/<str:user_id>/',
         views.show_photo_by_id, name='show_photo_by_id'),
    path('download_photo/<str:user_id>/',
         views.DownloadPhotoView.as_view(), name='download_photo'),
    path('download_stat/',
         views.DownloadStatView.as_view(), name='download_stat'),
    path('share_facebook/<str:user_id>',
         views.ShareFacebookView.as_view(), name='share_facebook'),
    path('share_twitter/<str:user_id>',
         views.ShareTwitterView.as_view(), name='share_twitter'),
    path('downloads/',
         views.Download.as_view(), name='download'),
]