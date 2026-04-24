# services.py
from sumup import Sumup
import os
from .models import Payment
import uuid
import requests
import certifi

# Fix SSL cassé par PostgreSQL sur Windows
os.environ.pop("CURL_CA_BUNDLE", None)
os.environ.pop("REQUESTS_CA_BUNDLE", None)


def _base_url():
    return os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")


def create_sumup_checkout(user):
    client = Sumup(api_key=os.getenv("SUMUP_API_KEY"))
    merchant_code = os.getenv("SUMUP_MERCHANT_CODE")

    if not merchant_code:
        raise ValueError("MERCHANT_CODE non défini")

    checkout_reference = str(uuid.uuid4())
    base = _base_url()

    if user.role == "taxi":
        amount = 5.0
        description = "Inscription Taxi H24Go"
        redirect_url = f"{base}/taxi/payment/callback/"
    elif user.role == "coiffeuse":
        amount = 5.0
        description = "Inscription Coiffeuse H24Go"
        redirect_url = f"{base}/coiffeuse/payment/callback/"
    else:
        raise ValueError("Role non pris en charge pour paiement")

    checkout = client.checkouts.create({
        "merchant_code": merchant_code,
        "amount": amount,
        "currency": "EUR",
        "checkout_reference": checkout_reference,
        "description": description,
        "redirect_url": redirect_url
    })

    Payment.objects.create(
        user=user,
        role=user.role,
        amount=amount,
        status="pending",
        checkout_id=checkout.id
    )

    return checkout.id


def get_checkout_raw(checkout_id):
    api_key = os.getenv("SUMUP_API_KEY")
    url = f"https://api.sumup.com/v0.1/checkouts/{checkout_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    resp = requests.get(url, headers=headers, verify=certifi.where())
    resp.raise_for_status()
    checkout_json = resp.json()

    for tx in checkout_json.get("transactions", []):
        if "entry_mode" in tx:
            tx["entry_mode"] = tx["entry_mode"].lower().replace("_", " ")

    return checkout_json


def create_sumup_checkout_course(client_user, course):
    api_key = os.getenv("SUMUP_API_KEY")
    merchant_code = os.getenv("SUMUP_MERCHANT_CODE")

    if not merchant_code:
        raise ValueError("MERCHANT_CODE non défini")
    if not course.prix_propose:
        raise ValueError("Prix non défini pour cette course")

    checkout_reference = str(uuid.uuid4())
    base = _base_url()

    resp = requests.post(
        "https://api.sumup.com/v0.1/checkouts",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "merchant_code": merchant_code,
            "amount": float(course.prix_propose),
            "currency": "EUR",
            "checkout_reference": checkout_reference,
            "description": f"Course Taxi H24Go #{course.id}",
            "redirect_url": f"{base}/client/course/payment/callback/"
        },
        verify=certifi.where()
    )
    resp.raise_for_status()
    checkout_data = resp.json()

    Payment.objects.create(
        user=client_user,
        role="client",
        amount=float(course.prix_propose),
        status="pending",
        checkout_id=checkout_data["id"],
        course=course
    )

    return checkout_data["id"]
    return checkout.id