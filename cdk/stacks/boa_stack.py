"""
Bank of Africa — CDK Stack
Complete infrastructure: DynamoDB + Lambda + API Gateway + S3 + Custom Resource for seeding.
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    CustomResource,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_iam as iam,
    custom_resources as cr,
)
from constructs import Construct
import os


class BankOfAfricaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ============================================================
        # DynamoDB Tables
        # ============================================================
        users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="boa_users",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        accounts_table = dynamodb.Table(
            self, "AccountsTable",
            table_name="boa_accounts",
            partition_key=dynamodb.Attribute(name="account_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        accounts_table.add_global_secondary_index(
            index_name="user_id-index",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
        )

        transactions_table = dynamodb.Table(
            self, "TransactionsTable",
            table_name="boa_transactions",
            partition_key=dynamodb.Attribute(name="account_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="txn_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ============================================================
        # S3 Buckets
        # ============================================================
        handbook_bucket = s3.Bucket(
            self, "HandbookBucket",
            bucket_name=f"boa-handbook-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=f"boa-frontend-{self.account}",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ============================================================
        # IAM Role for Lambda
        # ============================================================
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        # DynamoDB permissions
        users_table.grant_read_write_data(lambda_role)
        accounts_table.grant_read_write_data(lambda_role)
        transactions_table.grant_read_write_data(lambda_role)

        # Bedrock permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream",
                     "bedrock-agent-runtime:Retrieve", "bedrock-agentcore:InvokeAgentRuntime"],
            resources=["*"],
        ))

        # ============================================================
        # Seed Data Lambda (Custom Resource)
        # ============================================================
        seed_fn = lambda_.Function(
            self, "SeedFunction",
            function_name="boa-seed-data",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="seed_handler.handler",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "..", "lambda_code", "seed")),
            timeout=Duration.seconds(120),
            memory_size=512,
            role=lambda_role,
        )

        CustomResource(
            self, "SeedDataTrigger",
            service_token=seed_fn.function_arn,
            properties={"Version": "1.0"},
        )

        # ============================================================
        # API Handler Lambda
        # ============================================================
        api_fn = lambda_.Function(
            self, "ApiHandler",
            function_name="boa-api-handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="api_handler.handler",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "..", "lambda_code", "api")),
            timeout=Duration.seconds(120),
            memory_size=512,
            role=lambda_role,
            environment={
                "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-20250514",
                "REGION": self.region,
            },
        )

        # ============================================================
        # API Gateway
        # ============================================================
        api = apigw.RestApi(
            self, "BoaApi",
            rest_api_name="bank-of-africa-api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method(
            "POST",
            apigw.LambdaIntegration(api_fn),
        )

        # ============================================================
        # Agent Action Group Lambdas (for Bedrock Agent integration)
        # ============================================================
        agent_code_path = os.path.join(os.path.dirname(__file__), "..", "lambda_code", "agent_code")
        agent_functions = {}

        for fn_name in ["get_user_profile", "list_accounts", "get_balance",
                        "get_recent_transactions", "transfer_funds", "deposit_withdraw"]:
            fn = lambda_.Function(
                self, f"Fn-{fn_name}",
                function_name=f"boa-{fn_name.replace('_', '-')}",
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler=f"{fn_name}.handler",
                code=lambda_.Code.from_asset(agent_code_path),
                timeout=Duration.seconds(60),
                role=lambda_role,
            )
            fn.grant_invoke(iam.ServicePrincipal("bedrock.amazonaws.com"))
            agent_functions[fn_name] = fn

        # ============================================================
        # Outputs
        # ============================================================
        CfnOutput(self, "ApiEndpoint", value=api.url + "chat",
                  description="API endpoint for the chat frontend")
        CfnOutput(self, "FrontendURL", value=frontend_bucket.bucket_website_url,
                  description="Bank of Africa Chat App URL")
        CfnOutput(self, "FrontendBucket", value=frontend_bucket.bucket_name)
        CfnOutput(self, "HandbookBucket", value=handbook_bucket.bucket_name)

        for name, fn in agent_functions.items():
            CfnOutput(self, f"Arn-{name}", value=fn.function_arn)
