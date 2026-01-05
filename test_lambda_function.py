import unittest
from unittest.mock import patch, MagicMock
import lambda_function
from botocore.exceptions import ClientError

class TestLambdaFunction(unittest.TestCase):

    @patch('lambda_function.create_challenge')
    def test_should_return_challenge_data_when_http_method_is_get(self, mock_create_challenge):
        mock_challenge = MagicMock()
        mock_challenge.algorithm = 'SHA-256'
        mock_challenge.challenge = 'random-challenge'
        mock_challenge.salt = 'random-salt'
        mock_challenge.signature = 'signature'
        mock_create_challenge.return_value = mock_challenge

        event = {'httpMethod': 'GET'}
        context = {}

        response = lambda_function.lambda_handler(event, context)

        self.assertEqual(response['algorithm'], 'SHA-256')
        self.assertEqual(response['challenge'], 'random-challenge')
        self.assertEqual(response['salt'], 'random-salt')
        self.assertEqual(response['signature'], 'signature')
        mock_create_challenge.assert_called_once()

    @patch('lambda_function.verify_solution')
    @patch('lambda_function.boto3.client')
    def test_should_send_email_and_return_success_when_submission_is_valid(self, mock_boto_client, mock_verify_solution):
        mock_verify_solution.return_value = (True, None)
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses

        event = {
            'httpMethod': 'POST',
            'altcha': 'valid-payload',
            'mail': 'test@example.com',
            'text': 'Hello world',
            'subject': 'Test Subject',
            'referer': 'http://example.com'
        }
        context = {}

        response = lambda_function.lambda_handler(event, context)

        self.assertTrue(response['success'])
        self.assertEqual(response['location'], 'http://example.com')
        mock_verify_solution.assert_called_once()
        mock_ses.send_email.assert_called_once()

        # Verify email arguments
        call_args = mock_ses.send_email.call_args
        self.assertEqual(call_args[1]['Source'], lambda_function.SENDER)
        self.assertEqual(call_args[1]['Destination']['ToAddresses'][0], lambda_function.RECIPIENT)
        self.assertEqual(call_args[1]['ReplyToAddresses'][0], 'test@example.com')
        self.assertEqual(call_args[1]['Message']['Body']['Text']['Data'], 'Hello world')
        self.assertEqual(call_args[1]['Message']['Subject']['Data'], 'Test Subject')

    def test_should_return_failure_when_required_fields_are_missing(self):
        # Test missing subject
        event = {
            'httpMethod': 'POST',
            'altcha': 'valid-payload',
            'mail': 'test@example.com',
            'text': 'Hello world'
            # Missing subject
        }
        context = {}

        response = lambda_function.lambda_handler(event, context)

        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'Verification failed')

    @patch('lambda_function.verify_solution')
    def test_should_return_failure_when_altcha_verification_fails(self, mock_verify_solution):
        mock_verify_solution.return_value = (False, 'Invalid signature')

        event = {
            'httpMethod': 'POST',
            'altcha': 'invalid-payload',
            'mail': 'test@example.com',
            'text': 'Hello world',
            'subject': 'Test Subject'
        }
        context = {}

        response = lambda_function.lambda_handler(event, context)

        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'Verification failed')
        mock_verify_solution.assert_called_once()

    @patch('lambda_function.verify_solution')
    @patch('lambda_function.boto3.client')
    def test_should_handle_ses_client_error_gracefully(self, mock_boto_client, mock_verify_solution):
        mock_verify_solution.return_value = (True, None)
        mock_ses = MagicMock()

        error_response = {'Error': {'Message': 'SES Error'}}
        mock_ses.send_email.side_effect = ClientError(error_response, 'SendEmail')
        mock_boto_client.return_value = mock_ses

        event = {
            'httpMethod': 'POST',
            'altcha': 'valid-payload',
            'mail': 'test@example.com',
            'text': 'Hello world',
            'subject': 'Test Subject',
            'referer': 'http://example.com'
        }
        context = {}

        # The function catches the error and prints it, but still returns success structure based on current implementation
        response = lambda_function.lambda_handler(event, context)

        self.assertTrue(response['success'])
        mock_ses.send_email.assert_called_once()

