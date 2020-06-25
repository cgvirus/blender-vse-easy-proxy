import os
from sys import platform
import shutil
import subprocess
from pathlib import Path
from bpy_extras.io_utils import ImportHelper 
from bpy.props import CollectionProperty

import bpy
from bpy.types import (
    Menu,
    Panel,
    Operator,
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    PointerProperty,
    EnumProperty,
)

bl_info = {
    "name": "VSE Easy Proxy",
    "author": "CGVIRUS",
    "category": "Sequencer",
    "version": (1, 0),
    "wiki_url": "https://github.com/cgvirus/blender-vse-easy-proxy",
    "blender": (2, 80, 0),
}



class VSE_EasyProxyPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    if platform == "win32":
        cache_path= str(Path.home())+str(Path('/EasyProxyCache'))
    else:
        cache_path= str(Path.home())+str(Path('/EasyProxyCache'))
    
    ffmpegfilepath: bpy.props.StringProperty(
        name="FFMPEG",
        subtype='FILE_PATH',
        default = "ffmpeg"
    )
    
    proxyfilepath: bpy.props.StringProperty(
        name="Proxy Directory",
        subtype='FILE_PATH',
        default = str(cache_path)
    )


    def draw(self, context):
        layout = self.layout
        layout.label(text="""The path of FFMPEG executable if environment variable is not set""")
        layout.prop(self, "ffmpegfilepath")
        layout.label(text="""Path for global proxy directory""")
        layout.prop(self, "proxyfilepath")
        box = layout.box()
        box.operator(DeleteEasyProxy.bl_idname, icon= 'TRASH')


class ProxyProperty(PropertyGroup):
    
    
    crf: bpy.props.IntProperty(
        name= "CRF Quality",
        description= "CRF Qulaity. Lower makes bigger file size and better quality.",
        min= 5, max= 100,
        default = 20 
        )

    overwrite:bpy.props.BoolProperty(
        name= "Overwrite",
        description = "Overwrite existing proxy",
        default = 0
        )

    freeze:bpy.props.BoolProperty(
    name= "Freeze Blender",
    description = "Freeze Blender While Transcoding",
    default = 0
    )




class ToggleEasyProxy(bpy.types.Operator):

    bl_idname = "sequencer.toggle_easy_proxy"
    bl_label = "Toggle Proxy"
    bl_description = "Toggle proxy/original"



    toggle_proxy:bpy.props.BoolProperty(
        name= "Toggle Proxy",
        description = "Toggle proxy/original",
        default = 1
    ) 


    def execute(self,context):

        scene = context.scene
        proxyfilepath = Path(context.preferences.addons[__name__].preferences.proxyfilepath)
        # activestrp= bpy.context.scene.sequence_editor.active_strip

        if self.toggle_proxy == True:
            for sq in bpy.context.scene.sequence_editor.sequences_all:
                if sq.type == 'MOVIE':
                    activestrp= bpy.context.scene.sequence_editor.sequences_all[sq.name]
                    bpy.ops.sequencer.select_all()
                    bpy.ops.sequencer.enable_proxies(proxy_50=True)
                    activestrp.proxy.use_proxy_custom_directory = True
                    activestrp.proxy.directory = str(proxyfilepath)
                    for area in bpy.context.screen.areas:
                        if area.type == 'SEQUENCE_EDITOR':
                            for space in area.spaces:
                                if space.type == 'SEQUENCE_EDITOR': 
                                    space.proxy_render_size = 'PROXY_50'
            self.toggle_proxy = not self.toggle_proxy

        else:
            for area in bpy.context.screen.areas:
                if area.type == 'SEQUENCE_EDITOR':
                    for space in area.spaces:
                        if space.type == 'SEQUENCE_EDITOR': 
                            space.proxy_render_size = 'SCENE'
            self.toggle_proxy = True
    
        return {'FINISHED'}






class CreateProxy(bpy.types.Operator):

    bl_idname = "sequencer.create_easy_proxy"
    bl_label = "Create Proxy"
    bl_description = "Create proxy with ffmpeg"


    def execute(self,context):

        scene = context.scene
        mytool = scene.easy_proxy
        activestrp= bpy.context.scene.sequence_editor.active_strip
        proxyfilepath = Path(context.preferences.addons[__name__].preferences.proxyfilepath)
        ffmpegfilepath = Path(context.preferences.addons[__name__].preferences.ffmpegfilepath)
        ext = Path("proxy_50.avi")

        if activestrp.type == 'SOUND':
            self.report({'INFO'}, 'No Proxy on Sound File')
            return {'CANCELLED'}
        elif activestrp.type == 'IMAGE':
            self.report({'INFO'}, 'No Proxy on Image File')
            return {'CANCELLED'}        

        else:
            mov_path = Path(os.path.normpath(bpy.path.abspath(activestrp.filepath)))
            mov_name = Path(bpy.path.basename(activestrp.filepath))
            cmd = '%s -i "%s" -vf scale=640:-2 -vcodec libx264 -g 1 -bf 0 -vb 0 -crf %d -preset veryfast -acodec aac -ab 128k "%s/%s/%s" -y'\
            %(ffmpegfilepath,mov_path,mytool.crf,proxyfilepath,mov_name,ext)
            cmdpath=Path(cmd)

            # print(cmdpath)
            bpy.ops.sequencer.enable_proxies(proxy_50=True)
            activestrp.proxy.use_proxy_custom_directory = True
            activestrp.proxy.directory = str(proxyfilepath)
            
            
            if not os.path.exists(Path(proxyfilepath/mov_name)):
                os.makedirs(Path(proxyfilepath/mov_name))
            if os.path.exists(Path(proxyfilepath/mov_name/ext)) and mytool.overwrite == False:
                self.report({'INFO'}, 'proxy exists')
                # return {'CANCELLED'}
            else:
                proc = subprocess.Popen(str(cmdpath), stdin = subprocess.PIPE, stdout = subprocess.PIPE, shell=True)
                if mytool.freeze is True:
                    proc.communicate()
                    self.report({'INFO'}, 'Transcoding Done')                
                activestrp.use_proxy = False
                activestrp.use_proxy = True
                # return {'FINISHED'}
        
            for area in bpy.context.screen.areas:
                if area.type == 'SEQUENCE_EDITOR':
                    for space in area.spaces:
                        if space.type == 'SEQUENCE_EDITOR': 
                            space.proxy_render_size = 'PROXY_50'

        return {'FINISHED'} 


class CreateAllProxy(bpy.types.Operator):

    bl_idname = "sequencer.create_easy_all_proxy"
    bl_label = "Create All Proxy"
    bl_description = "Create all proxy with ffmpeg"


   
    def execute(self,context):
        
        scene = context.scene
        mytool = scene.easy_proxy
        
        proxyfilepath = Path(context.preferences.addons[__name__].preferences.proxyfilepath)
        ffmpegfilepath = Path(context.preferences.addons[__name__].preferences.ffmpegfilepath)

        ext = Path("proxy_50.avi")



        for sq in bpy.context.scene.sequence_editor.sequences_all:
            if sq.type == 'MOVIE':
                activestrp= bpy.context.scene.sequence_editor.sequences_all[sq.name]
                mov_path = Path(os.path.normpath(bpy.path.abspath(activestrp.filepath)))
                mov_name = Path(bpy.path.basename(activestrp.filepath))
                cmd = '%s -i "%s" -vf scale=640:-2 -vcodec libx264 -g 1 -bf 0 -vb 0 -crf %d -preset veryfast -acodec aac -ab 128k "%s/%s/%s" -y'\
                %(ffmpegfilepath,mov_path,mytool.crf,proxyfilepath,mov_name,ext)
                cmdpath=Path(cmd)

                print(cmdpath)
                bpy.ops.sequencer.enable_proxies(proxy_50=True)
                activestrp.proxy.use_proxy_custom_directory = True
                activestrp.proxy.directory = str(proxyfilepath)
                
                
                
                if not os.path.exists(Path(proxyfilepath/mov_name)):
                    os.makedirs(Path(proxyfilepath/mov_name))
                if os.path.exists(Path(proxyfilepath/mov_name/ext)) and mytool.overwrite == False:
                    self.report({'INFO'}, 'some proxies exist')
                    # return {'CANCELLED'}
                else:
                    proc = subprocess.Popen(str(cmdpath), stdin = subprocess.PIPE, stdout = subprocess.PIPE, shell=True)
                    if mytool.freeze is True:
                        proc.communicate()
                        self.report({'INFO'}, 'Transcoding Done')
                   
                    activestrp.use_proxy = False
                    activestrp.use_proxy = True
                    # return {'FINISHED'}

        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                for space in area.spaces:
                    if space.type == 'SEQUENCE_EDITOR': 
                        space.proxy_render_size = 'PROXY_50'
    
        
        return {'FINISHED'}



class DeleteEasyProxy(bpy.types.Operator):

    bl_idname = "preferences.delete_easy_proxy"
    bl_label = "Delete Proxy Folder"
    bl_description = "Delete the proxy folder"
 
    message : bpy.props.StringProperty(
        name = "message",
        description = "message",
        default = 'Proxy Folder Will be deleted'
    )
 
    def execute(self, context):

        proxyfilepath = Path(context.preferences.addons[__name__].preferences.proxyfilepath)       
        try:
            shutil.rmtree(proxyfilepath, ignore_errors=False, onerror=None)
            return {'FINISHED'}
        except:
            self.report({'INFO'}, 'No Directory Found')
            return {'FINISHED'}
        
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width = 400)
 
    def draw(self, context):
        self.layout.label(text=self.message)


class EasyProxyFilebrowser(bpy.types.Operator, ImportHelper): 
    
    bl_idname = "sequencer.create_easy_proxy_filebrowser" 
    bl_label = "Create Proxy in Browser"
    bl_description = "Selet files to create proxy in File Browser"
    
    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
    filter_folder : BoolProperty(name="Filter folders", description="", default=True, options={'HIDDEN'})
    filter_movie : BoolProperty(name="Filter folders", description="", default=True, options={'HIDDEN'})
    
    def execute(self, context): 
        
        scene = context.scene
        mytool = scene.easy_proxy  
        proxyfilepath = Path(context.preferences.addons[__name__].preferences.proxyfilepath)
        ffmpegfilepath = Path(context.preferences.addons[__name__].preferences.ffmpegfilepath)
        ext = Path("proxy_50.avi")
                        
        dirname = os.path.dirname(self.filepath)
        
        for f in self.files:
            activestrp= os.path.join(dirname, f.name) #get filepath properties from collection pointer

            mov_path = Path(os.path.normpath(bpy.path.abspath(activestrp)))
            mov_name = Path(bpy.path.basename(activestrp))
            cmd = '%s -i "%s" -vf scale=640:-2 -vcodec libx264 -g 1 -bf 0 -vb 0 -crf %d -preset veryfast -acodec aac -ab 128k "%s/%s/%s" -y'\
            %(ffmpegfilepath,mov_path,mytool.crf,proxyfilepath,mov_name,ext)
            
            cmdpath=Path(cmd)

            # print(cmdpath)
            
            
            
            if not os.path.exists(Path(proxyfilepath/mov_name)):
                os.makedirs(Path(proxyfilepath/mov_name))
            if os.path.exists(Path(proxyfilepath/mov_name/ext)) and mytool.overwrite == False:
                self.report({'INFO'}, 'some proxies exist')
                # return {'CANCELLED'}
            else:
                proc = subprocess.Popen(str(cmdpath), stdin = subprocess.PIPE, stdout = subprocess.PIPE, shell=True)
                if mytool.freeze is True:
                    proc.communicate()
                    self.report({'INFO'}, 'Transcoding Done')        
        
        return {'FINISHED'} 



class SequencerButtonsPanel:
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    @staticmethod
    def has_sequencer(context):
        return (context.space_data.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'})

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and (act_strip(context) is not None)



class SEQUENCER_PT_easy_proxy_settings(SequencerButtonsPanel, Panel):
    bl_label = "Easy Proxy Settings"
    bl_category = "Proxy & Cache"

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.scene.sequence_editor

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene
        mytool = scene.easy_proxy


        col = layout.column()
        layout.operator(ToggleEasyProxy.bl_idname)
        layout.prop(mytool,"crf")
        layout.prop(mytool,"overwrite")
        layout.prop(mytool,"freeze")
        layout.operator(CreateProxy.bl_idname)
        layout.operator(CreateAllProxy.bl_idname)
        layout.operator(EasyProxyFilebrowser.bl_idname)


# def menu_func(self,context):
#     self.layout.operator(CreateProxy.bl_idname)


classes = (

    VSE_EasyProxyPrefs,
    ProxyProperty,
    ToggleEasyProxy,
    CreateProxy,
    CreateAllProxy,
    DeleteEasyProxy,
    EasyProxyFilebrowser,
    SEQUENCER_PT_easy_proxy_settings,
)



def register():
    # bpy.types.SEQUENCER_MT_strip.append(menu_func)
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.easy_proxy = PointerProperty(type=ProxyProperty)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    # bpy.types.SEQUENCER_MT_strip.remove(menu_func)
    del bpy.types.Scene.easy_proxy


if __name__ == "__main__":
    register()