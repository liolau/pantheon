from experiment import Experiment
import os
from helpers.subprocess_wrappers import check_output
from helpers import utils
import context
from router import Router
from trace import Trace
import math
import itertools
import traceback
import pandas as pd

class Benchmark():
    def __init__(self, ramdisk = True, tmp_dir='./tmp_data', data_dir = './data', scheme='cubic', verbose=False):
	check_output('python setup.py', shell=True) #loads all schemes after reboot
        self.tmp_dir = tmp_dir
        self.data_dir = data_dir
        if ramdisk:
	    utils.make_sure_dir_exists(self.tmp_dir)
            res = check_output('df -T %s'%self.tmp_dir, shell=True)
            if not 'tmpfs' in res: check_output('sudo mount -t tmpfs -o size=300M tmpfs %s' % self.tmp_dir, shell=True)
            else: print('%s is already a ramdisk' %self.tmp_dir)
        self.scheme = scheme
        self.verbose = verbose
        self.build_experiments()
        
    def build_experiments(self):
        runs = 1
        runtime = 90
        routers = 11
        delays = [0, 25, 50, 75, 100]
        self.solo =  self.build_rtt_experiments(self.scheme, self.scheme, delays, runs, runtime, routers)
        self.mixed = []
        #self.mixed = self.build_rtt_experiments(self.scheme, 'cubic'    , delays, runs, runtime, routers)
        print('Expected runtime: %d seconds'%(runs*runtime*routers*len(delays)**2*2))

    def build_rtt_experiments(self, scheme_a, scheme_b, delays, runs, runtime, routers):
        rtt_unfairness_routers = [Router(delay=d) for d in delays]
        bottleneck_routers = self.build_router_range(18, 25, routers, range_factor=10)
        
        res = []
        for rtt_a, rtt_b in itertools.product(rtt_unfairness_routers, rtt_unfairness_routers):
            #build an experiment for each combination of rtt routers
            flows = [{'scheme':scheme_a, 'sender_router':rtt_a, 'count':3, 'flow_info':{'name':'%s_%d'%(scheme_a, rtt_a.args['delay'])}},
                     {'scheme':scheme_b, 'sender_router':rtt_b, 'count':3, 'flow_info':{'name':'%s_%d'%(scheme_b, rtt_b.args['delay'])}}]
            
            exs = [Experiment(  '3x%s%dms_3x%s%dms_queue%dB'%(scheme_a, rtt_a.args['delay'],scheme_b, rtt_b.args['delay'], q_size),
                                flows,
                                router,
                                runtime=runtime,
                                interval=5,
                                runs=runs,
                                tmp_dir=self.tmp_dir,
                                data_dir=self.data_dir)
                   for q_size, router in bottleneck_routers.items()]
            res.extend(exs)
        return res       

    def build_router_range(self, mbps, delay, num_routers, range_factor=10):
        """return a dict where
            values are routers with throughput 'mpbs' and delay 'delay' each, and queue sizes distributed logarithmically around the bdp within a range of 1/10bdp and 10bdp
            keys are the respectively used queue sizes"""
        bdp_bits = mbps*delay*1000.0*2
        bdp_bytes = bdp_bits/8
        step_size = 2.0/(num_routers-1)
        routers = {}
        current_queue_size = int(bdp_bytes/range_factor)
        for i in range(num_routers):
            r = Router(delay=delay, up_trace=Trace(mbps=mbps), up_queue_type='droptail', up_queue_args = 'bytes=%d'%int(current_queue_size))
            routers[int(current_queue_size)] = r
            current_queue_size *= math.pow(range_factor, step_size)
        return routers

    def run(self):
        ex_identifiers = ['ex_name', 'run_id']
        ex_parameters = ['bottleneck_tput', 'q_size', 'scheme_a', 'scheme_b', 'rtt_a', 'rtt_b', 'runtime']
        ex_results = ['loss', 'converged_fairness', 'time_to_max_fairness', 'delay', 'throughput', 'duration'] + ['throughput_rsd%d'%i for i in range(1, 7)]
        results = pd.DataFrame(columns=ex_identifiers + ex_parameters + ex_results)
        for ex in self.solo + self.mixed:
            try:
                print('running experiment %s' % ex.experiment_name)
                with utils.nostdout(do_nothing=self.verbose):
                    ex.run()
                    ex_results = ex.plot()                       
                    
                for run_id, res in ex_results.items():
                    res.pop('stats')
                    data = {}
                    data['ex_name']=ex.experiment_name
                    data['run_id']=int(run_id)
                    data['bottleneck_tput']=ex.router.up_trace.mbps
                    data['bottleneck_rtprop']=2*ex.router.delay
                    data['q_size']=int(ex.router.up_queue_args.split('=')[1])
                    data['scheme_a']=ex.flows[0]['scheme']
                    data['scheme_b']=ex.flows[1]['scheme']
                    data['rtprop_a']=2*ex.flows[0]['sender_router'].delay
                    data['rtprop_b']=2*ex.flows[1]['sender_router'].delay
                    data['runtime']=ex.runtime
                    for flow_id, rsd in res.pop('throughput_relative_standard_deviation').items():
                        data['throughput_rsd%d'%flow_id]=rsd
                    data['scheme_a_tput'] = res['group_data'][0]['tput']
                    data['schene_b_tput'] = res['group_data'][1]['tput']
                    res.pop('group_data')                        
                    data.update(res)
                    results = results.append(data, ignore_index=True)
                ex.cleanup_files()
            except Exception:
                with open('exceptions.txt', 'a+') as log:
                    traceback.print_exc(file=log)
                continue 

        results.to_csv(path_or_buf=os.path.join(self.data_dir, 'results.csv'), index=False)   
                
        


if __name__ == '__main__':
    b = Benchmark(scheme='bbr', verbose=False)
    b.run()

