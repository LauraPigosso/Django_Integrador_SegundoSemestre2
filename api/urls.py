from django.urls import path, include
from api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('accounts', views.AccountViewSet)
router.register('transfer', views.TansferViewSet)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('loan/',views.LoanViewSet.as_view()),
    path('credit/',views.CreditViewSet.as_view()),
    path('credit/<int:pk>',views.CreditViewSet.as_view()),
]