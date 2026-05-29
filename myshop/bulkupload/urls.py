from django.urls import path

from .views import bulk_upload, test_ocr


urlpatterns = [

    path(
        '',
        bulk_upload
    ),

    path(
        'test-ocr/',
        test_ocr
    ),

]