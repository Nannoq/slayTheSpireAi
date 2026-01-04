from stable_baselines3.common.callbacks import BaseCallback

class StopTrainingCallback(BaseCallback):
    def __init__(self, env, verbose=0):
        super().__init__(verbose)
        self.env = env

    def _on_step(self) -> bool:
        if self.env.stop_training:
            self.env.stop_training = False
            return False
        return True
