from django.urls import path

from .views import bulk_upload


urlpatterns = [

    path(
        '',
        bulk_upload
    ),

]