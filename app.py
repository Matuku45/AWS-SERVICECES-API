from flask import Flask, jsonify, redirect
import boto3
from botocore.exceptions import ClientError
from flasgger import Swagger
import json
from flask_cors import CORS

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
- **AWS Services Documentation / API Links:**
  - [EC2](https://docs.aws.amazon.com/ec2/)
  - [Lambda](https://docs.aws.amazon.com/lambda/)
  - [RDS](https://docs.aws.amazon.com/rds/)
  - [Redshift](https://docs.aws.amazon.com/redshift/)
  - [SQS](https://docs.aws.amazon.com/sqs/)
  - [SNS](https://docs.aws.amazon.com/sns/)
  - [CloudWatch](https://docs.aws.amazon.com/cloudwatch/)
  - [IAM](https://docs.aws.amazon.com/iam/)
  - [API Gateway](https://docs.aws.amazon.com/apigateway/)
  - [Step Functions](https://docs.aws.amazon.com/step-functions/)
  - [DynamoDB](https://docs.aws.amazon.com/amazondynamodb/)
  - [S3](https://docs.aws.amazon.com/s3/)
  - [Glue](https://docs.aws.amazon.com/glue/)
  - [Athena](https://docs.aws.amazon.com/athena/)
  - [Kinesis](https://docs.aws.amazon.com/kinesis/)
  - [Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
  - [EventBridge](https://docs.aws.amazon.com/eventbridge/)

You can interact with the endpoints below directly.
"""
}
swagger = Swagger(app)

# ---------------- AWS Clients ----------------
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# ---------------- ROOT ----------------
@app.route("/")
def root():
    return redirect("/apidocs")  # Redirect root to Swagger UI

# ---------------- S3 ENDPOINTS ----------------
@app.route("/s3/buckets", methods=["GET"])
def get_buckets():
    """
    S3 ENDPOINTS
    Get all S3 buckets
    ---
    responses:
      200:
        description: List of bucket names
        schema:
          type: array
          items:
            type: string
    """
    try:
        response = s3_client.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        return jsonify(buckets)
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/s3/buckets/<bucket_name>", methods=["POST"])
def create_bucket(bucket_name):
    """
    Create a new S3 bucket
    ---
    parameters:
      - name: bucket_name
        in: path
        type: string
        required: true
    responses:
      201:
        description: Bucket created
    """
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        return jsonify({"message": f"Bucket '{bucket_name}' created"}), 201
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/s3/buckets/<bucket_name>", methods=["DELETE"])
def delete_bucket(bucket_name):
    """
    Delete an S3 bucket
    ---
    parameters:
      - name: bucket_name
        in: path
        type: string
        required: true
    responses:
      200:
        description: Bucket deleted
    """
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        return jsonify({"message": f"Bucket '{bucket_name}' deleted"})
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

# ---------------- DynamoDB ENDPOINTS ----------------
@app.route("/dynamodb/items", methods=["GET"])
def get_dynamo_items():
    """
    DYNAMODB ENDPOINTS
    Get all DynamoDB items
    ---
    responses:
      200:
        description: List of DynamoDB items
    """
    try:
        table_name = "MyTable"
        response = dynamodb_client.scan(TableName=table_name)
        return jsonify(response.get('Items', []))
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/dynamodb/items", methods=["POST"])
def put_dynamo_item():
    """
    Add or update an item in DynamoDB
    ---
    parameters:
      - in: body
        name: item
        required: true
        schema:
          type: object
          example:
            id: "123"
            name: "Test Item"
    responses:
      200:
        description: Item saved
    """
    try:
        table_name = "MyTable"
        item = json.loads(request.data)
        if "id" not in item:
            return jsonify({"error": "Item must contain 'id'"}), 400
        dynamodb_client.put_item(
            TableName=table_name,
            Item={k: {'S': str(v)} for k, v in item.items()}
        )
        return jsonify({"message": "Item saved to DynamoDB"})
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/dynamodb/items/<id>", methods=["DELETE"])
def delete_dynamo_item(id):
    """
    Delete DynamoDB item by id
    ---
    parameters:
      - name: id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Item deleted
    """
    try:
        table_name = "MyTable"
        dynamodb_client.delete_item(
            TableName=table_name,
            Key={'id': {'S': id}}
        )
        return jsonify({"message": f"Item with id={id} deleted"})
    except ClientError as e:
        return jsonify({"error": str(e)}), 400

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
