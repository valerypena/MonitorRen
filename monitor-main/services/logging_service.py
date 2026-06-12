import logging
import os
import pymysql
from typing import Dict, Any, Optional

class LoggingService:
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config
        self.logger = logging.getLogger("ren_monitor")
        self.logger.setLevel(logging.DEBUG)
        
        # Ensure log dir exists
        os.makedirs("logs", exist_ok=True)
        log_file = os.path.join("logs", "app.log")
        
        # File handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def log(self, level: str, message: str, topic: str = "system") -> None:
        """
        Log a message locally and in the database if level is WARNING/ERROR.
        """
        lvl = level.upper()
        if lvl == "DEBUG":
            self.logger.debug(f"[{topic}] {message}")
        elif lvl == "INFO":
            self.logger.info(f"[{topic}] {message}")
        elif lvl == "WARNING":
            self.logger.warning(f"[{topic}] {message}")
            self._write_to_db(topic, message, "warning")
        elif lvl == "ERROR" or lvl == "CRITICAL":
            self.logger.error(f"[{topic}] {message}")
            self._write_to_db(topic, message, "critical")

    def _write_to_db(self, topic: str, message: str, severity: str) -> None:
        if not self.db_config:
            return
        
        # Open DB connection and insert log
        try:
            conn = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                timeout=2
            )
            with conn.cursor() as cursor:
                sql = "INSERT INTO network_logs (topic, message, severity) VALUES (%s, %s, %s)"
                cursor.execute(sql, (topic, message, severity))
            conn.commit()
            conn.close()
        except Exception as e:
            # Silently log locally to avoid infinite loops if DB fails
            self.logger.debug(f"[logging_service] Failed to sync log to database: {e}")
