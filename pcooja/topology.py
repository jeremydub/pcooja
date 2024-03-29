import random
from math import *
import heapq
from lxml import etree
import os

from .motes.mote import MoteType, Mote
from .radio.medium import *
from .radio.udgm.medium import *
from .radio.dgrm.medium import *

import logging
logger = logging.getLogger("pcooja")

class Topology:
    def __init__(self, motes, radiomedium=None):
        self.motes=motes
        self.last_id=len(motes)
        self.set_medium(radiomedium)

    def set_medium(self, radiomedium):
        if radiomedium == None:
            self.radiomedium = UDGM()
        else:
            self.radiomedium = radiomedium
        self._update_nbr_counts()

    def get_density(self):
        density=0.0
        for mote in self.motes:
            density += mote.nbr_count

        density = density / len(self.motes)

        return density

    def _update_nbr_counts(self):
        for mote in self.motes:
            mote.nbr_count=self.get_nbr_count(mote)


    def get_nbr_count(self, mote):
        return len(self.get_neighbors(mote))
    
    def get_neighbors(self, mote):
        return list(filter(lambda m: m != mote and self.is_in_range(mote,m), \
                           self.motes))

    def is_in_range(self, mote1, mote2):
        """ Return if the mote1 can send message to the mote2 """
        return self.radiomedium.is_in_range(mote1, mote2)

    def generate_random_motes_from_mote(self, mote, mote_type, mote_type_class, n_random=5):
        radius_min=self.transmitting_range/4
        radius_max=self.transmitting_range*0.9
        random_motes=[]
        n = len(self.motes)
        initial_angle=random.random()*360.0
        for i in range(n_random):
            new_p=(mote.x+radius_min+random.random()*(radius_max-radius_min), mote.y)
            current_angle=(initial_angle+i*(360./n_random))%360
            (x,y)=rotate2d(current_angle, new_p, (mote.x,mote.y))
            random_motes.append(mote_type_class(n+1, x,y, mote_type))
        return random_motes

    def set_mote_type(self, mote_id, mote_type):
        if type(mote_id) == int:
            mote = self.__getitem__(mote_id)

            mote.mote_type = mote_type
        elif type(mote_id) == list:
            for mid in mote_id:
                self.set_mote_type(mid,mote_type)
    def __len__(self):
        return len(self.motes)

    def __eq__(self, other):
        if type(self)==type(other):
            if len(self.motes)==len(other.motes):
                for mote in self.motes:
                    if mote not in other.motes:
                        return False
                return True
            else:
                return False
        elif type(other)==list:
            if len(self.motes)==len(other):
                for mote in self.motes:
                    if mote not in other:
                        return False
                return True
            else:
                return False
        else:
            return False

    def __iter__(self):
        return iter(self.motes)

    def __getitem__(self, mote_id):
        for i in range(len(self.motes)):
            if self.motes[i].id == mote_id:
                return self.motes[i]
        raise IndexError("No mote with ID "+str(mote_id))

    @staticmethod
    def from_csc(file_path):
        """
        Parse a topology in .csc file
        """
        
        tree = etree.parse(file_path)
        return Topology.from_xml(tree, file_path)

    @staticmethod
    def from_xml(xml, file_path=None):
        # Parsing general simulation and radio settings
        simulation_tag=xml.xpath("/simconf/simulation")[0]

        radiomedium_tag = simulation_tag.find("radiomedium")
        radiomedium = RadioMedium.from_xml(radiomedium_tag)

        if file_path != None: 
            folder = "/".join(file_path.split('/')[:-1])
            if len(folder) == 0 or folder[0] != "/":
                folder = os.path.abspath(folder)
        else:
            folder = None

        # Parsing Mote types 
        available_mote_types = {}
        motetype_tags = simulation_tag.xpath("motetype")
        for motetype_tag in motetype_tags:
            mote_type = MoteType.from_xml(motetype_tag, folder)
            available_mote_types[mote_type.identifier] = mote_type

        # Parsing motes
        mote_tags = simulation_tag.xpath("mote")

        motes = []
        for mote_tag in mote_tags:
            interface_config_tags = mote_tag.xpath("interface_config")
            x, y = (None,None)
            for interface_config_tag in interface_config_tags:
                if "interfaces.Position" in interface_config_tag.text:
                    x = float(interface_config_tag.xpath("x/text()")[0])
                    y = float(interface_config_tag.xpath("y/text()")[0])

            motetype_identifier = mote_tag.xpath("motetype_identifier/text()")[0]
            mote_type = available_mote_types[motetype_identifier]
            motes.append(Mote.from_xml(mote_tag, x, y, mote_type))

        #get the BaseRSSI
        Mote.basseRSSI_from_xml(radiomedium_tag, motes)
        radiomedium.motes = motes

        return Topology(motes, radiomedium)
    
    @staticmethod
    def generate_topology_with_density(goal_density, n=25, transmitting_range=100, \
            root_type=None, node_type=None):
        attempts=0
        heap=[]
        root=SkyMote(1,0,0)
        heapq.heappush(heap, root)
        topology = Topology(heap, transmitting_range, transmitting_range+20)
        while len(heap) < n:
            current_n=len(topology.motes)
            # select mote with minimum neighbor count (from heap)
            min_nbr_mote = heapq.nsmallest(1,heap)[0]
            n_random=30
            # generate <n_random> random motes around that mote in a specific range
            random_motes=topology.generate_random_motes_from_mote(min_nbr_mote, node_type, n_random)
            new_densities=[0]*n_random
            i=0
            for random_mote in random_motes:
                c=topology.get_nbr_count(random_mote)
                new_densities[i]=(topology.get_density()*current_n+c)/(current_n+1)
                i+=1
            min_i=0
            min_value=abs(new_densities[0]-goal_density)
            for i in range(1,len(new_densities)):
                current_value = abs(new_densities[i]-goal_density)
                if current_value<min_value:
                    min_i = i
                    min_value = abs(new_densities[i]-goal_density)
            heapq.heappush(heap, random_motes[min_i])
            topology.update_nbr_counts()
            attempts += 1
        return topology

    @staticmethod
    def get_tree25_topology(mote_class, root_type=None, node_type=None):
        ROOT_ID=1

        l=[(242.83184008074136,-88.93434685786869,1),(205.7645134037647,-62.438740480554074,2),(250.51864863077387,\
            -59.2420165357677,3),(294.4736028715864,-63.23792146675066,4),(176.19481691449084,-35.26658694986995,5),\
            (222.54731411389315,-32.869043991280165,6),(273.694897230475,-29.672320046493798,7),(321.64575640227054,\
            -33.66822497747676,8),(159.4120162043624,-2.500166515809672,9),(196.97352255560222,-0.10262355721989598,10),\
            (252.91619158936365,1.495738415173288,11),(301.66623174735577,-0.10262355721989598,12),(346.4203669743649,\
            1.495738415173288,13),(124.24805281171236,22.27444405628468,14),(180.1907218454738,35.86052082162674,15),\
            (224.14567608628633,30.266253918250598,16),(276.0924401890648,35.86052082162674,17),(351.2154528915445,\
            37.45888279401993,18),(89.08408941906231,47.04905462837903,19),(180.1907218454738,75.02038914525976,20),\
            (245.7235627135943,66.22939829709723,21),(290.4776979406035,67.82776026949043,22),(370.3957965602627,\
            64.63103632470406,23),(93.07999435004527,82.21301802102909,24),(204.16615143137156,106.18844760692684,25)]
        motes=[]
        for elem in l:
            mote_id=elem[2]
            if mote_id==ROOT_ID:
                mote_type=root_type
            else:
                mote_type=node_type
            motes.append(mote_class(mote_id,elem[0],elem[1], mote_type))

        return Topology(motes)

def generate_topology_random(n=50, width=100, height=50, max_range=None):
    motes=[]
    attempts=0
    mote_id=0

    while len(motes) < n and attempts < 100*n:
            
        if max_range == None :
            x = random.random()*width-width/2
            y = random.random()*height-height/2

            motes.append(SkyMote(mote_id,x,y))
            mote_id += 1

        attempts += 1
    return motes

def rotate2d(degrees,point,origin):
    """
    A rotation function that rotates a point around a point
    """
    x = point[0] - origin[0]
    yorz = point[1] - origin[1]
    newx = (x*cos(radians(degrees))) - (yorz*sin(radians(degrees)))
    newyorz = (x*sin(radians(degrees))) + (yorz*cos(radians(degrees)))
    newx += origin[0]
    newyorz += origin[1]

    return (newx,newyorz)

if __name__=="__main__":

    for density in range(20,100,5):
        density=float(density)/10
        topology=generate_topology_with_density(density, 25)
        print(density, topology.get_density())

    exit()
