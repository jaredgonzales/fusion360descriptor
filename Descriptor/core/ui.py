''' module: user interface'''

from typing import Optional
import adsk.core, adsk.fusion, traceback

try:
    from scipy.spatial.transform import Rotation # Test whether it's there
    _ = Rotation # Noop for import to not be unused
except ModuleNotFoundError:
    import sys
    import subprocess
    import os.path
    exec = sys.executable
    if "python" not in os.path.basename(sys.executable).lower():
        # There is a crazy thing on Mac, where sys.executable is Fusion iteself, not Python :(
        exec = subprocess.__file__
        for i in range(3):
            exec = os.path.dirname(exec)
        exec = os.path.join(exec, "bin", "python")
    subprocess.check_call([exec, '-m', 'ensurepip'])
    subprocess.check_call([exec, '-m', 'pip', 'install', 'scipy'])

from . import utils
from . import manager

def save_dir_dialog(ui: adsk.core.UserInterface) -> Optional[str]:     
    '''display the dialog to pick the save directory

    Parameters
    ----------
    ui : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    '''    

    # Set styles of folder dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'URDF Save Folder Dialog' 
    
    # Show folder dialog
    dlgResult = folderDlg.showDialog()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        return folderDlg.folder
    return None

def json_file_dialog(ui: adsk.core.UserInterface) -> Optional[str]:     
    '''display the dialog to pick a json file

    Parameters
    ----------
    ui : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    '''    

    # Set styles of folder dialog.
    fileDlg = ui.createFileDialog()
    fileDlg.filter = "Name Map JSON file (*.json)"
    fileDlg.title = 'Name Mapping File Dialog' 
    fileDlg.isMultiSelectEnabled = False
    
    # Show folder dialog
    dlgResult = fileDlg.showOpen()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        return fileDlg.filename
    return None

class MyInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, ui: adsk.core.UserInterface):
        self.ui = ui
        super().__init__()

    def notify(self, eventArgs: adsk.core.InputChangedEventArgs) -> None:
        try:
            cmd = eventArgs.firingEvent.sender
            assert isinstance(cmd, adsk.core.Command)
            inputs = cmd.commandInputs
            cmdInput = eventArgs.input

            # Get settings of UI
            directory_path = inputs.itemById('directory_path')
            name_map = inputs.itemById('name_map')
            robot_name = inputs.itemById('robot_name')
            save_mesh = inputs.itemById('save_mesh')
            sub_mesh = inputs.itemById('sub_mesh')
            mesh_resolution = inputs.itemById('mesh_resolution')
            inertia_precision = inputs.itemById('inertia_precision')
            target_units = inputs.itemById('target_units')
            target_platform = inputs.itemById('target_platform')

            utils.log(f"DEBUG: UI: processing command: {cmdInput.id}")

            assert isinstance(directory_path, adsk.core.TextBoxCommandInput)
            assert isinstance(name_map, adsk.core.TextBoxCommandInput)
            assert isinstance(robot_name, adsk.core.TextBoxCommandInput)
            assert isinstance(save_mesh, adsk.core.BoolValueCommandInput)
            assert isinstance(sub_mesh, adsk.core.BoolValueCommandInput)
            assert isinstance(mesh_resolution, adsk.core.DropDownCommandInput)
            assert isinstance(inertia_precision, adsk.core.DropDownCommandInput)
            assert isinstance(target_units, adsk.core.DropDownCommandInput)
            assert isinstance(target_platform, adsk.core.DropDownCommandInput)

            if cmdInput.id == 'generate':
                # User asked to generate using current settings
                # print(f'{directory_path.text}, {save_mesh.value}, {mesh_resolution.selectedItem.name},\
                #         {inertia_precision.selectedItem.name},\
                #         {target_units.selectedItem.name} )

                document_manager = manager.Manager(directory_path.text, robot_name.text,
                                                   save_mesh.value, sub_mesh.value,
                                                   mesh_resolution.selectedItem.name, 
                                                   inertia_precision.selectedItem.name, 
                                                   target_units.selectedItem.name, 
                                                   target_platform.selectedItem.name,
                                                   name_map.text)
                
                # Generate
                document_manager.run()

            elif cmdInput.id == 'preview':
                # Generate Hierarchy and Preview in panel
                document_manager = manager.Manager(directory_path.text, robot_name.text, save_mesh.value, sub_mesh.value, mesh_resolution.selectedItem.name, 
                                                   inertia_precision.selectedItem.name, target_units.selectedItem.name, 
                                                   target_platform.selectedItem.name, name_map.text)
                # # Generate
                _joints = document_manager.preview()

                joints_text = inputs.itemById('jointlist')
                assert isinstance(joints_text, adsk.core.TextBoxCommandInput)

                _txt = 'joint name: parent link-> child link\n'

                for k, j in _joints.items():
                    _txt += f'{k} : {j.parent} -> {j.child}\n' 
                joints_text.text = _txt

            elif cmdInput.id == 'save_dir':
                # User set the save directory
                name_map_file = save_dir_dialog(self.ui)
                if name_map_file is not None:
                    directory_path.text = name_map_file

            elif cmdInput.id == 'set_name_map':
                # User set the save directory
                name_map_file = json_file_dialog(self.ui)
                if name_map_file is not None:
                    name_map.text = name_map_file

        except:
            if self.ui:
                self.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self, ui):
        self.ui = ui
        super().__init__()
    def notify(self, eventArgs: adsk.core.CommandEventArgs) -> None:
        try:
            adsk.terminate()
        except:
            if self.ui:
                self.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCreatedHandler(adsk.core.CommandCreatedEventHandler):
    '''[summary]

    Parameters
    ----------
    adsk : adsk.core.CommandCreatedEventHandler
        Main handler for callbacks
    '''    
    def __init__(self, ui: adsk.core.UserInterface, handlers):
        '''[summary]

        Parameters
        ----------
        ui : adsk.core.UserInterface
            main variable to interact with autodesk
        handlers : list
            list to keep reference to UI handler
        '''        
        self.ui = ui
        self.handlers = handlers
        super().__init__()

    def notify(self, eventArgs: adsk.core.CommandCreatedEventArgs) -> None:
        ''' Construct the GUI and set aliases to be referenced later

        Parameters
        ----------
        args : adsk.core.CommandCreatedEventArgs
            UI information
        '''        
        try:
            cmd = eventArgs.command
            onDestroy = MyDestroyHandler(self.ui)
            cmd.destroy.add(onDestroy)
            
            onInputChanged = MyInputChangedHandler(self.ui)
            cmd.inputChanged.add(onInputChanged)
            
            self.handlers.append(onDestroy)
            self.handlers.append(onInputChanged)
            inputs = cmd.commandInputs

            assert manager.Manager.root is not None

            # Show path to save
            inputs.addTextBoxCommandInput('directory_path', 'Save Directory', 'C:', 2, True)
            # Button to set the save directory
            btn = inputs.addBoolValueInput('save_dir', 'Set Save Directory', False)
            btn.isFullWidth = True

            inputs.addTextBoxCommandInput('robot_name', 'Robot Name', manager.Manager.root.name.split()[0], 1, False)

            inputs.addTextBoxCommandInput('name_map', 'Name Map File', '', 1, True)
            # Button to set the save directory
            btn = inputs.addBoolValueInput('set_name_map', 'Select Name Map File', False)
            btn.isFullWidth = True

            # Add checkbox to generate/export the mesh or not
            inputs.addBoolValueInput('save_mesh', 'Save Mesh', True)

            # Add checkbox to generate/export sub meshes or not
            inputs.addBoolValueInput('sub_mesh', 'Sub Mesh', True)

            # Add dropdown to determine mesh export resolution
            di = inputs.addDropDownCommandInput('mesh_resolution', 'Mesh Resolution', adsk.core.DropDownStyles.TextListDropDownStyle)
            di = di.listItems
            di.add('Low', True, '')
            di.add('Medium', False, '')
            di.add('High', False, '')

            # Add dropdown to determine inertia calculation resolution
            di = inputs.addDropDownCommandInput('inertia_precision', 'Inertia Precision', adsk.core.DropDownStyles.TextListDropDownStyle)
            di = di.listItems
            di.add('Low', True, '')
            di.add('Medium', False, '')
            di.add('High', False, '')

            # Add dropdown to set target export units
            di = inputs.addDropDownCommandInput('target_units', 'Target Units', adsk.core.DropDownStyles.TextListDropDownStyle)
            di = di.listItems
            di.add('mm', False, '')
            di.add('cm', False, '')
            di.add('m', True, '')

            # Set the type of platform to target for building XML
            di = inputs.addDropDownCommandInput('target_platform', 'Target Platform', adsk.core.DropDownStyles.TextListDropDownStyle)
            di = di.listItems
            di.add('None', True, '')
            di.add('pyBullet', False, '')
            di.add('rviz', False, '')
            di.add('Gazebo', False, '')
            di.add('MoveIt', False, '')

            # Make a button to preview the hierarchy 
            btn = inputs.addBoolValueInput('preview', 'Preview Links', False)
            btn.isFullWidth = True

            # Create tab input
            tab_input = inputs.addTabCommandInput('tab_preview', 'Preview Tabs')
            tab_input_child = tab_input.children
            # Create group
            input_group = tab_input_child.addGroupCommandInput("preview_group", "Preview")
            textbox_group = input_group.children

            # Create a textbox.
            txtbox = textbox_group.addTextBoxCommandInput('jointlist', 'Joint List', '', 8, True)
            txtbox.isFullWidth = True

            # Make a button specifically to generate based on current settings 
            btn = inputs.addBoolValueInput('generate', 'Generate', False)
            btn.isFullWidth = True


        except:
            if self.ui:
                self.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def config_settings(ui: adsk.core.UserInterface, ui_handlers) -> bool:
    '''[summary]

    Parameters
    ----------
    ui : adsk.core.UserInterface
        part of the autodesk UI
    ui_handlers : List
        empty list to hold reference

    Returns
    -------
    bool
        success or failure
    '''

    try:
        commandId = 'Joint Configuration Descriptor'
        commandDescription = 'Settings to describe a URDF file'
        commandName = 'URDF Description App'

        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(commandId, commandName, commandDescription)

        onCommandCreated = MyCreatedHandler(ui, ui_handlers)
        cmdDef.commandCreated.add(onCommandCreated)
        ui_handlers.append(onCommandCreated)

        cmdDef.execute()

        adsk.autoTerminate(False)

        return True 

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        return False
