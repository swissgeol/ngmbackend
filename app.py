import boto3
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify
from flask_api import status
from flask_cors import CORS
from basicauth import decode

app = Flask(__name__)
CORS(app)

@app.route("/")
def root():
    return "welcome to NGM api server"

class NgmHttpError(Exception):
    status_code = 400
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(NgmHttpError)
def handle_http_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def get_file_from_bucket(bucket_name, file_name, access_key, secret_key, session_token):
    try:
        conn = boto3.client('s3',
                            region_name='eu-central-1',
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            aws_session_token=session_token)
        response = conn.get_object(Bucket=bucket_name,
                                   Key=file_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise NgmHttpError("No such key : {}".format(file_name),
                                                         status_code = status.HTTP_404_NOT_FOUND)
        else:
            raise NgmHttpError("unknown error: {}".format(e), status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        raise NgmHttpError("bucket ({}) or file ({}) not valids. \n{}".format(bucket_name, file_name, e),
                                                                              status_code = status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response['Body'].read()


@app.route('/tiles/<path:path>')
def get_tile(path):
    s3key = 'tiles/' + path
    try:
        # we cheat with a usual basic-auth header to get the AWS public and secret key
        # the true authorization will be done via boto3 on AWS api
        # reminder:
        # Authorization: Basic $(echo -n aws_key:aws_secret.session_token | base64 --wrap=0)
        authHeader = request.headers['Authorization']
        access_key, tmp = decode(authHeader)
        aws_secret_key, session_token = tmp.split('.')
    except AttributeError as e:
        raise NgmHttpError('Authorization required', status.HTTP_401_UNAUTHORIZED)

    return get_file_from_bucket('ngm-dev-authenticated-resources',
                                 s3key,
                                 access_key,
                                 aws_secret_key,
                                 session_token)
