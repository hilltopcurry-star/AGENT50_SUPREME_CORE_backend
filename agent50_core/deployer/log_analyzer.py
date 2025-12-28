class LogAnalyzer:
    def analyze(self, log_text):
        """
        Logs padh kar batata hai ke masla kya hai.
        """
        report = {
            "is_error": False,
            "error_type": None,
            "details": ""
        }

        if "ModuleNotFoundError" in log_text:
            report["is_error"] = True
            report["error_type"] = "MISSING_DEPENDENCY"
            # Extract module name (e.g., No module named 'flask')
            import re
            match = re.search(r"No module named '(\w+)'", log_text)
            if match:
                report["details"] = match.group(1)

        elif "Internal Server Error" in log_text:
            report["is_error"] = True
            report["error_type"] = "CRASH_ON_START"

        elif "gunicorn: command not found" in log_text:
            report["is_error"] = True
            report["error_type"] = "PROCFILE_ISSUE"

        return report