import json
from lambda_handler import handler

def test_handler_root_endpoint():
    # GIVEN
    event = {
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/"
            }
        }
    }
    
    # WHEN
    response = handler(event, None)
    
    # THEN
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "message" in body 