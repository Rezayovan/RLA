import random
import math
import numpy as np
from .shared_objects.BaseAudit import BaseAudit
from .shared_objects.Candidates import Candidates
from .shared_objects.Hypotheses import Hypotheses

class Cast(BaseAudit):

	def __init__(self, initial_cvr_data, num_candidates, num_winners, num_stages, batch_size, num_batches, risk_tolerance, threshold, random_seed):
		super().__init__()
		self.num_candidates = num_candidates
		assert 1. <= num_winners <= len(num_candidates)
		self.num_winners = num_winners
		self.num_stages = num_stages
		self.batch_size = batch_size
		self.num_batches = num_batches
		self.num_unaudited = num_batches
		self.threshold = threshold
		self.random_seed = random_seed
		print(num_batches)
		self.unaudited = np.arange(num_batches)
		self.alpha = self.calc_alpha_s(risk_tolerance)
		self.reported_batch_info, self.audited_batch_info, self.winners, self.losers = self.init_info()
		self.cvr_batches = initial_cvr_data


	def calc_alpha_s(self, risk_tolerance):
		diff = 1 - risk_tolerance
		diff_s = diff ** (1/float(self.num_stages))
		alpha_s = 1 - diff_s
		return alpha_s

	def init_info(self):
		total_votes = np.zeros(self.num_candidates)
		reported_batch_info = []
		get_batch_generator = self.get_batch_first()
		for _ in self.cvr_batches:
			batch_info = next(get_batch_generator)
			reported_batch_info.append(batch_info)
			for idx, num_votes in enumerate(batch_info):
				total_votes[idx] = total_votes[idx] + num_votes

		losers = np.argsort(total_votes)[:(num_candidates - num_winners)]
		winners = np.argsort(total_votes)[(num_candidates - num_winners):]
		reported_batch_info = np.asarray(reported_batch_info)
		audited_batch_info = np.zeros(reported_batch_info.shape)

		return reported_batch_info, audited_batch_info, winners, losers

	def get_batch_info(self):
		'''
		Get batch info
		'''
		return self.get_votes()

	def get_batch_first(self):
		'''
		Get batch info for beginning of audit.
		'''
		for batch in self.cvr_batches:
			yield batch

	def calc_adj_margin(self, winner, loser):
		reported_margin = 0
		audited_margin = 0
		for num in self.unaudited:
			reported_margin = reported_margin + self.reported_batch_info[num][winner] - self.reported_batch_info[num][loser]

		for batches in self.audited_batch_info:
			audited_margin = audited_margin + batches[winner] - batches[loser]

		return reported_margin + audited_margin

	'''
	Calculates the maximun overstatement for each batch of ballots
	Batches that have been audited will have a max overstatmennt of 0
	'''
	def calc_u_ps(self):
		u_ps = np.zeros(self.num_batches)

		# Matrix containing all the adj margins between any winner and any loser
		adj_margins = np.zeros([len(self.winners), len(self.losers)])

		for idw, winner in enumerate(self.winners):
			for idl, loser in enumerate(self.losers):
				adj_margins[idw][idl] = self.calc_adj_margin(winner, loser)

		print("adj margins %s" % adj_margins)

		for batch_num in self.unaudited:
			max_u_p = []
			for idw, winner in enumerate(self.winners):
				for idl, loser in enumerate(self.losers):
					u_p = (self.reported_batch_info[batch_num][winner] - self.reported_batch_info[batch_num][loser] + self.batch_size) / adj_margins[idw][idl]
					max_u_p.append(u_p)
			u_ps[batch_num] = np.amax(max_u_p)
		print("u_ups %s" % u_ps)
		return u_ps


	'''
	Calculates the threshold for how many batches need to be audited for this stage
	'''
	def calc_T(self):
		u_ps = self.calc_u_ps()
		t_ps = []
		squigglie_u_ps = []
		for u_p in u_ps:
			if(u_p < threshold):
				t_ps.append(u_p)
				squigglie_u_ps.append(0.0)
			else:
				t_ps.append(threshold)
				squigglie_u_ps.append(u_p - threshold)
		print("tps: %s" % t_ps)
		T = sum(t_ps)
		squigglie_u_ps = np.asarray(squigglie_u_ps)
		return T, squigglie_u_ps

	'''
	Returns the number of squigle u_ps needed to add up to 1-T
	'''
	def calc_n(self, T, squigglie_u_ps):
		sorted_squigglie_u_ps = np.argsort(squigglie_u_ps)
		sorted_squigglie_u_ps = sorted_squigglie_u_ps[::-1]
		sum = 0
		count = 0
		while sum < (1 - T):
			sum = sum + sorted_squigglie_u_ps[count]
			count = count + 1

		base = (self.num_unaudited - count) / self.num_unaudited
		n = math.log(base, self.alpha)
		n = math.ceil(n)
		return n

	def calc_t_s(self, batches_to_audit):
		adj_margins = np.zeros([len(self.winners), len(self.losers)])

		for idw, winner in enumerate(self.winners):
			for idl, loser in enumerate(self.losers):
				adj_margins[idw][idl] = self.calc_adj_margin(winner, loser)

		e_wlp = []
		for batch_num in batches_to_audit:
			for w in self.winners:
				for l in self.losers:
					reported = self.reported_batch_info[batch_num][w] - self.reported_batch_info[batch_num][l]
					audited = self.audited_batch_info[batch_num][w] - self.audited_batch_info[batch_num][l]
					e_wlp.append((reported - audited)/ adj_margins)
		return np.amin(e_wlp)

	def run_audit(self):
		random.seed(a = self.random_seed)

		for i in range(self.num_stages):
			T, squigglie_u_ps = self.calc_T()
			n = self.calc_n(T, squigglie_u_ps)
			batches_to_audit = random.sample(list(self.unaudited), n)
			for batch_num in batches_to_audit:
				np.delete(self.unaudited, batch_num)
				self.audited_batch_info[batch_num] = self.get_batch_info()
			t_s = self.calc_t_s(batches_to_audit)
			if t_s < self.threshold:
				print('Audit complete')
				return

		print('Audit failed full hand recount needed')
		return

# num_candidates, num_winners, num_stages, batch_size
# num_batches, risk_tolerance, threshold, random_seed

if __name__ == "__main__":
	num_candidates, num_winners, num_stages, batch_size = (2, 1, 2, 10)
	num_batches, risk_tolerance, threshold, random_seed = (20, .05, .01, 1234567)
	params = [num_candidates, num_winners, num_stages, batch_size,
	num_batches, risk_tolerance, threshold, random_seed]
	cast = Cast(*params)
	cast.run_audit()
