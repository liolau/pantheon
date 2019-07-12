import pandas as pd
import matplotlib.pyplot as plt
class BenchmarkAnalysis():
    def __init__(self, csv_path):
        self.data = pd.read_csv(csv_path)
        
    def run(self):
        fig, ax = plt.subplots()
        fig.suptitle('bbr lossrate to qsize')
        filtered = self.data[self.data['scheme_b']=='bbr']
        #filtered = filtered[filtered['rtt_a']==50]
        #filtered = filtered[filtered['rtt_b']==50]
        grouped = filtered.groupby(['scheme_a', 'scheme_b', 'rtt_a', 'rtt_b'])
        for k, v in dict(list(grouped)).items():
            v = v.sort_values('q_size')
            plt.semilogx(v['q_size'], v['time_to_max_fairness'])
        plt.show()


if __name__=='__main__':
    BenchmarkAnalysis('../experiments/results.csv').run()
