import smtplib
from django.conf import settings

print("Usuario:", repr(settings.EMAIL_HOST_USER), "| largo clave:", len(settings.EMAIL_HOST_PASSWORD))

for nombre, ssl, puerto in (("587 STARTTLS", False, 587), ("465 SSL", True, 465)):
    print("\n=====", nombre, "=====")
    try:
        if ssl:
            s = smtplib.SMTP_SSL("smtp.gmail.com", puerto, timeout=15)
        else:
            s = smtplib.SMTP("smtp.gmail.com", puerto, timeout=15)
            s.ehlo(); s.starttls(); s.ehlo()
        s.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("LOGIN OK")
        s.quit()
    except Exception as e:
        print("FALLO:", type(e).__name__, e)
