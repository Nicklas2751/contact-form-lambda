from __future__ import print_function
from botocore.exceptions import ClientError
from urllib.request import urlopen
import boto3
import json
import requests

def lambda_handler(event, context):
    if "g-recaptcha-response" in event and "mail" in event and "text" in event:
        success = checkRecaptcha(event["g-recaptcha-response"])
    else:
        success = False

    if success:
        send_email(event["mail"],event["text"])
    else:
        print("RECaptcha failed!")
    
    return {
        "location": event["referer"]
    }

def checkRecaptcha(captchaCode):
    requestData = { "secret": "mySecret", "response": captchaCode }
    data = requests.post("https://www.google.com/recaptcha/api/siteverify", data=requestData)
    result = data.json()
    return result.get('success', None)

def send_email(userMail, content):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "My Sender <cloud@my.domain>"

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "recipient@my.domain"
    
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "eu-west-1"
    
    # The subject line for the email.
    SUBJECT = "A user has sent you a message"
    
    # The character encoding for the email.
    CHARSET = "UTF-8"
    
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    
    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT
                ]
            },
            ReplyToAddresses=[
                userMail,
            ],
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': content,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])