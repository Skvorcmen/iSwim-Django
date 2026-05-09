import sys

print("DEBUG: Test ASGI file is running!", file=sys.stderr)

async def application(scope, receive, send):
    print(f"DEBUG: Request received: {scope['type']}", file=sys.stderr)
    
    if scope['type'] == 'http':
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'text/plain')],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Hello from Render! Django not loaded yet.',
        })
