from trace import Trace

class Router(object):
    """Abstract router for generating mahimahi commands"""

    default_args = {
        'delay':None,
        'up_trace':None,
        'down_trace':None,
        'up_queue_type':None,
        'up_queue_args':None,
        'down_queue_type':None,
        'down_queue_args':None,
        'up_loss':None,
        'down_loss':None
    }

    def __init__(self, **kwargs):
        """ Keyword arguments:
            delay -- delay in ms, integer or None (default: None)
            up_trace -- Trace for datalink, Trace or None (default:None)
            down_trace -- Trace for acklink, Trace or None (default:None)
            up_queue_type -- type of queue to be used for datalink, e.g. 'droptail'. See man mm-link for more options, string or None (default:None) 
            down_queue_type -- type of queue to be used for acklink, e.g. 'droptail'. See man mm-link for more options, string or None (default:None)
            up_queue_args -- queue arguments, e.g. 'packets=50', requires up_queue_type. See man mm-link for more options, string or None (default:None)
            down_queue_args -- queue arguments, e.g. 'packets=50', requires down_queue_type. See man mm-link for more options, string or None (default:None)
            up_loss -- fraction of packets to be lost in datalink, e.g. 0.2 loses 20% of data packets, float or None (default:None)
            down_loss -- fraction of packets to be lost in acklink, e.g. 0.2 loses 20% of acks, float or None (default:None)
        """

        self.args = dict(self.default_args)

        for k, v in kwargs.iteritems():
            if not k in self.default_args.keys():
                raise Exception('invalid router argument \'%s\'' % (k))

        self.args.update(kwargs)
        
        for k, v in self.args.iteritems():
            setattr(self, k, v)

    def get_mahimahi_link_args(self):
        """ return mahimahi link args string"""
        link_args = ''
        if self.up_queue_type:    link_args += '--uplink-queue=%s ' % (self.up_queue_type)
        if self.up_queue_args:    link_args += '--uplink-queue-args=%s ' % (self.up_queue_args)  
        if self.down_queue_type:  link_args += '--downlink-queue=%s ' % (self.down_queue_type)
        if self.down_queue_args:  link_args += '--downlink-queue-args=%s ' % (self.down_queue_args)
        return link_args

    def get_mahimahi_command(self, include_link=True):
        """return full mahimahi command"""
        command = ''

        if include_link:
            link_args = self.get_mahimahi_link_args()
            if self.up_trace and self.down_trace:
                command += 'mm-link %s %s %s' % (self.up_trace.get_path(), self.down_trace.get_path(), link_args)
            else:
                if self.up_trace or self.down_trace or link_args:
                    raise Exception('mm-link needs both up_trace and down_trace specified')
        
        if self.up_loss:      command += 'mm-loss uplink %f ' % (self.up_loss)
        if self.down_loss:    command += 'mm-loss downlink %f ' % (self.down_loss)
        if self.delay:        command += 'mm-delay %d ' % (self.delay)

        return command














