from test import run_tests
from collections import namedtuple
from router import Router
import analysis
from analysis.plot import Plot
import io
import itertools
import os
import shutil
from helpers import utils
from helpers.subprocess_wrappers import check_output

class Experiment():
    """ Wrapper for multi scheme experiments"""
    def __init__(self, experiment_name, flows, router, tmp_dir = './tmp_data', data_dir = './data', runtime=30, interval=1, runs=1):
        """
            Arguments:
            experiment_name -- the name the experiment is referenced by in report, plots, and filenames
            flows -- list of dictionaries where each dictionary must contain at least:
                    'scheme': name of the cc scheme used in the flow
                     and optionally may specify
                    'sender_router':router to be used for this flow alone (in addition to bottleneck link) (default:None)
                    'count':the number of flows with these parameter to be created (default:1)
		    'flow_info': dictionary containing 'color' (matplotlib color) and 'name' (string) for use in plots 
            router -- router for the bottleneck link
            
            Keyword Arguments:
            data_dir -- path of experiment data to be stored to
            tmp_dir -- path of temporary experiment data to be stored in, such as logs (will be cleared when cleanup is called)
            runtime -- experiment length in seconds
            interval -- interval between starting flows in seconds
            runs -- number of repetitions of experiment
        """
        self.experiment_name = experiment_name
        self.runs = runs
        self.data_dir = data_dir
        self.tmp_dir = tmp_dir
        self.next_flow_group_id = 0
        self.router = router
        self.flows = flows
        self.runtime=runtime
        converted_flows = []
        for flow in flows:
            for k in flow.keys():
                if not k in ['scheme', 'sender_router', 'count', 'flow_info']:
                    raise Exception("flow attribute '%s' not supported" % k) 
            converted_flow = {'scheme':flow['scheme']}
            if flow.get('sender_router'): converted_flow['mm_sender_cmd']=flow['sender_router'].get_mahimahi_command()
            converted_flow['flow_info'] = self.get_flow_info(flow)
            for i in range(flow.get('count', 1)):
                converted_flows.append(converted_flow)

        test_config = {'test-name':experiment_name, 'flows':converted_flows}
        
        #args
        args = {}
        args['test_config']=test_config
        args['flows']=len(converted_flows)
        args['mode']='local'
        args['data_dir']=self.tmp_dir
        args['runtime']=runtime
        args['interval']=interval
        args['start_run_id']=1
        args['run_times']=runs
        args['downlink_trace']=router.down_trace.get_path() if router.down_trace else 'traces/12mbps_constant.trace'
        args['uplink_trace']=router.up_trace.get_path() if router.up_trace else 'traces/12mbps_constant.trace'
        args['random_order']=None
        args['all']=None
        args['schemes']=None
        args['pkill_cleanup']=None

        args['prepend_mm_cmds']=router.get_mahimahi_command(include_link=False)
        args['append_mm_cmds']=''
        args['extra_mm_link_args']=router.get_mahimahi_link_args()

        Args = namedtuple('Args', args.keys())
        args_tuple = Args(**args)

        self.args_tuple = args_tuple

    def get_flow_info(self, flow):
        info = flow.get('flow_info', {})
        info['name'] = info.get('name', flow['scheme'])
        info['color'] = info.get('color', None)
        info['group'] = info.get('group', self.next_flow_group_id)
        self.next_flow_group_id += 1
        return info

    def run(self):
        """Run experiment""" 
	print(self.tmp_dir)
        run_tests(self.args_tuple)

    def plot(self):
        """Plot results of experiment (requires Experiment.run() to have been executed)"""
        plt_args = {}
        plt_args['schemes']=self.args_tuple.test_config['test-name']
        plt_args['data_dir']=self.tmp_dir
        plt_args['no_graphs']=None
        plt_args['custom_test']=True
        plt_args['include_acklink']=False
        Args = namedtuple('Args', plt_args.keys())
        p = Plot(Args(**plt_args), {i+1:flow['flow_info'] for i, flow in enumerate(self.args_tuple.test_config['flows'])})
        p.run()
        return p.perf_data[self.experiment_name]

    def cleanup_files(self, kill_9_iperf = True):

        #1. delete .log files explicitly
        log_types = ['acklink', 'datalink', 'mm_acklink', 'mm_datalink', 'stats']
        run_ids = list(range(1, self.runs+1))
        file_names = ['%s_%s_run%d.log'%(self.experiment_name, t, i) for t, i in itertools.product(log_types, run_ids)]
        file_paths = [os.path.join(self.tmp_dir, f) for f in file_names]
        for f in file_paths:
            os.remove(f)

        #2. delete all .log.ingress and .log.egress containing experiment name
        for filename in os.listdir(utils.tmp_dir):
            if not self.experiment_name in filename: continue
            path = os.path.join(utils.tmp_dir, filename)
            os.remove(path)

        #3. move all remaining files (graphs) to persistent data folder
	utils.make_sure_dir_exists(self.data_dir)
        for filename in os.listdir(self.tmp_dir):
            if not self.experiment_name in filename: continue
            path = os.path.join(self.tmp_dir, filename)
            new_path = os.path.join(self.data_dir, filename)
            shutil.move(path, new_path)

        if kill_9_iperf:
	    try:
                check_output('pkill -9 iperf', shell=True)
	    except:
		pass

        















