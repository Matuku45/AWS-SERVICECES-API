from flask import Flask, jsonify, redirect, request
import boto3
from botocore.exceptions import ClientError
from flasgger import Swagger
import json
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Swagger config
app.config['SWAGGER'] = {
    'title': 'AWS & Gemini API Dashboard',
    'uiversion': 3,
}
swagger = Swagger(app)

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
TABLE_NAME = os.environ.get("DYNAMO_TABLE", "MyTable")

# AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)


def json_error(message, status=400):
    """Return a consistent JSON error format."""
    return jsonify({"success": False, "error": message}), status


def json_success(data=None, message=None):
    """Return a consistent JSON success format."""
    resp = {"success": True}
    if message:
        resp["message"] = message
    if data is not None:
        resp["data"] = data
    return jsonify(resp)


@app.errorhandler(500)
def handle_500(e):
    return json_error("Internal server error", 500)


@app.errorhandler(404)
def handle_404(e):
    return json_error("Endpoint not found", 404)


@app.route("/")
def root():
    return redirect("/apidocs")


# ---------------- S3 ----------------
@app.route("/s3/buckets", methods=["GET"])
def get_buckets():
    try:
        response = s3_client.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        return json_success(buckets)
    except ClientError as e:
        return json_error(str(e))


@app.route("/s3/buckets/<bucket_name>", methods=["POST"])
def create_bucket(bucket_name):
    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
        )
        return json_success(message=f"Bucket '{bucket_name}' created")
    except ClientError as e:
        return json_error(str(e))


@app.route("/s3/buckets/<bucket_name>", methods=["DELETE"])
def delete_bucket(bucket_name):
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        return json_success(message=f"Bucket '{bucket_name}' deleted")
    except ClientError as e:
        return json_error(str(e))


# ---------------- DynamoDB ----------------
@app.route("/dynamodb/items", methods=["GET"])
def get_dynamo_items():
    try:
        response = dynamodb_client.scan(TableName=TABLE_NAME)
        return json_success(response.get('Items', []))
    except ClientError as e:
        return json_error(str(e))


@app.route("/dynamodb/items", methods=["POST"])
def put_dynamo_item():
    try:
        item = request.get_json(force=True, silent=True)
        if not item:
            return json_error("Invalid or missing JSON body")
        if "id" not in item:
            return json_error("Item must contain 'id'")
        dynamodb_client.put_item(
            TableName=TABLE_NAME,
            Item={k: {'S': str(v)} for k, v in item.items()}
        )
        return json_success(message="Item saved to DynamoDB")
    except ClientError as e:
        return json_error(str(e))


@app.route("/dynamodb/items/<id>", methods=["DELETE"])
def delete_dynamo_item(id):
    try:
        dynamodb_client.delete_item(
            TableName=TABLE_NAME,
            Key={'id': {'S': id}}
        )
        return json_success(message=f"Item with id={id} deleted")
    except ClientError as e:
        return json_error(str(e))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
