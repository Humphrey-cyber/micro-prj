from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from invest.models import Account, Investment, Category, UserInvestment
from django.shortcuts import get_object_or_404
import json
import requests
import base64
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime
from requests.auth import HTTPBasicAuth
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from .models import Investment
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import TruncDate

# Create your views here.

@csrf_exempt
@login_required

def payout(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = float(data.get("amount", 0))
            investment_id = int(data.get("investment_id"))
            if amount <= 0:
                return JsonResponse({"error": "Invalid amount."}, status=400)
            
            # Get the current user's account
            account = Account.objects.get(user=request.user)
            
            # Add the payout amount to the current balance
            account.balance += Decimal(str(amount))
            account.save()

            user_investment = UserInvestment.objects.create(
                user = request.user,
                investment_id = investment_id,
                amount = Decimal(str(amount)),
            )
            user_investment.save()

            return JsonResponse({"new_balance": account.balance})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)
def get_mpesa_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    return response.json().get("access_token")

def stk_push(request):
    phone_number = request.GET.get("phone")  
    amount = request.GET.get("amount")  

    if not phone_number or not amount:
        return JsonResponse({"error": "Phone number and amount are required"}, status=400)

    # ✅ Ensure the phone number is in 2547XXXXXXXX or 25411XXXXXXXX format
    if phone_number.startswith("07") or phone_number.startswith("011"):  
        phone_number = "254" + phone_number[1:]

    # ✅ Validate format (Safaricom supports 2547XXXXXXXX and 25411XXXXXXXX)
    if not (phone_number.startswith("2547") or phone_number.startswith("25411")) or len(phone_number) not in [12, 13]:
        return JsonResponse({"error": "Invalid phone number format"}, status=400)
    
    access_token = get_mpesa_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode("utf-8")

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": "Investment",
        "TransactionDesc": "Investment Payout"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)

    # Log the response
    print("🔴 M-Pesa API Response:", response.json())  # This will print in your terminal

    return JsonResponse(response.json())


@login_required
def home(request):
    print("✅ Home view reached!") # Debugging line
    user = request.user
    account, created = Account.objects.get_or_create(user=request.user)
    user_investments = UserInvestment.objects.filter(user=user)

    print("User Investments:", user_investments)  # Debugging line
    # Aggrerate investment  data for thwe pie chart

    #Pie Chart Data
    pie_totals = defaultdict(float)
    for investment in user_investments:
        name = investment.investment.name
        amount = investment.amount
        print(f"Investment: {name}, Amount: {amount}") # Debugging line
        pie_totals[name] += float(investment.amount)

    
    pie_data = list(pie_totals.values())
    pie_labels = list(pie_totals.keys())


    #Area chart Data
    daily_data =(
        user_investments
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(total=Sum('amount'))
        .order_by('date')
    )

    print("Daily Data:", daily_data)  # Debugging line

    area_labels = [entry['date'].strftime('%d %b %Y') for entry in daily_data]
    area_data = [float(entry['total']) for entry in daily_data]

    print("Pie Labels:", pie_labels)
    print("Pie Data:", pie_data)
    print("Area Labels:", area_labels)
    print("Area Data:", area_data)
 
    context = {
        'balance': account.balance,
        'status': account.status,
        'investment_chosen': account.investment_chosen,
        'recent_transaction': account.recent_transaction,
    }

    return render(request, 'home.html', {
        'pie_labels': json.dumps(pie_labels),
        'pie_data': json.dumps(pie_data),
        'area_labels': json.dumps(area_labels), 
        'area_data': json.dumps(area_data),
    })

def register(request):
    if request.user.is_authenticated:
        messages.error(request, 'You are already logged in')    
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if len(password) < 3:
            messages.error(request, 'password is too short')
            return redirect('register')
        
        get_all_users_by_username = User.objects.filter(username=username)
        if get_all_users_by_username:
            messages.error(request, 'Username is already taken use another username')
            return redirect('register')

        new_user = User.objects.create_user(username=username, email=email, password=password)
        new_user.save()
        messages.success(request, 'User successfully created, Login now ')
        return redirect('login')
    

    return render(request, 'register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('uname')
        password = request.POST.get('pass')

        validate_user = authenticate(username=username, password=password)
        if validate_user is not None:
            login(request, validate_user)
            return redirect('home')
        else:
            messages.error(request, 'User does not exist')
            return redirect('login')
        

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def investments(request):
    categories = Category.objects.all()
    investments = Investment.objects.all()
    return render(request, 'investments.html', {'categories': categories, 'investments': investments} )

def investment_detail(request, id):
    investments = Investment.objects.all()
    investment = get_object_or_404(Investment, id=id)
    return render(request, 'investment_detail.html', {'investment': investment})

def account_status(request):
    # Example account status (Replace with actual data from database)
    user_status = "Active"  # Fetch this from your database in a real-world scenario

    return render(request, 'account_status.html', {'status': user_status})

""""
@csrf_exempt
def submit_investment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        investment_id = data.get("investment_id")
        investment_name = data.get("investment_name")
        funds = float(data.get("funds"))  # Updated

        # Save the investment to the database
        investment = Investment.objects.create(
            investment_id=investment_id,
            name=investment_name,
            funds=funds  # Updated
        )

        # Fetch updated investments for chart
        investments = Investment.objects.values("name").annotate(total_funds=sum("funds"))
        
        return JsonResponse({"success": True, "investments": list(investments)})

    return JsonResponse({"success": False, "message": "Invalid request"})
"""""
def invest(request):
    if request.method == "POST":
        investment_id = request.POST.get('investment_id')
        amount = request.POST.get('amount')

        investment = Investment.objects.get(id=investment_id)
        UserInvestment.objects.create(
            user=request.user,
            investment=investment,
            amount=amount,
            )

        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})