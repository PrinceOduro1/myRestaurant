from django.db import models
from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

# Create your models here.
class FASTUSER(models.Model):
    fullname = models.CharField(max_length=50)
    email = models.EmailField()
    password = models.CharField(max_length=128)

    def save(self, *args, **kwargs):
        # Hash the password if it's not already hashed
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fullname}"

class FASTMENU(models.Model):
    MENU_CATEGORY = [
        ('BREAKFAST', 'Breakfast'),
        ('LUNCH', 'Lunch'),
        ('SUPPER', 'Supper'),
        ('DRINKS', 'Drinks'),
        ('PASTRIES', 'Pastries')
    ]
    foodname = models.CharField(max_length=100)
    food_category = models.CharField(max_length=30, choices=MENU_CATEGORY)
    price = models.FloatField()
    elapse_time = models.IntegerField()
    meal_picture = models.ImageField(upload_to='meal_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.foodname}"
    
class CartItem(models.Model):
    user = models.ForeignKey(FASTUSER, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FASTMENU, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    user = models.ForeignKey(FASTUSER, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    items = models.ManyToManyField(CartItem)  # Link order to cart items
    status = models.CharField(max_length=20, default='Pending')
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"
    
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    stripe_payment_intent = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.stripe_payment_intent} - {self.status}"