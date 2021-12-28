bl_info = {
    "name": "Procedural Symmetries",
    "description": "This tool automates the process of itteritavly adding symmetry planes to a custom mesh.",
    "author": "Vivian Bolsee",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"
}

import bpy
import mathutils
import random
import math
from bpy.props import (BoolVectorProperty,
                       IntProperty,
                       FloatProperty,
                       PointerProperty
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup
                       )

class PSProperties(PropertyGroup):
    PSIterations : IntProperty(
        name = "Itereations",
        description="The number of cycle through all the symmetries.",
        default = 4,
        min = 1,
        max = 10
        )

    PSSymmetries : IntProperty(
        name = "Symmetries",
        description="The number of symmetries per cycle.",
        default = 6,
        min = 1,
        max = 10
        )
        
    PSOffsetMin : FloatProperty(
        name = "Offset Min",
        description="The lower bound to the offset of the symmetry plane from the origin.",
        default = -1.0,
        min = -10.0,
        max = 10.0
        )

    PSOffsetMax : FloatProperty(
        name = "Offset Max",
        description="The upper bound to the offset of the symmetry plane from the origin.",
        default = 0.0,
        min = -10.0,
        max = 10.0
        )
    PSFinalSymmetry : BoolVectorProperty(
        name = "",
        subtype='XYZ',
        description="Apply a final symmetry in on or more primary axis.",
        default=(True,False,True)
        )

def PSOrthoRandom(right, up, forward):
    a = random.uniform(0,6.2831853)
    s = math.sin(a)
    c = math.cos(a)
    return ((up*s+forward*c)).normalized()

def PSRandomize(selected,min,max):
    right = mathutils.Vector((1.0, 0.0, 0.0))
    up = mathutils.Vector((0.0, 0.0, 1.0))
    forward = mathutils.Vector((0.0, 1.0, 0.0))
    
    for i in selected.children:
        newr = PSOrthoRandom(right, up, forward)
        up = newr.cross(right).normalized()
        forward = up.cross(newr)
        right = newr
        i.rotation_euler = (0.0,-math.asin(right.z),math.atan2(right.y,right.x))
        i.location = right*random.uniform(min,max)

class PS_OT_Generate(bpy.types.Operator):
    bl_idname = "ps.generate"
    bl_label = "Generate"

    def execute(self, context):
        scene = context.scene
        view_layer = context.view_layer
        pointer = scene.PSPointer
        self.report({'INFO'}, "Generating")
        if len(context.selected_objects) != 1:
            self.report({'ERROR'}, "You must have a single mesh selected.")
            return {'CANCELLED'}
        selected = context.selected_objects[0]
        collection = selected.users_collection[0]
        layer_collection = view_layer.layer_collection.children[collection.name]
        view_layer.active_layer_collection = layer_collection
        selected.modifiers.clear()
        
        for o in scene.objects:
            o.select_set(False)
        for c in selected.children:
            try:
                c.select_set(True)
            except ReferenceError as e:
                continue
        bpy.ops.object.delete()
        selected.select_set(True)
        empties = []
        for i in range(pointer.PSSymmetries):
            o = bpy.data.objects.new( "Symmetry{}".format(i), None )
            view_layer.active_layer_collection.collection.objects.link(o)
            o.parent = selected
            o.rotation_mode = 'XYZ'
            o.empty_display_type = 'ARROWS'
            o.empty_display_size = 0.0001
            empties.append(o)
        for i in range(pointer.PSIterations):
            for j in range(pointer.PSSymmetries):
                m = selected.modifiers.new("Mirror{}{}".format(i,j), 'MIRROR')
                m.use_bisect_axis[0] = True
                m.mirror_object = empties[j]
        m = selected.modifiers.new("FinalMirror", 'MIRROR')
        m.use_axis[0] = pointer.PSFinalSymmetry[0]
        m.use_axis[1] = pointer.PSFinalSymmetry[1]
        m.use_axis[2] = pointer.PSFinalSymmetry[2]
        m.use_bisect_axis[0] = pointer.PSFinalSymmetry[0]
        m.use_bisect_axis[1] = pointer.PSFinalSymmetry[1]
        m.use_bisect_axis[2] = pointer.PSFinalSymmetry[2]
        PSRandomize(selected,pointer.PSOffsetMin,pointer.PSOffsetMax)
        return {'FINISHED'}
    
class PS_OT_Randomize(bpy.types.Operator):
    bl_idname = "ps.randomize"
    bl_label = "Randomize"

    def execute(self, context):
        scene = context.scene
        pointer = scene.PSPointer
        self.report({'INFO'}, "Randomizing")
        if len(context.selected_objects) != 1:
            self.report({'ERROR'}, "You must have a single mesh selected.")
            return {'CANCELLED'}
        selected = context.selected_objects[0]
        PSRandomize(selected,pointer.PSOffsetMin,pointer.PSOffsetMax)
        return {'FINISHED'}

class PSPanelBase:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tools"
    bl_options = {"DEFAULT_CLOSED"}
    
class PS_PT_Panel(PSPanelBase, bpy.types.Panel):
    bl_idname = "ProceduralSymmetries"
    bl_label = "Procedural Symmetries"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        pointer = scene.PSPointer
        layout.prop(pointer, "PSIterations")
        layout.prop(pointer, "PSSymmetries") 
        layout.prop(pointer, "PSOffsetMin")
        layout.prop(pointer, "PSOffsetMax")
        layout.label(text="Final Symmetries:")
        layout.prop(pointer, "PSFinalSymmetry")
        layout.operator("ps.generate")
        layout.operator("ps.randomize")

def register():
    bpy.utils.register_class(PSProperties)
    bpy.utils.register_class(PS_OT_Generate)
    bpy.utils.register_class(PS_OT_Randomize)
    bpy.utils.register_class(PS_PT_Panel)
    bpy.types.Scene.PSPointer = PointerProperty(type=PSProperties)
    
def unregister():
    bpy.utils.unregister_class(PSProperties)
    bpy.utils.unregister_class(PS_OT_Generate)
    bpy.utils.unregister_class(PS_OT_Randomize)
    bpy.utils.unregister_class(PS_PT_Panel)
    del bpy.types.Scene.PSPointer

if __name__ == "__main__":
    register()
