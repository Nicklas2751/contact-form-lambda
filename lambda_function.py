import os

import boto3
from altcha import create_challenge, verify_solution, ChallengeOptions
from botocore.exceptions import ClientError

# Configuration
SENDER = os.environ.get("SES_SENDER", "My Sender <cloud@my.domain>")
RECIPIENT = os.environ.get("SES_RECIPIENT", "recipient@my.domain")
AWS_REGION = os.environ.get("SES_REGION", "eu-west-1")
ALTCHA_HMAC_KEY = os.environ.get("ALTCHA_HMAC_KEY", "change-me-to-a-secret-key")

def lambda_handler(event, context):
    """
    AWS Lambda Handler for Contact Form with ALTCHA protection.
    Handles GET requests to generate a challenge and POST requests to submit the form.
    """
    method = event.get("httpMethod", "POST")

    # Handle Challenge Generation (GET)
    if method == "GET":
        return handle_get_challenge()

    # Handle Form Submission (POST)
    if "altcha" in event and "mail" in event and "text" in event and "subject" in event:
        success = check_altcha(event["altcha"])
    else:
        success = False
        print("Missing required fields")

    if success:
        if send_email(event["mail"], event["text"], event["subject"]):
            return {
                "success": True,
                "location": event.get("referer")
            }
        else:
            return {
                "success": False,
                "error": "Failed to send email"
            }
    else:
        print("ALTCHA verification failed!")
        return {
            "success": False,
            "error": "Verification failed"
        }

def handle_get_challenge():
    """Generates a new ALTCHA challenge."""
    options = ChallengeOptions(
        hmac_key=ALTCHA_HMAC_KEY,
        max_number=100000, # Adjust difficulty here
    )
    challenge = create_challenge(options)
    # Convert Challenge object to dictionary for JSON serialization
    return {
        "algorithm": challenge.algorithm,
        "challenge": challenge.challenge,
        "salt": challenge.salt,
        "signature": challenge.signature,
    }

def check_altcha(payload):
    """Verifies the ALTCHA payload."""
    if not payload:
        return False

    verified, err = verify_solution(payload, ALTCHA_HMAC_KEY, check_expires=True)
    if err:
        print(f"ALTCHA Error: {err}")
    return verified

def send_email(user_mail, content, subject):
    """Sends the email using AWS SES."""
    charset = "UTF-8"

    client = boto3.client('ses', region_name=AWS_REGION)

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [RECIPIENT]
            },
            ReplyToAddresses=[user_mail],
            Message={
                'Body': {
                    'Text': {
                        'Charset': charset,
                        'Data': content,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        return False
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")
        return True
