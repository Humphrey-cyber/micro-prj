from django.contrib import admin
from .models import Investment, Category, Account

# Register your models here.
admin.site.register(Investment)
admin.site.register(Category)
admin.site.register(Account)
