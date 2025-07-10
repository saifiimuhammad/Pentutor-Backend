import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
 
from .utils import generate_secure_hash



def initiate_payment(request):
    payload = {
        "pp_Version": "1.1",
        "pp_TxnType": "MWALLET",
        "pp_Language": "EN",
        "pp_MerchantID": settings.MERCHANT_ID,
        "pp_Password": settings.API_PASSWORD,
        "pp_TxnRefNo": "T" + timezone.now().strftime('%Y%m%d%H%M%S'),
        "pp_Amount": "1000",  # 1000 PKR = 10.00
        "pp_TxnDateTime": timezone.now().strftime('%Y%m%d%H%M%S'),
        "pp_BillReference": "invoice001",
        "pp_Description": "Payment for order",
        "pp_ReturnURL": "https://yourdomain.com/payment/response/",
    }
    
    # Hash it
    payload["pp_SecureHash"] = generate_secure_hash(payload, settings.INTEGRITY_SALT)

    response = requests.post(settings.PAYMENT_API_URL, data=payload)
    return JsonResponse(response.json())


@csrf_exempt
def payment_response(request):
    data = request.POST.dict()
    received_hash = data.pop("pp_SecureHash")

    calculated_hash = generate_secure_hash(data, settings.INTEGRITY_SALT)

    if calculated_hash == received_hash and data["pp_ResponseCode"] == "000":
        return HttpResponse("Payment Successful")
    return HttpResponse("Payment Failed")