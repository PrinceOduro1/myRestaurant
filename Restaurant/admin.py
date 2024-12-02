from django.contrib import admin
from .models import FASTMENU,FASTUSER,CartItem,Order,Payment
# Register your models here.
admin.site.register(FASTUSER)
admin.site.register(FASTMENU)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(Payment)