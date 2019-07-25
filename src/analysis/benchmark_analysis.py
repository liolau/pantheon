import pandas as pd
import matplotlib.pyplot as plt
import os
from numpy.linalg import lstsq
import numpy as np
from arg_parser import parse_benchmark_analysis
import context

class BenchmarkAnalysis():
	def __init__(self, data_dir):
		self.data_dir = data_dir
		self.csv_path = os.path.join(self.data_dir, 'results.csv')
		self.data = pd.read_csv(self.csv_path)

	def run(self):
		solo = self.data.query('scheme_a==scheme_b')
		self.plot_loss(			'Lossrate vs Queue Size', 						'loss.png', 			solo)
		self.plot_variance(		'Relative Standard Deviation vs Queue Size', 	'rsd.png', 				solo)
		self.plot_fair(			'Jain Fairness vs RTT Unfairness', 				'fairness.png', 		solo)
		self.plot_fair_total(	'Jain Fairness (total) vs RTT Unfairness', 		'fairness_total.png',	solo)

		mixed = self.data.query('scheme_a!=scheme_b')
		if len(mixed)==0: return #in case of cubic
		self.plot_loss(			'Lossrate vs Queue Size (mixed flows)', 					'loss_mixed.png',			mixed)
		self.plot_variance(		'Relative Standard Deviation vs Queue Size (mixed flows)', 	'rsd_mixed.png',			mixed)
		self.plot_fair(			'Jain Fairness vs RTT Unfairness (mixed flows)', 			'fairness_mixed.png',		mixed)
		self.plot_fair_total(	'Jain Fairness (total) vs RTT Unfairness (mixed flows)', 	'fairness_total_mixed.png',	mixed)

	
	def plot_loss(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		filtered = data.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], v['loss'],label='%dms RTT'%(k[0] + k[1]))
		ax.set_xlabel('Queue Size (bytes)')
		ax.set_ylabel('Loss Rate (fraction)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))

	def plot_variance(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		filtered = data.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], sum([v['throughput_rsd%d'%i] for i in range(1, 7)]),label='%dms RTT'%(k[0] + k[1]))
		ax.set_xlabel('Queue Size (bytes)')
		ax.set_ylabel('Relative Standard Deviation of Throughput')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))
	
	def plot_fair(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		x_data = abs(data['rtprop_a'] - data['rtprop_b'])
		y_data = data['interval_fairness']
		plt.plot(x_data, y_data, '.', alpha=0.3, label='Experiment Results')
		A = np.vstack([x_data, np.ones(len(x_data))]).T
		m, c = lstsq(A, y_data, rcond=None)[0]
		plt.plot(x_data, m*x_data + c, 'r', label='Linear Regression')
		ax.set_xlabel('RTT Unfairness (ms)')
		ax.set_ylabel('Jain Fairness')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))

	def plot_fair_total(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		x_data = abs(data['rtprop_a'] - data['rtprop_b'])
		y_data = data['overall_fairness']
		plt.plot(x_data, y_data, '.', alpha=0.3, label='Experiment Results')
		A = np.vstack([x_data, np.ones(len(x_data))]).T
		m, c = lstsq(A, y_data, rcond=None)[0]
		plt.plot(x_data, m*x_data + c, 'r', label='Linear Regression')
		ax.set_xlabel('RTT Unfairness (ms)')
		ax.set_ylabel('Jain Fairness (total)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))


if __name__=='__main__':
	default_data_dir = os.path.join(context.src_dir, 'experiments/data')
	args = parse_benchmark_analysis(default_data_dir)
	BenchmarkAnalysis(args.data_dir).run()
