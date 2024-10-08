# -*- coding: utf-8 -*-
"""
Created on Sun May 12 20:17:17 2019

@author: syuntoku

Modified by cadop Dec 19 2021
"""

from typing import List, Sequence
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
from . import utils

class Joint:

    # Defaults for all joints. Need be be floats, not ints
    effort_limit = 100.0
    vel_limit = 100.0

    def __init__(self, name: str, xyz: Sequence[float], rpy: Sequence[float], axis: Sequence[float], parent: str, child:str, joint_type: str, upper_limit: float, lower_limit: float):
        """
        Attributes
        ----------
        name: str
            name of the joint
        type: str
            type of the joint(ex: rev)
        xyz: [x, y, z]
            coordinate of the joint
        axis: [x, y, z]
            coordinate of axis of the joint
        parent: str
            parent link
        child: str
            child link
        joint_xml: str
            generated xml describing about the joint
        tran_xml: str
            generated xml describing about the transmission
        """
        self.name = name
        self.type = joint_type
        self.xyz = xyz
        self.rpy = rpy
        self.parent = parent
        self.child = child
        self._joint_xml = None
        self._tran_xml = None
        self.axis = axis  # for 'revolute' and 'continuous'
        self.upper_limit = upper_limit  # for 'revolute' and 'prismatic'
        self.lower_limit = lower_limit  # for 'revolute' and 'prismatic'
        
    @property
    def joint_xml(self):
        """
        Generate the joint_xml and hold it by self.joint_xml
        """

        joint = Element('joint')
        joint.attrib = {'name':utils.format_name(self.name), 'type':self.type}

        origin = SubElement(joint, 'origin')
        origin.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':' '.join([str(_) for _ in self.rpy])}

        parent = SubElement(joint, 'parent')
        self.parent = utils.format_name(self.parent)
        parent.attrib = {'link':self.parent}

        child = SubElement(joint, 'child')
        self.child = utils.format_name(self.child)
        child.attrib = {'link':self.child}

        if self.type == 'revolute' or self.type == 'continuous' or self.type == 'prismatic':        
            axis = SubElement(joint, 'axis')
            axis.attrib = {'xyz':' '.join([str(_) for _ in self.axis])}
        if self.type == 'revolute' or self.type == 'prismatic':
            limit = SubElement(joint, 'limit')
            limit.attrib = {'upper': str(self.upper_limit), 'lower': str(self.lower_limit),
                            'effort': f'{Joint.effort_limit}', 'velocity': f'{Joint.vel_limit}'}

        rough_string = ElementTree.tostring(joint, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self._joint_xml = "\n".join(reparsed.toprettyxml(indent="  ").split("\n")[1:])

        return self._joint_xml

    @property
    def transmission_xml(self):
        """
        Generate the tran_xml and hold it by self.tran_xml
        
        
        Notes
        -----------
        mechanicalTransmission: 1
        type: transmission interface/SimpleTransmission
        hardwareInterface: PositionJointInterface        
        """        
        
        tran = Element('transmission')
        tran.attrib = {'name':utils.format_name(self.name) + '_tran'}
        
        joint_type = SubElement(tran, 'type')
        joint_type.text = 'transmission_interface/SimpleTransmission'
        
        joint = SubElement(tran, 'joint')
        joint.attrib = {'name':utils.format_name(self.name)}
        hardwareInterface_joint = SubElement(joint, 'hardwareInterface')
        hardwareInterface_joint.text = 'hardware_interface/EffortJointInterface'
        
        actuator = SubElement(tran, 'actuator')
        actuator.attrib = {'name':utils.format_name(self.name) + '_actr'}
        hardwareInterface_actr = SubElement(actuator, 'hardwareInterface')
        hardwareInterface_actr.text = 'hardware_interface/EffortJointInterface'
        mechanicalReduction = SubElement(actuator, 'mechanicalReduction')
        mechanicalReduction.text = '1'

        rough_string = ElementTree.tostring(tran, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self._tran_xml  = "\n".join(reparsed.toprettyxml(indent="  ").split("\n")[1:])

        return self._tran_xml

class Link:

    scale = '0.001'

    def __init__(self, name, xyz, rpy, center_of_mass, sub_folder, mass, inertia_tensor, body_dict, sub_mesh, material_dict, visible):
        """
        Parameters
        ----------
        name: str
            name of the link
        xyz: [x, y, z]
            coordinate for the visual and collision
        center_of_mass: [x, y, z]
            coordinate for the center of mass
        link_xml: str
            generated xml describing about the link
        sub_folder: str
            the name of the repository to save the xml file
        mass: float
            mass of the link
        inertia_tensor: [ixx, iyy, izz, ixy, iyz, ixz]
            tensor of the inertia
        body_lst = [body1, body2, body3]
            list of visible bodies
        body_dict = {body.entityToken: name of occurrence}
            dictionary of body entity tokens to the occurrence name
        """

        self.name = name
        # xyz for visual
        self.xyz = [x for x in xyz]
        self.rpy = [x for x in rpy]
        # xyz for center of mass
        self.center_of_mass = [x for x in center_of_mass]
        self._link_xml = None
        self.sub_folder = sub_folder
        self.mass = mass
        self.inertia_tensor = inertia_tensor
        self.body_dict = body_dict
        self.sub_mesh = sub_mesh # if we want to export each body as a separate mesh
        self.material_dict = material_dict
        self.visible = visible

        
    @property
    def link_xml(self):
        """
        Generate the link_xml and hold it by self.link_xml
        """
        self.name = utils.format_name(self.name)

        # Only generate a link if there is an associated body
        if self.body_dict.get(self.name) is None:
            return ""

        link = Element('link')
        link.attrib = {'name':self.name}
        rpy = ' '.join([str(_) for _ in self.rpy])
        scale = ' '.join([self.scale]*3)

        #inertial
        inertial = SubElement(link, 'inertial')
        origin_i = SubElement(inertial, 'origin')
        origin_i.attrib = {'xyz':' '.join([str(_) for _ in self.center_of_mass]), 'rpy':rpy}       
        mass = SubElement(inertial, 'mass')
        mass.attrib = {'value':str(self.mass)}
        inertia = SubElement(inertial, 'inertia')
        inertia.attrib = {'ixx':str(self.inertia_tensor[0]), 'iyy':str(self.inertia_tensor[1]),
                        'izz':str(self.inertia_tensor[2]), 'ixy':str(self.inertia_tensor[3]),
                        'iyz':str(self.inertia_tensor[4]), 'ixz':str(self.inertia_tensor[5])}        
        
        # visual
        if self.sub_mesh: # if we want to export each as a separate mesh
            for body_name in self.body_dict[self.name]:
                # body_name = utils.format_name(body_name)
                visual = SubElement(link, 'visual')
                origin_v = SubElement(visual, 'origin')
                origin_v.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':rpy}
                geometry_v = SubElement(visual, 'geometry')
                mesh_v = SubElement(geometry_v, 'mesh')
                mesh_v.attrib = {'filename':f'package://{self.sub_folder}{utils.format_name(body_name)}.stl','scale':scale}
                material = SubElement(visual, 'material')
                material.attrib = {'name':'silver'}
        elif self.visible:
            visual = SubElement(link, 'visual')
            origin_v = SubElement(visual, 'origin')
            origin_v.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':rpy}
            geometry_v = SubElement(visual, 'geometry')
            mesh_v = SubElement(geometry_v, 'mesh')
            mesh_v.attrib = {'filename':f'package://{self.sub_folder}{utils.format_name(self.name)}.stl','scale':scale}
            material = SubElement(visual, 'material')
            material.attrib = {'name': self.material_dict[self.name]['material']}
    
        
        # collision
        if self.sub_mesh:
            for collision_body in self.body_dict[self.name]:
                collision = SubElement(link, 'collision')
                origin_c = SubElement(collision, 'origin')
                origin_c.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':rpy}
                geometry_c = SubElement(collision, 'geometry')
                mesh_c = SubElement(geometry_c, 'mesh')
                mesh_c.attrib = {'filename':f'package://{self.sub_folder}{utils.format_name(collision_body)}.stl','scale':scale}
        elif self.visible:
            collision = SubElement(link, 'collision')
            origin_c = SubElement(collision, 'origin')
            origin_c.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':rpy}
            geometry_c = SubElement(collision, 'geometry')
            mesh_c = SubElement(geometry_c, 'mesh')
            mesh_c.attrib = {'filename':f'package://{self.sub_folder}{utils.format_name(self.name)}.stl','scale':scale}

        rough_string = ElementTree.tostring(link, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self._link_xml  = "\n".join(reparsed.toprettyxml(indent="  ").split("\n")[1:])
        return self._link_xml
