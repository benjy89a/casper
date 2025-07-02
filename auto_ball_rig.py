import pymel.core as pm
import importlib

from ..core.utils import curve_library

importlib.reload(curve_library)

'''
스쿼시까지 구현 완료.
파이멜화 진행후 유아이 구현해보기
'''

class CasperHelpers(object):
    @classmethod
    def add_attr(cls, node, long_name, attr_type, default_value, keyable=False):
        pm.addAttr(node, longName=long_name, attributeType=attr_type, defaultValue=default_value, keyable=keyable)

    @classmethod
    def set_attr(cls, node, attr, value, value_type=None):
        if value_type:
            pm.setAttr(f'{node}.{attr}', *value, type=value_type)
        else:
            pm.setAttr(f'{node}.{attr}', value)

    @classmethod
    def connect_attr(cls, node_a, attr_a, node_b, attr_b, force=False):
        pm.connectAttr(f'{node_a}.{attr_a}', f'{node_b}.{attr_b}', force=force)

    @classmethod
    def lock_and_hide_attrs(cls, node, attrs, lock=True, hide=True, channelBox=False):
        keyable = not hide

        for attr in attrs:
            full_name = f'{node}.{attr}'
            pm.setAttr(full_name, lock=lock, keyable=keyable, channelBox=channelBox)

    @classmethod
    def make_unselectable(cls, transform_node):
        shape_node = transform_node.getShape()

        cls.set_attr(shape_node, "overrideEnabled", True)
        cls.set_attr(shape_node, "overrideDisplayType", 2)

    @classmethod
    def create_display_layer(cls, name, members, reference=False):
        display_layer = pm.createDisplayLayer(name=name, empty=True)

        if reference:
            pm.setAttr(f'{display_layer}.displayType', 2)
        if members:
            pm.editDisplayLayerMembers(display_layer, members, noRecurse=True)

        return display_layer

    @classmethod
    def create_and_assign_lambert_shader(cls, name, shape_node):
        shader = pm.shadingNode('lambert', name=name, asShader=True)
        shader_sg = pm.sets(name=f'{shader}SG', renderable=True, noSurfaceShader=True, empty=True)
        cls.connect_attr(shader, "outColor", shader_sg, "surfaceShader")
        pm.sets(shader_sg, e=True, forceElement=[shape_node])

        return shader


class BallAutoRig(object):

    def __init__(self):
        self.primary_color = [0.0, 0.0, 1.0]
        self.secondary_color = [1.0, 1.0, 1.0]

    def set_colors(self, primary, secondary):
        self.primary_color = primary
        self.secondary_color = secondary

    def construct_rig(self, name='ball'):
        pm.select(clear=True)
        root_grp = pm.group(name=name, empty=True, world=True)
        anim_controls_grp = pm.group(name='anim_controls', empty=True, parent=root_grp)
        geometry_grp = pm.group(name='geometry_doNotTouch', empty=True, parent=root_grp)
        ball_geo = self.create_ball('ball_geo', parent=geometry_grp)
        ball_ctrl = self.create_ball_ctrl('ball_ctrl', parent=anim_controls_grp)

        pm.parentConstraint(ball_ctrl, ball_geo, maintainOffset=True, weight=1)

        squash_grp = pm.group(name='squash_grp', empty=True, parent=anim_controls_grp)
        squash_ctrl = self.create_squash_ctrl('squash_ctrl', parent=squash_grp)

        pm.pointConstraint(ball_ctrl, squash_grp, offset=[0, 0, 0], weight=1)

        self.create_squash_deformer(ball_geo, squash_ctrl)

        CasperHelpers.create_display_layer("ball_geometry", [ball_geo], True)

    def create_ball(self, name, parent=None):
        ball_geo = pm.sphere(pivot=(0, 0, 0), axis=(0, 1, 0), radius=1, name=name)[0]
        if parent:
            ball_geo = pm.parent(ball_geo, parent)[0]

        self.create_ball_shader(ball_geo)

        return ball_geo

    def create_ball_ctrl(self, name, parent=None):
        curve_library_path = '/home/mago/casper/core/utils/curve_library.json'
        ball_ctrl = curve_library.create_curve_from_crv_lib('arrowBoth', curve_library_path)
        if parent:
            ball_ctrl = pm.parent(ball_ctrl, parent)[0]

        CasperHelpers.lock_and_hide_attrs(ball_ctrl, ['sx', 'sy', 'sz', 'v'])
        CasperHelpers.set_attr(ball_ctrl, 'rotateOrder', 3)

        ball_ctrl = pm.rename(ball_ctrl, name)
        return ball_ctrl

    def create_ball_shader(self, ball_geo):
        ball_shape = ball_geo.getShape()
        ball_shader = CasperHelpers.create_and_assign_lambert_shader("ballShader", ball_shape)

        ramp = pm.shadingNode("ramp", name='ballRamp', asTexture=True)
        CasperHelpers.set_attr(ramp, "interpolation", 0)
        CasperHelpers.set_attr(ramp, "colorEntryList[0].position", 0.0)
        CasperHelpers.set_attr(ramp, "colorEntryList[0].color", self.primary_color, value_type="double3")
        CasperHelpers.set_attr(ramp, "colorEntryList[1].position", 0.5)
        CasperHelpers.set_attr(ramp, "colorEntryList[1].color", self.secondary_color, value_type="double3")

        place2d_util = pm.shadingNode('place2dTexture', name='ballPlace2dTexture', asUtility=True)
        CasperHelpers.set_attr(place2d_util, "repeatU", 1)
        CasperHelpers.set_attr(place2d_util, "repeatV", 3)

        CasperHelpers.connect_attr(place2d_util, "outUV", ramp, "uv")
        CasperHelpers.connect_attr(place2d_util, "outUvFilterSize", ramp, "uvFilterSize")

        CasperHelpers.connect_attr(ramp, "outColor", ball_shader, "color")

    def create_squash_ctrl(self, name, parent=None):
        curve_library_path = '/home/mago/casper/core/utils/curve_library.json'
        squash_ctrl = curve_library.create_curve_from_crv_lib('circle', curve_library_path)
        if parent:
            squash_ctrl = pm.parent(squash_ctrl, parent)[0]
        CasperHelpers.lock_and_hide_attrs(squash_ctrl, ['sx', 'sy', 'sz', 'v'])
        CasperHelpers.set_attr(squash_ctrl, "rotateOrder", 3)
        CasperHelpers.add_attr(squash_ctrl, "squashStretch", "double", 0, keyable=True)

        squash_ctrl = pm.rename(squash_ctrl, name)

        return squash_ctrl

    def create_squash_deformer(self, squash_obj, squash_ctrl):
        pm.select(squash_obj, replace=True)
        squash_deformer, squash_handle = pm.nonLinear(type='squash')

        squash_handle = pm.rename(squash_handle, "ball_squash")

        CasperHelpers.set_attr(squash_handle, "visibility", False)
        CasperHelpers.lock_and_hide_attrs(squash_handle, ["v"], hide=False)

        pm.parent(squash_handle, squash_ctrl)
        CasperHelpers.connect_attr(squash_ctrl, "squashStretch", squash_deformer, "factor", force=True)

        pm.select(clear=True)


pm.newFile(force=True)
ball = BallAutoRig()
ball.construct_rig()


