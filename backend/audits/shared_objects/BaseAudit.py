import threading
import queue

class BaseAudit:
    def __init__(self):
        # Initialized in subclass
        self.num_ballots = None

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
