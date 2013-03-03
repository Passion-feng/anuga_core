"""
Runup example from the manual, slightly modified
"""
#---------
#Import Modules
#--------
import anuga
import numpy
from math import sin, pi, exp
from anuga import Domain

#---------
#Setup computational domain
#---------
points, vertices, boundary = anuga.rectangular_cross(100,3)
domain=Domain(points,vertices,boundary)    # Create Domain
domain.set_name('runup')                   # Output to file runup.sww
domain.set_datadir('.')                    # Use current folder
domain.set_quantities_to_be_stored({'stage': 2, 'xmomentum': 2, 'ymomentum': 2, 'elevation': 1})

#------------------------------------------------------------------------------
# Setup Algorithm, either using command line arguments
# or override manually yourself
#------------------------------------------------------------------------------
from anuga.utilities.argparsing import parse_standard_args
alg, cfl = parse_standard_args()
domain.set_flow_algorithm(alg)
domain.set_CFL(cfl)

#------------------
# Define topography
#------------------
def topography(x,y):
        return -x/2 #Linear bed slope

def stagefun(x,y):
    return -0.2 #Stage

domain.set_quantity('elevation',topography)     # Use function for elevation
domain.get_quantity('elevation').smooth_vertex_values() # Steve's fix -- without this, substantial artificial velcities are generated everywhere in the domain. With this fix, there are artificial velocities near the coast, but not elsewhere.
domain.set_quantity('friction',0.0)             # Constant friction
domain.set_quantity('stage', stagefun)          # Constant negative initial stage

#--------------------------
# Setup boundary conditions
#--------------------------
Br=anuga.Reflective_boundary(domain)            # Solid reflective wall
Bt=anuga.Transmissive_boundary(domain)          # Continue all values of boundary -- not used in this example
Bd=anuga.Dirichlet_boundary([-0.2, 0., 0.])     # Constant boundary values -- not used in this example
Bw=anuga.Time_boundary(domain=domain,
	function=lambda t: [(0.0*sin(t*2*pi)-0.1)*exp(-t)-0.1,  0.0,  0.0]) # Time varying boundary -- get rid of the 0.0 to do a runup.

#----------------------------------------------
# Associate boundary tags with boundary objects
#----------------------------------------------
domain.set_boundary({'left': Br, 'right': Bw, 'top': Br, 'bottom':Br})

#------------------------------
#Evolve the system through time
#------------------------------
#xwrite=open("xvel.out","wb")
#ywrite=open("yvel.out","wb")
## Set print options to be compatible with file writing via the 'print' statement 
#numpy.set_printoptions(threshold=numpy.nan, linewidth=numpy.nan)

for t in domain.evolve(yieldstep=0.2,finaltime=30.0):
    print domain.timestepping_statistics()
print 'Finished'