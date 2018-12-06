import threading
import queue

from Candidates import Candidates

class BaseAudit:
    def __init__(self):
        # Initialized in subclass
        self.num_ballots = None
        self.num_candidates = None
        self.votes_array = None
        self.num_winners = None

        # global vars
        self._VOTES_BUFFER = queue.Queue()
        self._LOCK = threading.Lock()
        self._CV = threading.Condition(self._LOCK)
        self.random_gen = None

        # status vars
        self.IS_DONE = False
        self.IS_DONE_MESSAGE = ""
        self.IS_DONE_FLAG = ""

    def append_votes_buffer(self, vote):
        cv = self._CV
        buffer = self._VOTES_BUFFER

        cv.acquire()
        buffer.put(vote)
        cv.notify()
        cv.release()

    def get_votes(self):
        cv = self._CV
        buffer = self._VOTES_BUFFER

        cv.acquire()
        print("getting vote")
        while buffer.empty():
            print("wait condition")
            cv.wait()
        votes = buffer.get()
        cv.release()

        return votes

    def get_sequence_number(self):
        """Returns random sequence number to draw ballot from."""
        num_ballots = self.num_ballots
        ballot_to_draw = self.random_gen.randint(1, num_ballots)
        return ballot_to_draw

    def arrange_candidates(self):
        """
        From `votes_array`, we can find the winners as the `num_winners` candidates
        (indices) with the most votes. The losers are the rest of the candidates.
        """
        sorted_candidates = sorted(enumerate(self.votes_array), \
                key=lambda t: t[1], reverse=True)

        # Indices of winners in the votes array
        winners = set(t[0] for t in sorted_candidates[:self.num_winners])
        # Indices of losers in the votes array
        losers = set(t[0] for t in sorted_candidates[self.num_winners:])

        return Candidates(winners, losers)
