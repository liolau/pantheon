import pandas as pd
import matplotlib.pyplot as plt
import os
from numpy.linalg import lstsq
import numpy as np
class BenchmarkAnalysis():
	def __init__(self, data_dir):
		self.data_dir = data_dir
		self.csv_path = os.path.join(self.data_dir, 'results.csv')
		self.data = pd.read_csv(self.csv_path)

	def run(self):
		self.plot_loss()
		self.plot_fair()
		self.plot_fair_total()
		self.plot_variance()

	
	def plot_loss(self):
		fig, ax = plt.subplots()
		fig.suptitle('Lossrate vs Queue Size')
		filtered = self.data.query('scheme_a==scheme_b')
		filtered = filtered.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], v['loss'],label='%dms RTT'%(k[0] + k[1]))
		ax.set_xlabel('Queue Size (bytes)')
		ax.set_ylabel('Loss Rate (fraction)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, 'loss.png'))

	def plot_variance(self):
		fig, ax = plt.subplots()
		fig.suptitle('Relative Standard Deviation vs Queue Size')
		filtered = self.data.query('scheme_a==scheme_b')
		filtered = filtered.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], sum([v['throughput_rsd%d'%i] for i in range(1, 7)]),label='%dms RTT'%(k[0] + k[1]))
		ax.set_xlabel('Queue Size (bytes)')
		ax.set_ylabel('Relative Standard Deviation of Throughput')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, 'rsd.png'))
	
	def plot_fair(self):
		fig, ax = plt.subplots()
		fig.suptitle('Jain Fairness vs RTT Unfairness')
		filtered = self.data.query('scheme_a==scheme_b')
		x_data = abs(filtered['rtprop_a'] - filtered['rtprop_b'])
		y_data = filtered['interval_fairness']
		plt.plot(x_data, y_data, '.', alpha=0.3, label='Experiment Results')
		A = np.vstack([x_data, np.ones(len(x_data))]).T
		m, c = lstsq(A, y_data, rcond=None)[0]
		plt.plot(x_data, m*x_data + c, 'r', label='Linear Regression')
		ax.set_xlabel('RTT Unfairness (ms)')
		ax.set_ylabel('Jain Fairness')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, 'fairness.png'))

	def plot_fair_total(self):
		fig, ax = plt.subplots()
		fig.suptitle('Jain Fairness (total) vs RTT Unfairness')
		filtered = self.data.query('scheme_a==scheme_b')
		x_data = abs(filtered['rtprop_a'] - filtered['rtprop_b'])
		y_data = filtered['overall_fairness']
		plt.plot(x_data, y_data, '.', alpha=0.3, label='Experiment Results')
		A = np.vstack([x_data, np.ones(len(x_data))]).T
		m, c = lstsq(A, y_data, rcond=None)[0]
		plt.plot(x_data, m*x_data + c, 'r', label='Linear Regression')
		ax.set_xlabel('RTT Unfairness (ms)')
		ax.set_ylabel('Jain Fairness (total)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, 'fairness_total.png'))


if __name__=='__main__':
	BenchmarkAnalysis('../experiments/data').run()
