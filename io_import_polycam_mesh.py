# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# <pep8 compliant>

# Blend file saving was borrowed from https://github.com/CGCookie/io_export_blend, thanks!

bl_info = {
    "name": "Import and process GLTF photogrammetry",
    "author": "nikolajmunk",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import GLTF files, fix bad geometry, shade flat and save.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}


import bpy
import os

from bpy_extras.io_utils import ImportHelper
from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty

def actually_export(export_scene, filepath):
    # Set the export scene as the active scene
    bpy.context.window.scene = export_scene

    # Remove all other scenes
    for scn in bpy.data.scenes:
        if scn != export_scene:
            bpy.data.scenes.remove(scn)

    # Save data to desired path
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
    print('Object saved to ' + filepath)

    # Undo the scene deletion stuff
    #XXX Yes, this *is* a kind of kludgey way to put everything back... but it works!
    bpy.ops.ed.undo_push()
    bpy.ops.ed.undo()


def export_blend_objects(objects_to_export, filepath):
    print("Exporting objects to .blend...")
    objects = []
    object_names = []
    for ob in objects_to_export:
            objects.append(ob)
            object_names.append(ob.name)

    # Create a new empty scene to hold export objects
    export_scene = bpy.data.scenes.new("blend_export")

    # Add objects from list to scene
    for ob in objects:
        export_scene.collection.objects.link(ob)

    actually_export(export_scene, filepath)

    return {'FINISHED'}

class ImportSomeData(bpy.types.Operator, ImportHelper):
    """Batch import GLTF files and process them"""
    bl_idname = "import_scene.custom_scans"
    bl_label = "Import Scans"
    bl_options = {'PRESET', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".glb"

    filter_glob: StringProperty(
            default="*.glb",
            options={'HIDDEN'},
            )

    # Selected files
    files: CollectionProperty(type=PropertyGroup)

    def process_mesh(self, ob):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.set_normals_from_faces()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_flat()
        bpy.ops.object.modifier_add(type='DECIMATE')
        decimate_modifier = ob.modifiers['Decimate']
        decimate_modifier.ratio = 0.1
        print('Applied processing to: ' + ob.name)

    def execute(self, context):

        # Get the folder
        folder = os.path.dirname(self.filepath)
        print('Processing files in ' + folder)
        # Create destination folder
        folder_name = 'Processed Scans'
        destination_path = os.path.join(folder, folder_name)
        os.makedirs(destination_path,exist_ok=True)
        
        #obs = []
        # Iterate through the selected files
        for i in self.files:
            # Generate full path to file
            path_to_file = (os.path.join(folder, i.name))
            clean_name = i.name.replace('.glb', '')
            bpy.ops.import_scene.gltf(filepath=path_to_file)
            # Append Object(s) to the list
            #obs.append(context.selected_objects[:])
            for o in context.selected_objects:
                o.name = clean_name
            # Print the imported object reference
            print ("Imported object:", context.object)
            # Apply processing
            self.process_mesh(context.object)
            filename = clean_name + ".blend"
            filepath = os.path.join(destination_path, filename)
            export_blend_objects(context.selected_objects, filepath)

            #self.save_to_blend(context.selected_objects, destination_path)

        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Import and Process GLTF Photogrammetry")


def register():
    bpy.utils.register_class(ImportSomeData)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_scene.custom_scans('INVOKE_DEFAULT')

