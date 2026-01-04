import time
import logging
import requests

class GameController:
    def __init__(self, not_ready_limit=15):
        self.base = "http://localhost:8080"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.not_ready_limit = not_ready_limit
        self.not_ready_counter = 0

    def wait_for_server(self):
        self.logger.info("Waiting for server...")
        while True:
            try:
                r = requests.get(f"{self.base}/health", timeout=1)
                if r.status_code == 200:
                    self.logger.info("Server ready")
                    return
            except:
                pass
            time.sleep(1)

    def get_state(self):
        return requests.get(f"{self.base}/state").json()
    
    def reset_run(self):
        return requests.post(f"{self.base}/reset")

    def start_run(self, character, ascension_level):
        self.reset_run()
        time.sleep(3)
        self.logger.info(
            f"Sending cmd > start run : character={character} - ascension_level={ascension_level}"
        )
        requests.post(
            f"{self.base}/start",
            json={
                "character": character,
                "ascension_level": ascension_level
            }
        ).json()
        time.sleep(5)

    def send_command(self, cmd):
        self.logger.info(f"Sending cmd > {cmd}")

        try:
            r = requests.post(f"{self.base}/command", data=cmd, timeout=2)
            result = r.json()
        except Exception as e:
            self.logger.error(f"HTTP error while sending command: {e}")
            return False

        if not result.get("success", False):
            self.logger.error(
                f"Command ({cmd}) return error : {result.get('error', 'Unknown error')}"
            )
            return False

        return True

    def can_send_new_action(self, ready, cmds):
        if not cmds:
            self.logger.debug(f"No cmd available")
            self.not_ready_counter = 0
            return False

        if ready:
            self.not_ready_counter = 0
            return True

        self.not_ready_counter += 1
        if self.not_ready_counter == self.not_ready_limit:
            self.logger.warning(
                f"Game state still not ready (try : {self.not_ready_counter}/{self.not_ready_limit}). Forcing action send..."
            )

        return self.not_ready_counter >= self.not_ready_limit
