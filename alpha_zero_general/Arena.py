import numpy as np
from .pytorch_classification.utils import Bar, AverageMeter
import time


class Arena:
    """
    An Arena class where any 2 agents can be pit against each other.
    """

    def __init__(self, player, game, display=None):
        self.player = player
        self.game = game
        self.display = display

    def playGame(self, verbose=False):
        steps = []
        env_state, complexity = self.game.get_initial_state()
        it = 0
        next_state = self.game.getGameEnded(env_state)
        while next_state == 0:
            it += 1
            if verbose and self.display:
                self.display(env_state)
            steps.append(env_state.agent.problem)
            action = self.player(env_state)
            valids = self.game.getValidMoves(env_state)
            if valids[action] == 0:
                print(action)
                assert valids[action] > 0
            env_state = self.game.get_next_state(env_state, action)
            next_state = self.game.getGameEnded(env_state)

        # Display the final move
        if verbose:
            assert self.display
            self.display(env_state)
        # Final state
        steps.append(env_state.agent.problem)

        is_win = next_state == 1
        if verbose:
            if is_win:
                outcome_str = "Problem Solved"
            else:
                outcome_str = "Failed"
            print("\n\t\tResult: {}\n\n".format(outcome_str))
        return is_win, steps

    def playGames(self, num, verbose=False):
        """
        Evaluate a model by having it attempt to solve num problems.

        Returns:
            solved: number of problems solved
            failed: number of problems unsolved
            details: the problems attempted with each step as ascii math expressions
        """
        details = {"solved": [], "failed": []}
        eps_time = AverageMeter()
        bar = Bar("Problem.solve", max=num)
        end = time.time()
        eps = 0
        maxeps = int(num)

        solved = 0
        failed = 0
        for _ in range(num):
            is_win, steps = self.playGame(verbose=verbose)
            if is_win:
                solved += 1
                details["solved"].append(steps)
            else:
                failed += 1
                details["failed"].append(steps)

            # bookkeeping + plot progress
            eps += 1
            eps_time.update(time.time() - end)
            end = time.time()
            bar.suffix = "({eps}/{maxeps}) Eps Time: {et:.3f}s | Total: {total:} | ETA: {eta:}".format(
                eps=eps + 1,
                maxeps=maxeps,
                et=eps_time.avg,
                total=bar.elapsed_td,
                eta=bar.eta_td,
            )
            bar.next()
        bar.finish()

        return solved, failed, details
