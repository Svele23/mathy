from typing import Optional, Type

import gym
import numpy as np
import plac
import tensorflow as tf
from gym import error, spaces, utils
from gym.envs.registration import register
from gym.utils import seeding

from ..agent.controller import MathModel
from ..features import (
    FEATURE_BWD_VECTORS,
    FEATURE_FWD_VECTORS,
    FEATURE_LAST_BWD_VECTORS,
    FEATURE_LAST_FWD_VECTORS,
    FEATURE_LAST_RULE,
    FEATURE_MOVE_MASK,
    FEATURE_NODE_COUNT,
    FEATURE_PROBLEM_TYPE,
)
from ..agent.training.mcts import MCTS
from ..core.expressions import MathTypeKeysMax
from ..mathy_env import MathyEnv, MathyEnvTimeStep
from ..mathy_env_state import MathyEnvState
from ..rules.rule import ExpressionChangeRule
from ..util import is_terminal_transition
from ..types import MathyEnvProblemArgs
from .binomial_distribution import MathyBinomialDistributionEnv
from .complex_term_simplification import MathyComplexTermSimplificationEnv
from .polynomial_simplification import MathyPolynomialSimplificationEnv


class MaskedDiscrete(spaces.Discrete):
    r"""A masked discrete space in :math:`\{ 0, 1, \\dots, n-1 \}`.
    Example::
        >>> MaskedDiscrete(3, mask=(1,1,0))
    """
    mask: np.array

    def __init__(self, n, mask):
        assert isinstance(mask, (tuple, list))
        assert len(mask) == n
        self.mask = np.array(mask)
        super(MaskedDiscrete, self).__init__(n)

    def sample(self):
        probability = self.mask / np.sum(self.mask)
        return self.np_random.choice(self.n, p=probability)


__mcts: Optional[MCTS] = None
__model: Optional[MathModel] = None


def mathy_load_model(gym_env: MathyGymEnv):
    global __model
    if __model is None:
        import os

        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "5"
        tf.compat.v1.logging.set_verbosity("CRITICAL")
        __model = MathModel(gym_env.mathy.action_size, "agents/ablated")
        __model.start()


def mathy_free_model():
    global __model
    if __model is not None:
        __model.stop()
        __model = None


def mcts_cleanup(gym_env: MathyGymEnv):
    global __mcts
    assert (
        __mcts is not None and __model is not None
    ), "MCTS search is already destroyed"
    mathy_free_model()
    __mcts = None


def mcts_start_problem(gym_env: MathyGymEnv):
    global __mcts, __model
    num_rollouts = 500
    epsilon = 0.0
    mathy_load_model(gym_env)
    assert __model is not None
    __mcts = MCTS(
        env=gym_env.mathy,
        model=__model,
        cpuct=0.0,
        num_mcts_sims=num_rollouts,
        epsilon=epsilon,
    )


def mcts_choose_action(gym_env: MathyGymEnv) -> int:
    global __mcts, __model
    assert (
        __mcts is not None and __model is not None
    ), "MCTS search must be initialized with: `mcts_start_problem`"
    assert (
        gym_env.mathy is not None and gym_env.state is not None
    ), "MathyGymEnv has invalid MathyEnv or MathyEnvState members"
    pi = __mcts.getActionProb(gym_env.state, temp=0.0)
    action = gym_env.action_space.np_random.choice(len(pi), p=pi)
    return action


def nn_choose_action(gym_env: MathyGymEnv) -> int:
    global __model
    assert __model is not None, "MathModel must be initialized with: `mathy_load_model`"
    assert (
        gym_env.mathy is not None and gym_env.state is not None
    ), "MathyGymEnv has invalid MathyEnv or MathyEnvState members"

    # leaf node
    pi_mask = gym_env.action_space.mask
    num_valids = len(pi_mask)
    pi, _ = __model.predict(gym_env.state, pi_mask)
    pi = pi.flatten()
    # Clip any predictions over batch-size padding tokens
    if len(pi) > num_valids:
        pi = pi[:num_valids]
    # mask out invalid moves from the prediction by multiplying by
    # the pi_mask which is filled with 0 or 1 based on if the action
    # at that index is valid for the current environment state.
    min_p = abs(np.min(pi))
    pi = np.array([p + min_p for p in pi])
    pi *= pi_mask
    # In case we masked out values, we renormalize to sum to 1.
    pi_sum = np.sum(pi)
    if pi_sum > 0:
        pi /= pi_sum
    action = np.random.choice(len(pi), p=pi)
    # action = np.argmax(pi)
    return action


def main():
    env = gym.make(
        "mathy-v0",
        env_class=MathyPolynomialSimplificationEnv,
        env_problem_args={"difficulty": 5},
    )
    episodes = 10
    print_every = 2
    solved = 0
    failed = 0
    agent = "model"
    agent = "random"
    agent = "mcts"
    for i_episode in range(episodes):

        if agent == "mcts":
            mcts_start_problem(env)
        elif agent == "model":
            mathy_load_model(env)
        print_problem = i_episode % print_every == 0
        observation = env.reset()
        if print_problem:
            env.render()
        for t in range(100):
            if agent == "mcts":
                action = mcts_choose_action(env)
            elif agent == "random":
                action = env.action_space.sample()
            elif agent == "model":
                action = nn_choose_action(env)
            observation, reward, done, info = env.step(action)
            if print_problem:
                env.render()
            if not done:
                continue
            # Episode is over
            if reward > 0.0:
                solved += 1
            else:
                failed += 1
            break
    print(
        f"Finished ({episodes}) with agent ({agent})\n"
        f"Solved ({solved}) problem and Failed ({failed})"
    )
    if agent == "mcts":
        mcts_cleanup(env)
    elif agent == "model":
        mathy_free_model()
    env.close()


if __name__ == "__main__":
    plac.call(main)