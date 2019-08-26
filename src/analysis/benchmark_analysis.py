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
		scheme_a = solo['scheme_a'].values[0]
		scheme_b = solo['scheme_b'].values[0]
		scheme_str = "\n6x%s competing"%(scheme_a)
		self.plot_loss(			'Lossrate vs Queue Capacity' + scheme_str,							'loss.pdf', 			solo)
		self.plot_variance(		'Relative Standard Deviation vs Queue Capacity' + scheme_str,		'rsd.pdf', 				solo)
		self.plot_fair(			'Jain Fairness vs RTT Unfairness' + scheme_str, 					'fairness.pdf', 		solo)
		self.plot_fair_total(	'Jain Fairness (total) vs RTT Unfairness' + scheme_str, 			'fairness_total.pdf',	solo)
		self.plot_time_to_convergence('Convergence Time vs Fairness after Convergence' + scheme_str,'convergence.pdf',		solo)
		self.plot_queueing_delay('Queuing Delay vs Queue Capacity' + scheme_str,					'delay.pdf',			solo)
		self.plot_throughput(	'Throughput vs Queue Capacity' + scheme_str,						'throughput.pdf',		solo)

		mixed = self.data.query('scheme_a!=scheme_b')
		if len(mixed)==0: return #in case of cubic
		scheme_a = mixed['scheme_a'].values[0]
		scheme_b = mixed['scheme_b'].values[0]
		scheme_str = "\n3x%s 3x%s competing"%(scheme_a, scheme_b)
		self.plot_loss(			'Lossrate vs Queue Capacity' + scheme_str,							'loss_mixed.pdf',			mixed)
		self.plot_variance(		'Relative Standard Deviation vs Queue Capacity' + scheme_str,	 	'rsd_mixed.pdf',			mixed)
		self.plot_fair(			'Jain Fairness vs RTT Unfairness' + scheme_str, 					'fairness_mixed.pdf',		mixed)
		self.plot_fair_total(	'Jain Fairness (total) vs RTT Unfairness' + scheme_str, 			'fairness_total_mixed.pdf',	mixed)
		self.plot_time_to_convergence('Convergence Time vs Fairness after Convergence' + scheme_str,'convergence_mixed.pdf',	mixed)
		self.plot_queueing_delay('Queuing Delay vs Queue Capacity' + scheme_str,			 		'delay_mixed.pdf',			mixed)
		self.plot_throughput_mixed(	'Throughput vs Queue Capacity' + scheme_str,					'throughput_mixed.pdf',		mixed)
	
	def plot_loss(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		filtered = data.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], v['loss'],label='%dms RTT'%(k[0] + k[1]))
		ax.set_xlabel('Queue Capacity (bytes)')
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
			plt.semilogx(v['q_size'], sum([v['throughput_rsd%d'%i] for i in range(1, 7)])/6.0,label='%dms RTT'%(k[0] + k[1]))
		ax.set_xlabel('Queue Capacity (bytes)')
		ax.set_ylabel('Relative Standard Deviation of Throughput')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))
	
	def plot_fair(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		x_data = abs(data['rtprop_a'] - data['rtprop_b'])
		y_data = data['interval_fairness']
		plt.plot(x_data, y_data, '.', alpha=0.3, label='Experiment Results')
		m, c = self.linear_regression(x_data, y_data)
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
		m, c = self.linear_regression(x_data, y_data)
		plt.plot(x_data, m*x_data + c, 'r', label='Linear Regression')
		ax.set_xlabel('RTT Unfairness (ms)')
		ax.set_ylabel('Jain Fairness (total)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))
		return np.mean(y_data), m

	def plot_time_to_convergence(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		x_data = data['overall_fairness']
		y_data = data['time_to_max_fairness']
		plt.plot(x_data, y_data, '.', alpha=0.3, label='Experiment Results')
		m, c = self.linear_regression(x_data, y_data)
		plt.plot(x_data, m*x_data + c, 'r', label='Linear Regression')
		ax.set_xlabel('Total Jain Fairness')
		ax.set_ylabel('Time to max Fairness (s)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))

	def plot_queueing_delay(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		filtered = data.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], v['mean_bottleneck_delay'] - (v['bottleneck_rtprop']/2),label='%dms oneway propagation delay'%((k[0] + k[1])/2))
			q_sizes = v['q_size']
			tputs = v['bottleneck_tput']
		plt.semilogx(q_sizes, q_sizes/(tputs/8.0*1000), label='full queue', color='grey')
		ax.set_xlabel('Queue Capacity (bytes)')
		ax.set_ylabel('Queuing Delay (ms)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))

	def plot_throughput_mixed(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		filtered = data.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		colors = list("rgbcym")
		color_id = 0
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], v['scheme_a_tput'],label='%s %dms RTT'%(v['scheme_a'].values[0], k[0] + k[1]), color=colors[color_id])
			plt.semilogx(v['q_size'], v['scheme_b_tput'], '--', label='%s %dms RTT'%(v['scheme_b'].values[0], k[0] + k[1]), color=colors[color_id])
			color_id += 1
			q_sizes = v['q_size']
			tputs = v['bottleneck_tput']
		plt.semilogx(q_sizes, tputs/2.0, label='Fair share', color='black')
		ax.set_xlabel('Queue Capacity (bytes)')
		ax.set_ylabel('Throughput (Mbit)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))

	def plot_throughput(self, title, filename, data):
		fig, ax = plt.subplots()
		fig.suptitle(title)
		filtered = data.query('rtprop_a==rtprop_b')
		grouped = filtered.groupby(['rtprop_a', 'bottleneck_rtprop'])
		colors = list("rgbcym")
		color_id = 0
		for k, v in dict(list(grouped)).items():
			v = v.sort_values('q_size')
			plt.semilogx(v['q_size'], v['throughput'],label='%s %dms RTT'%(v['scheme_a'].values[0], k[0] + k[1]), color=colors[color_id])
			color_id += 1
			q_sizes = v['q_size']
			tputs = v['bottleneck_tput']
		plt.semilogx(q_sizes, tputs, label='Bottleneck capacity', color='black')
		ax.set_xlabel('Queue Capacity (bytes)')
		ax.set_ylabel('Throughput (Mbit)')
		plt.legend()
		plt.savefig(os.path.join(self.data_dir, filename))

	def linear_regression(self, x_data, y_data):
		A = np.vstack([x_data, np.ones(len(x_data))]).T
		m, c = lstsq(A, y_data, rcond=None)[0]
		return m, c


if __name__=='__main__':
	default_data_dir = os.path.join(context.src_dir, 'experiments/data')
	args = parse_benchmark_analysis(default_data_dir)
	BenchmarkAnalysis(args.data_dir).run()
