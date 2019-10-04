from gym.envs.registration import register

from ...envs.polynomial_combine_in_place import MathyPolynomialCombineInPlaceEnv
from ...types import MathyEnvDifficulty, MathyEnvProblemArgs
from ..mathy_gym_env import MathyGymEnv

#
# Combine like terms without commuting
#


class GymPolynomialCombineInPlace(MathyGymEnv):
    def __init__(self, difficulty: MathyEnvDifficulty, **kwargs):
        super(GymPolynomialCombineInPlace, self).__init__(
            env_class=MathyPolynomialCombineInPlaceEnv,
            env_problem_args=MathyEnvProblemArgs(difficulty=difficulty),
            **kwargs
        )


class PolynomialCombineInPlaceEasy(GymPolynomialCombineInPlace):
    def __init__(self, **kwargs):
        super(PolynomialCombineInPlaceEasy, self).__init__(
            difficulty=MathyEnvDifficulty.easy, **kwargs
        )


class PolynomialCombineInPlaceNormal(GymPolynomialCombineInPlace):
    def __init__(self, **kwargs):
        super(PolynomialCombineInPlaceNormal, self).__init__(
            difficulty=MathyEnvDifficulty.normal, **kwargs
        )


class PolynomialCombineInPlaceHard(GymPolynomialCombineInPlace):
    def __init__(self, **kwargs):
        super(PolynomialCombineInPlaceHard, self).__init__(
            difficulty=MathyEnvDifficulty.hard, **kwargs
        )


register(
    id="mathy-poly-combine-easy-v0",
    entry_point="mathy.gym.envs:PolynomialCombineInPlaceEasy",
)
register(
    id="mathy-poly-combine-normal-v0",
    entry_point="mathy.gym.envs:PolynomialCombineInPlaceNormal",
)
register(
    id="mathy-poly-combine-hard-v0",
    entry_point="mathy.gym.envs:PolynomialCombineInPlaceHard",
)
