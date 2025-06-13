import pymel.core as pm
import importlib

from core.utils import curve_library
importlib.reload(curve_library)

class CasperHelpers(object):
    @classmethod
    def add_attr(cls, node, long_name, attr_type, default_value, keyable=False):
        pm.addAttr(node, longName=long_name, attributeType = attr_type, defaultValue = default_value, keyable = keyable)

    @classmethod
    def set_attr(cls, node, attr, value, value_type = None):
        if value_type:
            pm.setAttr(f'{node}.{attr}',  *value, type=value_type)
        else:
            pm.setAttr(f'{node}.{attr}', value)

    @classmethod
    def connect_attr(cls, node_a, attr_a, node_b, attr_b, force=False):
        pm.connectAttr(f'{node_a}.{attr_a}',f'{node_b}.{attr_b}', force=force)

    @classmethod
    def lock_and_hide_attrs(cls, node, attrs, lock=True, hide=True, channelBox=False):
        keyable = not hide

        for attr in attrs:
            full_name = f'{node}.{attr}'
            pm.setAttr(full_name, lock=lock, keyable = keyable, channelBox = channelBox)
    @classmethod
    def create_display_layer(cls, name, members, reference=False):
        display_layer = pm.createDisplayLayer(name=name, empty=True)

        if reference:
            pm.setAttr(f'{display_layer}',2)
        if members:
            pm.editDisplayLayerMembers(display_layer, members, noRecurse=True)

        return display_layer


class BallAutoRig(object):

    def __init__(self):
        self.primary_color = [0.0, 0.0, 1.0]
        self.secondary_color = [1.0, 1.0, 1.0]

    def set_colors(self, primary, secondary):
        self.primary_color = primary
        self.secondary_color = secondary

    def create_ball(self,name,parent=None):
        ball_geo = pm.sphere(pivot=(0,0,0), axis=(0,1,0), radius=1, name=name)[0]
        if parent:
            ball_geo = pm.parent(ball_geo,parent)[0]

        return ball_geo

    def create_ball_ctrl(self, name, parent=None):
        curve_library_path ='/home/mago/casper/core/utils/curve_library.json'
        ball_ctrl = curve_library.create_curve_from_crv_lib('arrowBoth',curve_library_path)
        if parent:
            ball_ctrl = pm.parent(ball_ctrl,parent)[0]

        CasperHelpers.lock_and_hide_attrs(ball_ctrl,['sx','sy','sz','v'])
        CasperHelpers.set_attr(ball_ctrl,'rotateOrder',3)

        ball_ctrl = pm.rename(ball_ctrl,name)
        return ball_ctrl

    def construct_rig(self, name='ball'):
        pm.select(clear=True)
        root_grp = pm.group(name=name, empty=True, world=True)
        anim_controls_grp = pm.group(name='anim_controls', empty=True, parent=root_grp)
        geometry_grp = pm.group(name='geometry_doNotTouch', empty=True, parent=root_grp)
        ball_geo = self.create_ball('ball_geo', parent=geometry_grp)
        ball_ctrl = self.create_ball_ctrl('ball_ctrl',parent=anim_controls_grp)

        pm.parentConstraint(ball_ctrl,ball_geo,maintainOffset=True, weight=1)
        CasperHelpers.create_display_layer("ball_geometry",[ball_geo], True)




pm.newFile(force=True)
ball = BallAutoRig()
ball.construct_rig()


