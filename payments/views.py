from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .jazzcash import generate_jazzcash_url
from .easypaisa import generate_easypaisa_url

from .models import Payment
from meetings.models import Meeting

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_jazzcash(request):
    meeting_id = request.data.get("meeting_id")
    amount = float(request.data.get("amount", 0))
    user = request.user

    meeting = Meeting.objects.get(id=meeting_id)
    payment_url, txn_ref = generate_jazzcash_url(user, meeting_id, amount)

    Payment.objects.create(
        user=user,
        meeting=meeting,
        amount=amount,
        txn_ref=txn_ref,
        gateway="jazzcash",
    )

    return Response({"payment_url": payment_url})

@api_view(['GET'])
def verify_jazzcash(request):
    txn_ref = request.GET.get("pp_TxnRefNo")
    status = request.GET.get("pp_ResponseCode")

    try:
        payment = Payment.objects.get(txn_ref=txn_ref)
        if status == "000":
            payment.is_successful = True
            payment.save()
            return Response({"status": "success"})
        else:
            return Response({"status": "failed"})
    except Payment.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=404)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_easypaisa(request):
    meeting_id = request.data.get("meeting_id")
    amount = float(request.data.get("amount", 0))
    user = request.user

    meeting = Meeting.objects.get(id=meeting_id)
    payment_url, txn_ref = generate_easypaisa_url(user, meeting_id, amount)

    Payment.objects.create(
        user=user,
        meeting=meeting,
        amount=amount,
        txn_ref=txn_ref,
        gateway="easypaisa",
    )

    return Response({"payment_url": payment_url})

@api_view(['GET'])
def verify_easypaisa(request):
    txn_ref = request.GET.get("orderRefNum")
    status = request.GET.get("paymentStatus")  

    try:
        payment = Payment.objects.get(txn_ref=txn_ref)
        if status == "SUCCESS":
            payment.is_successful = True
            payment.save()
            return Response({"status": "success"})
        else:
            return Response({"status": "failed"})
    except Payment.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=404)
