from flask import Flask, jsonify, redirect, request
import boto3
from botocore.exceptions import ClientError, NoRegionError
from flasgger import Swagger
import json
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ---------------- Swagger Configuration ----------------
app.config['SWAGGER'] = {
    'title': 'AWS & Gemini API Dashboard',
    'uiversion': 3,
    'description': """
# Interactive AWS & Gemini API Dashboard

Welcome! Use this dashboard to explore and interact with APIs.

## Links:

- **[S3 & DynamoDB API Endpoints](#s3-endpoints)**
- **[Gemini API](https://geminiapi-c01h.onrender.com/)**
- **[AWS Management Console](https://console.aws.amazon.com/)**
"""
}
swagger = Swagger(app)

# ---------------- AWS REGION & CLIENTS ----------------
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)

# ---------------- ROOT ----------------
@app.route("/")
def root():
    return redirect("/apidocs")  # Redirect root to Swagger UI

# ---------------- S3 ENDPOINTS ----------------
@app.route("/s3/buckets", methods=["GET"])
def get_buckets():
    """Get all S3 buckets"""
    try:
        response = s3_client.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        return jsonify(buckets)
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/s3/buckets/<bucket_name>", methods=["POST"])
def create_bucket(bucket_name):
    """Create a new S3 bucket"""
    try:
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': AWS_REGION})
        return jsonify({"message": f"Bucket '{bucket_name}' created"}), 201
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/s3/buckets/<bucket_name>", methods=["DELETE"])
def delete_bucket(bucket_name):
    """Delete an S3 bucket"""
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        return jsonify({"message": f"Bucket '{bucket_name}' deleted"})
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

# ---------------- DynamoDB ENDPOINTS ----------------
TABLE_NAME = os.environ.get("DYNAMO_TABLE", "MyTable")

@app.route("/dynamodb/items", methods=["GET"])
def get_dynamo_items():
    """Get all DynamoDB items"""
    try:
        response = dynamodb_client.scan(TableName=TABLE_NAME)
        return jsonify(response.get('Items', []))
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/dynamodb/items", methods=["POST"])
def put_dynamo_item():
    """Add or update an item in DynamoDB"""
    try:
        item = json.loads(request.data)
        if "id" not in item:
            return jsonify({"error": "Item must contain 'id'"}), 400
        dynamodb_client.put_item(
            TableName=TABLE_NAME,
            Item={k: {'S': str(v)} for k, v in item.items()}
        )
        return jsonify({"message": "Item saved to DynamoDB"})
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/dynamodb/items/<id>", methods=["DELETE"])
def delete_dynamo_item(id):
    """Delete DynamoDB item by id"""
    try:
        dynamodb_client.delete_item(
            TableName=TABLE_NAME,
            Key={'id': {'S': id}}
        )
        return jsonify({"message": f"Item with id={id} deleted"})
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
