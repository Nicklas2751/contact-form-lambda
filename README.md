# Serverless Contact Form with ALTCHA Protection

[![Build and Test](https://github.com/Nicklas2751/contact-form-lambda/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/Nicklas2751/contact-form-lambda/actions/workflows/build-and-test.yml)
[![Deploy to AWS Lambda](https://github.com/Nicklas2751/contact-form-lambda/actions/workflows/deploy.yml/badge.svg)](https://github.com/Nicklas2751/contact-form-lambda/actions/workflows/deploy.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Nicklas2751/contact-form-lambda)](https://github.com/Nicklas2751/contact-form-lambda/releases)
[![License](https://img.shields.io/github/license/Nicklas2751/contact-form-lambda)](https://github.com/Nicklas2751/contact-form-lambda/blob/main/LICENSE)

A robust, serverless contact form backend running on AWS Lambda, protected against spam using [ALTCHA](https://altcha.org/) (Alternative CAPTCHA). This solution allows you to receive contact form submissions via email (AWS SES) without managing servers or using intrusive cookies/tracking.

## Features

- **Serverless**: Runs on AWS Lambda (Python 3.14+).
- **Spam Protection**: Uses [ALTCHA](https://altcha.org/), a privacy-friendly, proof-of-work based CAPTCHA alternative. No cookies, no tracking.
- **Email Delivery**: Sends emails using Amazon Simple Email Service (SES).
- **API Gateway**: Exposed via AWS API Gateway with VTL templates for request transformation.
- **CI/CD**: Fully automated deployment pipeline using GitHub Actions.

## Architecture

1.  **Client**: HTML Form with ALTCHA widget sends data to API Gateway.
2.  **API Gateway**: Receives HTTP GET (Challenge) and POST (Submission) requests. Uses VTL templates to transform form data into JSON.
3.  **Lambda**:
    - **GET**: Generates a cryptographic challenge for ALTCHA.
    - **POST**: Verifies the ALTCHA solution and sends the email via SES.
4.  **SES**: Delivers the email to your inbox.

## Prerequisites

- An AWS Account.
- A verified domain or email address in AWS SES.
- AWS CLI installed and configured (optional, for CLI setup).
- Python 3.14+ installed locally for development.

---

## Setup Guide

You can set up the infrastructure using the AWS Management Console or the AWS CLI.

### Option 1: AWS Management Console (Manual)

#### 1. AWS SES Setup
1.  Go to **Amazon SES** -> **Identities**.
2.  Create an identity for your sender email (e.g., `noreply@yourdomain.com`) and recipient email (if in Sandbox mode).
3.  Verify them via the confirmation emails.

#### 2. Create Lambda Function
1.  Go to **Lambda** -> **Create function**.
2.  Name: `website-contact-form`.
3.  Runtime: **Python 3.14**.
4.  Architecture: **x86_64** (or arm64).
5.  Create the function.
6.  **Permissions**: Go to **Configuration** -> **Permissions**. Click the Role name. Attach the policy `AmazonSESFullAccess` (or a more restrictive inline policy allowing `ses:SendEmail`).

#### 3. Configure Environment Variables
Go to **Configuration** -> **Environment variables** and add:
- `SES_SENDER`: Verified sender email.
- `SES_RECIPIENT`: Recipient email.
- `SES_REGION`: e.g., `eu-west-1`.
- `ALTCHA_HMAC_KEY`: A long random string (secret).

#### 4. API Gateway Setup
1.  Go to **API Gateway** -> **Create API** -> **REST API** (Build).
2.  Create a new API named `ContactFormAPI`.
3.  **Create Resource**: `/contact` (or use root `/`).
4.  **Create Methods**: `GET` and `POST`.
5.  **Setup POST**:
    - Integration type: **Lambda Function**.
    - Select your function.
    - **Integration Request** -> **Mapping Templates**:
        - Content-Type: `application/x-www-form-urlencoded`.
        - Template: Copy content from `api_gateway_mapping_template.vtl`.
6.  **Setup GET**:
    - Integration type: **Lambda Function**.
    - **Integration Request** -> **Mapping Templates**:
        - Content-Type: `application/json`.
        - Template: Copy content from `api_gateway_mapping_template.vtl`.
        - **Request body passthrough**: "When there are no templates defined".
7.  **Enable CORS**: Select the resource -> **Actions** -> **Enable CORS**. Allow `Access-Control-Allow-Origin: '*'`.
8.  **Deploy API**: Actions -> **Deploy API** -> New Stage (e.g., `prod`).

---

### Option 2: AWS CLI Setup

Replace placeholders like `YOUR_ACCOUNT_ID`, `eu-west-1`, etc.

```bash
# 1. Create IAM Role for Lambda
aws iam create-role --role-name ContactFormLambdaRole --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'

# 2. Attach SES Permissions
aws iam attach-role-policy --role-name ContactFormLambdaRole --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess
aws iam attach-role-policy --role-name ContactFormLambdaRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 3. Create Lambda Function (Upload a dummy zip first or deploy via GitHub Actions later)
zip function.zip lambda_function.py
aws lambda create-function --function-name website-contact-form \
--zip-file fileb://function.zip --handler lambda_function.lambda_handler --runtime python3.14 \
--role arn:aws:iam::YOUR_ACCOUNT_ID:role/ContactFormLambdaRole

# 4. Set Environment Variables
aws lambda update-function-configuration --function-name website-contact-form \
--environment "Variables={SES_SENDER=noreply@example.com,SES_RECIPIENT=you@example.com,SES_REGION=eu-west-1,ALTCHA_HMAC_KEY=supersecretkey}"

# 5. Create API Gateway (Simplified - Console is recommended for VTL complexity)
aws apigateway create-rest-api --name "ContactFormAPI"
# Note: Configuring Resources, Methods, and VTL templates via CLI is verbose. 
# It is recommended to use the Console or Terraform/CloudFormation for the API Gateway part.
```

---

## GitHub Actions Integration

To enable automated deployments, you need to create an IAM user and set GitHub Secrets.

### 1. Create IAM User for Deployment
Create a user (e.g., `github-deployer`) with the following permissions (JSON Policy):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["lambda:UpdateFunctionCode", "lambda:UpdateAlias", "lambda:GetAlias", "lambda:CreateAlias"],
            "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:website-contact-form"
        }
    ]
}
```

### 2. GitHub Secrets
Go to your repository **Settings** -> **Secrets and variables** -> **Actions** and add:

| Secret Name | Description |
|-------------|-------------|
| `AWS_ACCESS_KEY_ID` | Access Key for the IAM User. |
| `AWS_SECRET_ACCESS_KEY` | Secret Key for the IAM User. |
| `AWS_REGION` | AWS Region (e.g., `eu-west-1`). |
| `AWS_LAMBDA_FUNCTION_NAME` | Name of your function (e.g., `website-contact-form`). |

---

## Client-Side Integration

### 1. Get your API URL
You can find your API Endpoint URL in the AWS Console under **API Gateway** -> **Stages** -> **prod** -> **Invoke URL**.

Or via CLI:
```bash
aws apigateway get-rest-apis
# Look for the 'id' of your API
aws apigateway get-stage --rest-api-id YOUR_API_ID --stage-name prod
```
URL format: `https://{rest-api-id}.execute-api.{region}.amazonaws.com/prod/contact`

### 2. Example HTML Form

Include the ALTCHA widget script and configure the form.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact Form</title>
    <!-- Import ALTCHA Widget -->
    <script async defer src="https://cdn.jsdelivr.net/gh/altcha-org/altcha@main/dist/altcha.min.js" type="module"></script>
</head>
<body>
    <h1>Contact Us</h1>
    
    <!-- Replace YOUR_API_GATEWAY_URL with your actual URL -->
    <form action="YOUR_API_GATEWAY_URL" method="POST">
        
        <label for="mail">Email:</label>
        <input type="email" id="mail" name="mail" required>
        
        <label for="subject">Subject:</label>
        <input type="text" id="subject" name="subject" required>

        <label for="text">Message:</label>
        <textarea id="text" name="text" required></textarea>

        <!-- ALTCHA Widget -->
        <!-- The challengeurl is the same as the form action (GET request) -->
        <altcha-widget challengeurl="YOUR_API_GATEWAY_URL"></altcha-widget>

        <button type="submit">Send</button>
    </form>
</body>
</html>
```

---

## Local Development

To run tests and develop locally:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Nicklas2751/contact-form-lambda.git
    cd contact-form-lambda
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Tests**:
    ```bash
    python -m unittest discover
    ```

## License

This project is licensed under the MIT License.

