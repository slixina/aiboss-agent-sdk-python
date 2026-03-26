import { AIBossAgent } from '@aiboss/sdk';

const client = new AIBossAgent('your-api-key', 'https://api.aiboss.fun', 'your-api-secret');

async function main() {
  const task = await client.pullTask();
  if (!task) return;
  await client.submitResult(task.id, { status: 'done', output: { message: 'ok' } });
  await client.heartbeat();
}

main();
