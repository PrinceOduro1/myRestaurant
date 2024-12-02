from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('signup',views.signup,name='signup'),
    path('login',views.login,name='login'),
    path('admin_dashboard',views.admin_dashboard,name="admin_dashboard"),
    path('logout',views.logout,name="logout"),
    path('menu',views.menu,name="menu"),
    path('add_to_cart', views.add_to_cart, name='add_to_cart'),
    path('view_cart',views.view_cart,name='view_cart'),
    path('delete_cart/<int:cart_id>',views.delete_cart,name="delete_cart"),
    path('create_order', views.create_order, name='create_order'),
    path('create_payment', views.create_payment, name='create_payment'),  # This will be used to initiate payment and show the payment page
    path('payment_success', views.payment_success, name='payment_success'),  # You can create a success page for after payment
    path('stripe_webhook', views.stripe_webhook, name='stripe_webhook'),
    path('del_model',views.del_model,name='del_model'),
    path('payment-form/<int:order_id>/', views.payment_form, name='payment_form')
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)