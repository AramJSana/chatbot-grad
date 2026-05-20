import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

current_workspace = f'https://{spark.conf.get("spark.databricks.workspaceUrl")}'

DATABRICKS_TOKEN = dbutils.secrets.get(scope="dbrickstoken", key="dbrickstoken")
DATABRICKS_BASE_URL = f'{current_workspace}/serving-endpoints'

