# To change this template, choose Tools | Templates
# and open the template in the editor.

import anuga
import numpy
import math
import anuga.structures.inlet

from anuga.utilities.system_tools import log_to_file
from anuga.structures.inlet_operator import Inlet_operator
import parallel_inlet
import pypar

class Parallel_Inlet_operator(Inlet_operator):
    """Parallel Inlet Operator - add water to an inlet potentially 
    shared between different parallel domains.

    Sets up the geometry of problem

    Inherit from this class (and overwrite
    discharge_routine method for specific subclasses)

    Input: domain, line, 
    """

    """
    master_proc - index of the processor which coordinates all processors 
    associated with this inlet operator.
    procs - list of all processors associated with this inlet operator
    
    """

    def __init__(self,
                 domain,
                 line,
                 Q = 0.0,
                 description = None,
                 label = None,
                 logging = False,
                 master_proc = 0,
                 procs = None,
                 verbose = False):

        self.domain = domain
        self.domain.set_fractional_step_operator(self)
        self.line = numpy.array(line, dtype='d')
        self.master_proc = master_proc 

        if procs is None:
            self.procs = [self.master_proc]
        else:
            self.procs = procs

        self.myid = pypar.rank()

        # should set this up to be a function of time and or space)
        self.Q = Q

        if description == None:
            self.description = ' '
        else:
            self.description = description


        if label == None:
            self.label = "inlet_%g" % Inlet_operator.counter + "_P" + str(self.myid)
        else:
            self.label = label + '_%g' % Inlet_operator.counter + "_P" + str(self.myid)


        self.verbose = verbose

        # Keep count of inlet operator

        # Only master proc can update the static counter
        if self.myid == master_proc:
            Inlet_operator.counter += 1

        self.enquiry_point = 0.5*(self.line[0] + self.line[1])

        self.outward_vector = self.line
        self.inlet = parallel_inlet.Parallel_Inlet(self.domain, self.line, master_proc = master_proc,
                                                    procs = procs, verbose= verbose)
        self.set_logging(logging)

    def __call__(self):

        volume = 0

        # Need to run global command on all processors
        current_volume = self.inlet.get_global_total_water_volume()

        # Only the master proc calculates the update
        if self.myid == self.master_proc:
            timestep = self.domain.get_timestep()

            t = self.domain.get_time()
            Q1 = self.update_Q(t)
            Q2 = self.update_Q(t + timestep)

            volume = 0.5*(Q1+Q2)*timestep

            assert current_volume + volume >= 0.0 , 'Requesting too much water to be removed from an inlet!'

            #print "Volume to be removed from Inlet = " + str(volume)

        # Set stages evenly on all processors
        self.inlet.set_stages_evenly(volume)


    def update_Q(self, t):
        """Virtual method allowing local modifications by writing an
        overriding version in descendant
        """
        # Only one processor should call this function unless Q is parallelizable
        if callable(self.Q):
            Q = self.Q(t)[0]
        else:
            Q = self.Q

        return Q

    def statistics(self):
        # WARNING: requires synchronization, must be called by all procs associated
        # with this inlet

        message = ''

        inlet_stats = self.inlet.statistics()
        

        if self.myid == self.master_proc:
            message  = '=======================================\n'
            message += 'Parallel Inlet Operator: %s\n' % self.label
            message += '=======================================\n'
            
            message += 'Description\n'
            message += '%s' % self.description
            message += '\n'

            message += inlet_stats

            message += '=====================================\n'

        return message


    def print_statistics(self):
        # WARNING: requires synchronization, must be called by all procs associated
        # with this inlet
        
        print self.statistics()


    def print_timestepping_statistics(self):
        # WARNING: Must be called by master proc to have any effect

        if self.myid == self.master_proc:
            message = '---------------------------------------------\n'
            message += 'Parallel Inlet report for %s:\n' % self.label
            message += '--------------------------------------------\n'
            message += 'Q [m^3/s]: %.2f\n' % self.Q
        
            print message


    def set_logging(self, flag=True):
        # WARNING: Must be called by master proc to have any effect

        stats = self.statistics()
        self.logging = flag
        
        if self.myid == self.master_proc:
            # If flag is true open file with mode = "w" to form a clean file for logging
            # PETE: Have to open separate file for each processor
            if self.logging:
                self.log_filename = self.label + '.log'
                log_to_file(self.log_filename, stats, mode='w')
                log_to_file(self.log_filename, 'time,Q')

            #log_to_file(self.log_filename, self.culvert_type)


    def timestepping_statistics(self):

        message  = '%.5f, ' % self.domain.get_time()
        message += '%.5f, ' % self.Q

        return message

    def log_timestepping_statistics(self):
        # WARNING: Must be called by master proc to have any effect

        if self.myid == self.master_proc:
            if self.logging:
                log_to_file(self.log_filename, self.timestepping_statistics())



    def set_Q(self, Q):
        # LOCAL
        self.Q = Q

    def get_Q(self):
        # LOCAL
        return self.Q


    def get_inlet(self):
        # LOCAL
        return self.inlet

    def get_line(self):
        return self.line

    def get_master_proc(self):
        return self.master_proc

    def parallel_safe(self):
        return True
