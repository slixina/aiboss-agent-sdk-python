import time
import json
import logging
import random
import builtins
from typing import Dict
from .client import AibossClient
from .executor import Executor
from .executors.ping import PingExecutor
from .executors.scrape import ScrapeExecutor
from .sandbox import install_sandbox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Aiboss")

class AgentRunner:
    def __init__(self):
        self.client = AibossClient()
        self.executors: Dict[str, Executor] = {}
        self.error_count = 0
        
        # Harden Runtime
        # self._harden_runtime() # Disabled: causes issues with standard libraries (requests, platform, etc)
        install_sandbox()
        
        # Register default executors
        self._register_executor(PingExecutor())
        self._register_executor(ScrapeExecutor())

    def _harden_runtime(self):
        """Remove dangerous builtins to prevent RCE."""
        try:
            if hasattr(builtins, 'exec'):
                del builtins.exec
            if hasattr(builtins, 'eval'):
                del builtins.eval
            logger.info("Runtime hardened: exec/eval removed")
        except Exception as e:
            logger.warning(f"Failed to harden runtime: {e}")

    def _register_executor(self, executor: Executor):
        self.executors[executor.task_type] = executor
        logger.info(f"Registered capability: {executor.task_type}")

    def run(self):
        if not self.client.agent_id:
            logger.error("Agent not enrolled. Please run 'aiboss enroll' first.")
            return

        logger.info(f"Agent {self.client.agent_id} started. Capabilities: {list(self.executors.keys())}")
        
        while True:
            try:
                # Sync with server
                sync_response = self.client.sync(status="idle")
                
                # Reset error count on successful sync
                self.error_count = 0
                
                command = sync_response.get("command")
                
                if command == "sleep":
                    base_duration = sync_response.get("duration", 10)
                    # Add Jitter (random deviation +/- 10%)
                    jitter = random.uniform(-0.1, 0.1) * base_duration
                    sleep_time = max(1, base_duration + jitter)
                    # logger.debug(f"Sleeping for {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    
                elif command == "work":
                    task = sync_response.get("task")
                    if task:
                        self.process_task(task)
                    else:
                        logger.warning("Received work command but no task data")
                        
                elif command == "kill":
                    logger.warning("Received kill switch. Stopping agent.")
                    break
                    
                else:
                    logger.warning(f"Unknown command: {command}")
                    time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Agent stopping...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                
                # Exponential Backoff with Jitter
                self.error_count += 1
                backoff = min(60, (2 ** self.error_count)) # Cap at 60s
                jitter = random.uniform(0, 1) # Add up to 1s random delay
                sleep_time = backoff + jitter
                
                logger.info(f"Backing off for {sleep_time:.2f}s (Attempt {self.error_count})")
                time.sleep(sleep_time)

    def process_task(self, task: Dict):
        task_id = task.get("id")
        task_type = task.get("type")
        input_data = task.get("input") # Spec says 'input'

        if not task_id or not task_type:
            logger.error(f"Invalid task structure: {task}")
            return

        executor = self.executors.get(task_type)
        if not executor:
            logger.warning(f"No executor found for task type: {task_type}. Failing task gracefully.")
            # Submit failure so the task is not stuck in 'assigned' state until timeout
            try:
                self.client.submit_task(
                    task_id=task_id, 
                    result={"error": f"Agent capability mismatch: No executor for type '{task_type}'"}, 
                    duration_ms=0, 
                    success=False
                )
            except Exception as e:
                logger.error(f"Failed to submit error result: {e}")
            return

        logger.info(f"Executing task {task_id} ({task_type})")
        start_time = time.time()
        
        try:
            # Execute
            result = executor.execute(input_data)
            
            # Calculate duration
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Task {task_id} completed in {execution_time_ms}ms")
            
            # Submit result
            self.client.submit_task(task_id, result, execution_time_ms, success=True)
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Error executing task {task_id}: {e}")
            self.client.submit_task(task_id, {"error": str(e)}, execution_time_ms, success=False)
