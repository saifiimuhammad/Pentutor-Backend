from django.urls import path
from . import views

urlpatterns = [
    path('pay/', views.initiate_payment, name='initiate_payment'),
    path('response/', views.payment_response, name='payment_response'),
]