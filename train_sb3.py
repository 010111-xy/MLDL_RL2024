"""Sample script for training a control policy on the Hopper environment
   using stable-baselines3 (https://stable-baselines3.readthedocs.io/en/master/)

    Read the stable-baselines3 documentation and implement a training
    pipeline with an RL algorithm of your choice between PPO and SAC.
"""
import gym
import optuna

from env.custom_hopper import *
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy


def train_model(env_id):
    train_env = gym.make(env_id)
    print('State space:', train_env.observation_space)  # state-space
    print('Action space:', train_env.action_space)  # action-space
    print('Dynamics parameters:', train_env.get_parameters())  # masses of each link of the Hopper
    env = make_vec_env(env_id, n_envs=4)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=1000000)
    model.save("model_ppo")
    return model

def test_model(model, env_id):
    env = gym.make(env_id)
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=50)
    return mean_reward, std_reward

def main():
    source_env_id = 'CustomHopper-source-v0'
    target_env_id = 'CustomHopper-target-v0'

    source_model = train_model(source_env_id)
    source_on_source_mean, source_on_source_std = test_model(source_model, source_env_id)
    print(f"source -> source: {source_on_source_mean} -> {source_on_source_std}")
    source_on_target_mean, source_on_target_std = test_model(source_model, target_env_id)
    print(f"source -> target: {source_on_target_mean} -> {source_on_target_std}")

    target_model = train_model(target_env_id)
    target_on_target_mean, target_on_target_std = test_model(target_model, target_env_id)
    print(f"target -> target: {target_on_target_mean} -> {target_on_target_std}")


def test():
    model = PPO.load('model_ppo_source')
    env = gym.make('CustomHopper-target-v0')
    obs = env.reset()
    for _ in range(1000):
        action, _states = model.predict(obs, deterministic=True)
        obs, rewards, dones, info = env.step(action)
        env.render()
        if dones:
            obs = env.reset()

def tuning(trial):
    n_steps = trial.suggest_int('n_steps', 2048, 8192)
    gamma = trial.suggest_float('gamma', 0.9, 0.9999, log=True)
    learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True)
    ent_coef = trial.suggest_float('ent_coef', 0.0, 0.1)
    clip_range = trial.suggest_float('clip_range', 0.1, 0.4)
    n_epochs = trial.suggest_int('n_epochs', 1, 10)
    
    env = make_vec_env(lambda: gym.make('CustomHopper-source-v0'), n_envs=4)

    model = PPO(
        "MlpPolicy",
        env,
        n_steps=n_steps,
        gamma=gamma,
        learning_rate=learning_rate,
        ent_coef=ent_coef,
        clip_range=clip_range,
        n_epochs=n_epochs,
        verbose=0 # close log output
    )
    model.learn(total_timesteps=100000)
    mean_reward, _ = evaluate_policy(model, env, n_eval_episodes=10)

    return mean_reward

def get_best_params():
    study = optuna.create_study(direction='maximize')
    study.optimize(tuning, n_trials=100)
    print("Best params: ", study.best_params)


if __name__ == '__main__':
    #main()
    #test()
    get_best_params()