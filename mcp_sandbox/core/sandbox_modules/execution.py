from typing import Dict, Any
import time

class SandboxExecutionMixin:
    def execute_python_code(self, sandbox_id: str, code: str) -> Dict[str, Any]:
        error = self.verify_sandbox_exists(sandbox_id)
        if error:
            return error
        start_ts = int(time.time())
        logger = self._get_logger()
        logger.info("Executing code:")
        logger.info("=" * 50)
        logger.info(code)
        logger.info("=" * 50)
        logger.info(f"Running code in sandbox {sandbox_id}")
        try:
            with self._get_running_sandbox(sandbox_id) as sandbox:
                temp_code_file = "/tmp/code_to_run.py"
                write_code_cmd = f"cat > {temp_code_file} << 'EOL'\n{code}\nEOL"
                write_result = sandbox.exec_run(
                    cmd=["sh", "-c", write_code_cmd],
                    workdir="/app/results",
                    privileged=False
                )
                if write_result.exit_code != 0:
                    logger.error(f"Failed to write code to sandbox: {write_result.output.decode('utf-8')}")
                    return {
                        "error": "Failed to prepare code execution",
                        "stdout": "",
                        "stderr": write_result.output.decode('utf-8'),
                        "exit_code": write_result.exit_code,
                        "files": [],
                        "file_links": []
                    }
                exec_result = sandbox.exec_run(
                    cmd=["python", temp_code_file],
                    workdir="/app/results",
                    stdout=True,
                    stderr=True,
                    demux=True,
                    privileged=False
                )
                exit_code = exec_result.exit_code
                stdout_bytes, stderr_bytes = exec_result.output
                stdout = stdout_bytes.decode('utf-8') if stdout_bytes else ""
                stderr = stderr_bytes.decode('utf-8') if stderr_bytes else ""
                sandbox.exec_run(cmd=["rm", "-f", temp_code_file], privileged=False)
                all_files = self.list_files_in_sandbox(sandbox_id, with_stat=True)
                new_files = [f for f, ctime in all_files if ctime >= start_ts]
                file_links = [self.get_file_link(sandbox_id, f) for f in new_files]
                logger.info("Execution results:")
                logger.info(f"Exit code: {exit_code}")
                if stdout:
                    logger.info("Stdout:")
                    logger.info(stdout)
                if stderr:
                    logger.warning("Stderr:")
                    logger.warning(stderr)
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "files": new_files,
                    "file_links": file_links
                }
        except ValueError as e:
            return {
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "files": [],
                "file_links": []
            }
        except Exception as e:
            logger.error(f"Failed to run code in sandbox {sandbox_id}: {e}", exc_info=True)
            error_message = str(e)
            if hasattr(e, 'stderr') and e.stderr:
                stderr = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                error_message = f"{error_message}\nDetails: {stderr}"
            return {
                "error": error_message,
                "stdout": "",
                "stderr": error_message,
                "exit_code": 1,
                "files": [],
                "file_links": []
            }

    def _get_logger(self):
        from mcp_sandbox.utils.config import logger
        return logger
