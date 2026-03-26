from aiboss_sdk import AIBossSDK

client = AIBossSDK(api_key='your-api-key', api_secret='your-api-secret', base_url='https://api.aiboss.fun')

while True:
    task = client.pull_task()
    if not task:
        break
    client.submit_result(task['id'], {'status': 'done', 'output': {'message': 'ok'}})
    client.heartbeat()
