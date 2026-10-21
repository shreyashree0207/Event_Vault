import os
from io import BytesIO
from pathlib import Path

import boto3
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


BACKEND_DIR = Path(__file__).resolve().parent
STORAGE_MODE = os.getenv("TICKETS_STORAGE", "local").strip().lower()
LOCAL_TICKETS_DIR = Path(
    os.getenv("TICKETS_LOCAL_DIR", str(BACKEND_DIR / "generated_tickets"))
).resolve()


def _make_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION") or None,
        endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
    )


def generate_ticket_pdf(
    *,
    ticket_code: str,
    booking_id: int,
    event_name: str,
    event_date: str,
    venue: str,
    seat_number: str,
) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    pdf.setTitle(f"Event Vault Ticket {ticket_code}")
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(inch, height - inch, "EVENT VAULT")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(inch, height - 1.45 * inch, "Event admission ticket")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(inch, height - 2.3 * inch, event_name[:80])
    pdf.setFont("Helvetica", 12)
    pdf.drawString(inch, height - 2.75 * inch, f"Date: {event_date}")
    pdf.drawString(inch, height - 3.1 * inch, f"Venue: {venue[:100]}")
    pdf.drawString(inch, height - 3.45 * inch, f"Seat: {seat_number}")
    pdf.drawString(inch, height - 3.8 * inch, f"Booking reference: {booking_id}")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(inch, height - 4.35 * inch, f"Ticket code: {ticket_code}")

    qr_code = qr.QrCodeWidget(ticket_code)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(2 * inch, 2 * inch, transform=[
        (1.7 * inch / qr_width, 0, 0, 1.7 * inch / qr_height, 0.15 * inch, 0.15 * inch)
    ])
    drawing.add(qr_code)
    renderPDF.draw(drawing, pdf, width - 3 * inch, height - 4 * inch)

    pdf.setFont("Helvetica", 9)
    pdf.drawString(inch, inch, "Keep this ticket private and present it at the venue.")
    pdf.save()
    return output.getvalue()


def store_ticket_pdf(ticket_code: str, content: bytes) -> str:
    key = f"tickets/{ticket_code}.pdf"

    if STORAGE_MODE == "local":
        path = (LOCAL_TICKETS_DIR / f"{ticket_code}.pdf").resolve()
        if path.parent != LOCAL_TICKETS_DIR:
            raise ValueError("Invalid ticket code for local storage.")
        LOCAL_TICKETS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    if STORAGE_MODE != "s3":
        raise RuntimeError("TICKETS_STORAGE must be either 'local' or 's3'.")

    bucket = os.getenv("S3_TICKETS_BUCKET", "").strip()
    if not bucket:
        raise RuntimeError("S3_TICKETS_BUCKET must be set when TICKETS_STORAGE=s3.")

    _make_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
        ContentType="application/pdf",
        ServerSideEncryption="AES256",
    )
    return key


def read_ticket_pdf(object_key: str) -> bytes:
    if STORAGE_MODE == "local":
        file_name = Path(object_key).name
        if not file_name.endswith(".pdf") or "/" in file_name or "\\" in file_name:
            raise ValueError("Invalid local ticket object key.")
        path = (LOCAL_TICKETS_DIR / file_name).resolve()
        if path.parent != LOCAL_TICKETS_DIR:
            raise ValueError("Invalid local ticket object key.")
        return path.read_bytes()

    if STORAGE_MODE != "s3":
        raise RuntimeError("TICKETS_STORAGE must be either 'local' or 's3'.")
    bucket = os.getenv("S3_TICKETS_BUCKET", "").strip()
    if not bucket:
        raise RuntimeError("S3_TICKETS_BUCKET must be set when TICKETS_STORAGE=s3.")
    response = _make_s3_client().get_object(Bucket=bucket, Key=object_key)
    return response["Body"].read()
