import math
from numpy.random import poisson
import argparse
import os
from helpers import utils
import context

"""Tool for generating mahimahi trace files. Can be used as a standalone commandline tool or from another python script."""

class Trace():
    """Abstract trace object. Generates traces if they do not already exist."""
    def __init__(self, mbps = 8, distribution = 'constant', file_path = None, ms = 1000):
	"""
	Arguments:
		mbps -- float or integer, desired throughput
		distribution -- 'constant' or 'poisson', depending on the distribution ot be used
		file_path -- string, optional. If None, a combination of distribution and throughput will be used as default
		ms -- int, maximum length of generated trace
	"""
        self.mbps=mbps
        if file_path: self.file_path = file_path
        else:
			trace_dir=os.path.join(context.src_dir, 'experiments/traces')
	    	utils.make_sure_dir_exists(trace_dir)
        	self.file_path = '%s/%dmbps_%s.trace'%(trace_dir, mbps, distribution)
        	if not os.path.isfile(self.file_path):
        		self.generate_trace(mbps, distribution, trace_ms = ms, file_path = self.file_path)

    def generate_constant_trace(self, mbps, max_trace_ms = 1000):
        mtu_per_ms = mbps/12.0 #Mbps/8/1500*1000
        full_mtu_per_ms = int(math.floor(mtu_per_ms))
        mtu_buildup = 0.0
        trace = []
        for i in xrange(1, max_trace_ms+1):
            trace = trace + [i]*full_mtu_per_ms
            mtu_buildup += mtu_per_ms - full_mtu_per_ms
            if mtu_buildup >= 1.0:
                trace.append(i)
                mtu_buildup -=1
            if abs(len(trace)/float(i)-mtu_per_ms) < 0.05:
                break


        str_trace = map(str, trace)
        result = '\n'.join(str_trace) + '\n'

        return result

    def generate_poisson_trace(self, mbps, trace_ms=1000):
        mtu_per_ms = mbps/12.0 #Mbps/8/1500*1000
        distribution = poisson(mtu_per_ms, trace_ms)
        trace = []
        for i, p in enumerate(distribution):
            trace += [i+1]*p
        str_trace = map(str, trace)
        result = '\n'.join(str_trace) + '\n'

        return result

    #Mbps: average Mb/s of the generated trace
    #distribution: "constant" or "poisson", depending on the probability distribution to be used
    #trace size: length of trace file in milliseconds        
    def generate_trace(self, mbps, distribution, trace_ms=1000, file_path=None):
        if distribution == "constant": trace = self.generate_constant_trace(mbps, trace_ms)
        elif distribution == "poisson": trace = self.generate_poisson_trace(mbps, trace_ms)
        else: raise Exception("unknown distribution \"%s\"" % distribution)

        if file_path:
            with open(file_path, "w+") as f:
                f.write(trace)

        return trace

    def get_path(self):
        return self.file_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Mahimahi trace files.')
    parser.add_argument('Mbps', type=float, help='average Mbps of the trace file')
    parser.add_argument('distribution', help='"constant" or "poisson", the distribution to be used')
    parser.add_argument('--trace_ms', type=int, help='maximum length of the trace in ms', default=1000)
    parser.add_argument('--file', help='file path to write trace to')
    args = parser.parse_args()
    
    print(Trace(file_path='a').generate_trace(args.Mbps, args.distribution, args.trace_ms, args.file))
    
