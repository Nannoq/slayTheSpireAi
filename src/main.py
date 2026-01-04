import os
import logging
import random
import subprocess
import time
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy

from logging_config import setup_logging
from action_manager import ActionManager
from game_controller import GameController
from game_env import GameEnv
from stop_training_callback import StopTrainingCallback

def mask_fn(env):
    return env.get_action_mask()

PERSOS = ["IRONCLAD", "THE_SILENT"]
random.shuffle(PERSOS)
MODEL_PATH = "ressources/models/sts_ppo"

setup_logging()
logger = logging.getLogger("Main")
game_process = subprocess.Popen(
    ["java", "-jar", ".\\ModTheSpire.jar", "--skip-launcher"],
    cwd="ressources/jar",
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL)
time.sleep(15)
action_manager = ActionManager(filepath="ressources/actions/all_actions.json")
game_controller = GameController()
models = {}
envs = {}
callbacks = {}

for perso in PERSOS:
    envs[perso] = GameEnv(action_manager, game_controller)
    callbacks[perso] = StopTrainingCallback(envs[perso], verbose=1)
    envs[perso] = ActionMasker(envs[perso], mask_fn)
    if os.path.exists(f"{MODEL_PATH}_{perso}.zip"):
        logger.info("Loading existing model...")
        models[perso] = MaskablePPO.load(f"{MODEL_PATH}_{perso}", env=envs[perso])
    else:
        logger.info("Creating new model...")
        models[perso] = MaskablePPO(
        MaskableActorCriticPolicy,
        envs[perso],
        verbose=1,
        n_steps=256,
        batch_size=64,
        learning_rate=3e-4,
    )

current_perso = None
current_model = None

try:
    while True:
        for perso, model in models.items():
            current_perso = perso
            current_model = model
            game_controller.start_run(perso, 0)
            logger.info(f"Training model for {perso}...")
            model.learn(total_timesteps=100_000_000, callback=callbacks[perso], reset_num_timesteps=False)
            model.save(f"{MODEL_PATH}_{perso}")
            action_manager.save()
except KeyboardInterrupt:
    logger.info("Training stopped by user")
    if current_model is not None and current_perso is not None:
        logger.info(f"Saving model for {current_perso}")
        current_model.save(f"{MODEL_PATH}_{current_perso}")
    action_manager.save()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    if current_model is not None and current_perso is not None:
        logger.info(f"Saving model for {current_perso}")
        current_model.save(f"{MODEL_PATH}_{current_perso}")
    action_manager.save()
    raise
