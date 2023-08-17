from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns=[
     # throttle check
    path('throttle', views.throttle_check),
    
    path('category',views.item_category),
    path('category/<int:id>', views.category_single),

    path('menu-items/',views.menu_items),
    path('menu-items/<int:id>',views.menu_single),

    path('groups/<str:group_name>/users', views.group_users),
    path('groups/<str:group_name>/users/<int:userId>', views.group_user_detail),
    
    path('cart/menu-items',views.cart_management),
    
    path('orders',views.order_management),
    path('orders/<int:orderId>',views.order_detail),

    path('api-token-auth/',obtain_auth_token), #admin: "token": "1f5ba40d017278c8292172e9063bb2fc94a54fe4"  #adrian:"token": "3c3589b0086bb93a2a7452ad39d2e010c7d01fe6"  #mario:"token": "b60885157331f37c6b2f3b64cc655fbb7af64e23"
]                                           