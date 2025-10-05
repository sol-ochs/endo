from app.main import handler

def lambda_handler(event, context):
    return handler(event, context)