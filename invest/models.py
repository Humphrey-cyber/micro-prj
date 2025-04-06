from django.db import models
from django.contrib.auth.models import User

# Create your models here.


# Create your models here.
class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, default="Active")
    investment_chosen = models.CharField(max_length=50, default="None")
    recent_transaction = models.CharField(max_length=255, default="No Transaction")

    def __str__(self):
        return f"{self.user.username}'s Account"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name 
      

class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(default="No Description")
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='investments/', default='default.jpg')

    def __str__ (self):
        return f"{self.user.username} - {self.name} - ${self.amount} "
    
class UserInvestment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.investment.name} - {self.amount}"

    

