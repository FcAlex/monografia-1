import bpy
import math

''' ------------------ DATA STRUCTURES: ------------------ '''

class Node(object):
    # Attributes 'label' and 'object' are required for every node:
    def __init__(self, label, object, dimX=0, dimY=0, dimZ=0):
        # Object label
        self.label = label
        # Object itself: 
        self.obj = object
        # Subshapes:
        self.children = []
        # Dimensions:
        self.dimX = dimX
        self.dimY = dimY
        self.dimZ = dimZ
        
    def addChild(self, object):
        self.children.append(object)
        
    def descendant(self, label):
        for child in self.children:
            if child.label == label:
                return child
    
    def getDimX(self):
        return self.dimX
    
    def getDimY(self):
        return self.dimY
    
    def getDimZ(self):
        return self.dimZ
    
    def getPolygon(self, index):
        return self.obj.data.polygons[index]
    
    def getEdges(self):
        return self.obj.data.edges
        
########################################################################

''' ------------------ FUNCTIONS: ------------------ '''

'''Creates initial 3D Mass (root node):'''

def create3DMass(label, width, depth, height):
    # Creating primitive object:
    bpy.ops.mesh.primitive_cube_add()
    
    # Selecting created object:
    bpy.data.objects["Cube"].select_set(True)
    
    # Storing reference to object:
    mass = bpy.context.selected_objects[0]
    
    # Changing name attribute to label:
    mass.name = label
    
    # Setting object dimensions:
    bpy.ops.transform.resize(value=(width/2, depth/2, height/2))
    
    bpy.data.objects[label].select_set(False)
    
    return mass

'''Utility functions for grid generation:'''

def vert(x, y, sizeRows, sizeColumns):
    # Create a single vert:
    return (x * sizeColumns, y * sizeRows, 0)

def face(x, y, rows):
    # Create a single face:
    return (x * rows + y,
           (x + 1) * rows + y,
           (x + 1) * rows + 1 + y,
           x * rows + 1 + y)

'''Creates virtual shape:'''

def createGrid(label, width, height, rows, columns):
    # Changing for desired number of rows and columns:
    rows += 1
    columns += 1
    
    # Calculating size of the cells:
    sizeRows = (width/2) / ((columns-1) / 2)
    sizeColumns = (height/2) / ((rows-1) / 2)

    # Looping to create the grid:
    verts = [vert(x, y, sizeRows, sizeColumns) for x in range(rows) for y in range(columns)]
    faces = [face(x, y, columns) for x in range(rows - 1) for y in range(columns - 1)]

    # Create Mesh Datablock:
    mesh = bpy.data.meshes.new(label)
    mesh.from_pydata(verts, [], faces)

    # Create Object and link to scene:
    obj = bpy.data.objects.new(label, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Select the object:
    bpy.context.view_layer.objects.active = obj
    bpy.data.objects[label].select_set(True)

    # Moves object origin to its center:
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Move 3D cursor to scene origin:
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)

    # Move shape origin to scene origin: 
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()
            override['area'] = area
            override['region'] = area.regions[4]
            bpy.ops.view3d.snap_selected_to_cursor(override, use_offset=False)
    
    bpy.data.objects[label].select_set(False)
    
    return mesh

########################################################################

''' ---------------------- RESETING THE SCENE: ---------------------- '''
    
if len(bpy.context.scene.objects) > 0:
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

########################################################################

''' ------------------ SIMULATING SELEX RULES: ------------------ '''

'''C1: Initial settings:'''

label = "building"
width = 9
depth = 11
height = 5

'''C2: {<> -> createShape("building", height, width, depth)};'''

mass3D = create3DMass(label, width, depth, height)

# Defining shape tree root node:
root = Node("root", None)

# Adding building mass node:
root.addChild(Node(label, mass3D, width, depth, height))

# Retrieving root node descendant by label:
building = root.descendant("building")

# Configuring object mode:
bpy.ops.object.mode_set(mode = "EDIT")
bpy.ops.mesh.select_all(action = "DESELECT")
bpy.ops.object.mode_set(mode = "OBJECT")

# Creating nodes with object faces:
front = Node(building.label + "_" + "front", building.getPolygon(3), building.getDimX(), 0, building.getDimZ())
left = Node(building.label + "_" + "left", building.getPolygon(0), building.getDimY(), 0, building.getDimZ())
right = Node(building.label + "_" + "right", building.getPolygon(2), building.getDimY(), 0, building.getDimZ())
back = Node(building.label + "_" + "back", building.getPolygon(1), building.getDimX(), 0, building.getDimZ())

# Adding front, back, left and right faces as children:
building.addChild(front)
building.addChild(left)
building.addChild(right)
building.addChild(back)

# Reseting object mode:
bpy.ops.object.mode_set(mode = "EDIT")
bpy.ops.mesh.select_all(action = "DESELECT")
bpy.ops.object.mode_set(mode = "OBJECT")

'''C3: {<[label=="building_front"]> 
       -> createGrid("facade", 4, 4)};'''
    
frontFace = building.descendant("building_front")

# Retrieving face dimensions:
faceWidth = frontFace.getDimX()
faceHeight = frontFace.getDimZ()

# DEBUG - Printing dimensions:
print("FACE DIMENSIONS: ", faceWidth, faceHeight)

# Defining number of rows and columns of the grid:
rows = 3
columns = 5

label = "facade"

# Using face dimensions to generate grid:
virtualShape = createGrid(label, int(faceWidth), int(faceHeight), rows, columns)

# Adding virtual shape as child of building_front:
frontFace.addChild(Node(label, virtualShape))

# Retriving object from shape tree:
facade = frontFace.descendant(label)

# Positioning virtual shape over appropriate face:

# Always rotate 90 degrees at x-axis:
bpy.context.object.rotation_euler[0] = 1.5708

# Rotating grid to fit over the face appropriately:
bpy.context.object.rotation_euler[1] = 1.5708

# If it's 'front' or 'back' face, just update location at y-axis appropriately:

## Inverting the sign is needed for 'front' location:
bpy.context.object.location[1] = (-building.getDimY()) / 2

## For 'back' location:
# bpy.context.object.location[1] = building.getDimY() / 2

# If it's 'left' or 'right' face:

## Perform a rotation by 90 degrees at z-axis:
# bpy.context.object.rotation_euler[2] = 1.5708

## Inverting the sign is needed for 'left' location:
# bpy.context.object.location[0] = (-building.getDimX()) / 2

## For 'right' location:
# bpy.context.object.location[0] = building.getDimX() / 2

'''C4: {<descendant()[label=="building"] / 
                     [label=="building_front"] / 
                     [label=="facade"] / 
                     [type=="cell"] 
                     [rowIdx in (3, 4)] 
                     [colIdx in (1, 2)> 
                     -> addVolume("entrance", "building_front", 1, ["ef", "el", "er"])};'''

# Selection by rows and columns indexes:

## Selection settings:
rowsIndex = [2, 3]
columnsIndex = [1, 2]

# Shape tree labels:
facade = "facade"
parent = "bulding_front"
label = "region"

## Finding row and column indexes for a specific cell (using its polygon index):

# idxRow = (cellIndex / columns) + 1
# idxColumn = (cellIndex / rows) + 1

## Finding cells corresponding to 'rowsIndex' and 'columnsIndex':

# (columns * rowIndex) - columns + (columnIndex - 1)

# Used to store the conversion from row and column indexes to face index:
selectedCells = []

for rowIndex in rowsIndex:
    for columnIndex in columnsIndex:
        cellIndex = (columns * rowIndex) - columns + (columnIndex - 1)
        selectedCells.append(cellIndex)

# DEBUG: Printing selected indexes:      
print("SELECTED CELLS: ", selectedCells)

# Changing object mode:
bpy.ops.object.mode_set(mode = 'OBJECT')

## Deselect everything:
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action = 'DESELECT')

bpy.ops.object.mode_set(mode = 'OBJECT')

# Looping through selectedCells in order to select each one:
for cell in selectedCells:    
    # Setting each cell select status to True:
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.data.objects[facade].data.polygons[cell].select = True
    bpy.ops.object.mode_set(mode = 'EDIT')
        
# Changing select mode:
bpy.ops.mesh.select_mode(type='FACE')

# Separate selected subgrid from 'facade' by creating a new form:
bpy.ops.mesh.separate(type='SELECTED')

# Storing reference to region (to be used for extrusion from building):
region = bpy.context.selected_objects[0]

# Changing name attribute to label:
region.name = label

# Adding 'region' as child of 'building_front': (THE CHILD WILL BE ENTRANCE)
frontFace.addChild(Node(label, region))

# Changing to object mode:
bpy.ops.object.mode_set(mode = "OBJECT")

# Moving object's origin to its center:
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

# Creating unliked copy to be used as virtual shape of 'entrance':
bpy.ops.object.duplicate()

# AFTER EXTRUSION CHANGE PARENT TO parentName.001...
# Renaming virtual shape appropriately:
entranceGrid = bpy.data.objects[label + ".001"]

# Renaming virtual shape:
entranceGrid.name = label + "_grid"

# Retrieving 'entrance' node:
region = frontFace.descendant("region")

# AFTER EXTRUSION CHANGE PARENT TO entrance_front...
# Adding virtual shape as 'entrance' child:
region.addChild(Node(entranceGrid.name, entranceGrid))

# Deselecting object:
bpy.data.objects[entranceGrid.name].select_set(False)

# Selecting object to dissolve internal edges:
bpy.data.objects[label].select_set(True)

# Changing object mode:
bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.mode_set(mode = 'EDIT')

# Selecting all the faces:
bpy.ops.mesh.select_all(action = 'SELECT')

# Changing object mode:
bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.mode_set(mode = 'EDIT')

# Selecting faces of the object by it's index (unnecessary):
#bpy.data.objects[label].data.polygons[0].select = True
#bpy.data.objects[label].data.polygons[1].select = True
#bpy.data.objects[label].data.polygons[2].select = True
#bpy.data.objects[label].data.polygons[3].select = True

# Selecting boundary edges:
bpy.ops.mesh.region_to_loop()

bpy.ops.object.mode_set(mode = 'OBJECT')

# Creating list with all of the object indexes:
ids = list(range(len(region.getEdges())))

# DEBUG: Printing all of the edges indexes:
print("ALL EDGES INDEXES: ", ids)

# Storing just the selected indexes:
selectedEdges = [e.index for e in region.getEdges() if e.select]

# DEBUG: Printing border indexes:
print("BORDER EDGES INDEXES: ", selectedEdges)

# Removing border indexes, so the remaining will be internal:
for e in selectedEdges:
    ids.remove(e)
    
# DEBUG: Printing internal indexes:
print("INTERNAL EDGES INDEXES: ", ids)

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action = 'DESELECT')

bpy.ops.object.mode_set(mode = 'OBJECT')

# Selecting internal edges by index:
for id in ids:
    bpy.data.objects[label].data.edges[id].select = True
    
bpy.ops.object.mode_set(mode = 'EDIT')

# Dissolving internal edges:
bpy.ops.mesh.dissolve_edges()

# Deselecting object:
bpy.data.objects[label].select_set(False)

# DEBUG: building_front number of children:
print("BUILDING_FRONT CHILDREN: ", len(frontFace.children))

bpy.ops.object.mode_set(mode = 'OBJECT')

# Selecting objects to be joined:
bpy.data.objects["region"].select_set(True)

bpy.context.view_layer.objects.active = bpy.data.objects["building"]
bpy.data.objects["building"].select_set(True)

# Joining selected objects ('entrance' will be merged into 'building'):
bpy.ops.object.join()

# Changing object mode:
bpy.ops.object.mode_set(mode = 'EDIT')

# Selecting last object face by its index:
regionIdx = len(building.obj.data.polygons)-1

print("REGION INDEX: ", regionIdx)

bpy.ops.mesh.select_all(action = 'DESELECT')

# Reselect specific face:
bpy.ops.object.mode_set(mode = 'OBJECT')

# Selecting faces of the object by it's index:
bpy.data.objects["building"].data.polygons[regionIdx].select = True

# Extrusion setting (h = height):
extrusionHeight = 2

# Changing object mode:
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_mode(type = 'FACE')

# Applying extrusion:

## Invert value for 'front' and 'left' face extrusion:
bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={"value":(0, -extrusionHeight, 0)}
)

# TO-DO: ORGANIZE SHAPE TREE WITH NEW NODES...

'''C4: {<descendant()[label=="entrance"] / [label=="ef"]> 
       -> roundShape("front", 1.0, "vertical")};'''
       
## Settings: offset = degree of rounding | segments = degree of 'realism'
roundingDegree = 0.365 # vertical
# roundingDegree = 0.365*1.7 # horizontal
numberSegments = 30

# Changing object mode:       
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action = 'DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT')

# Entering edges indexes (just for testing):
# e1 = int(input("Enter first edge: "))
# e2 = int(input("Enter second edge: "))

# Selecting left and right edges from the face (round front - vertical):
## STILL HARDCODED... left = 17 and right = 19
bpy.data.objects["building"].data.edges[17].select = True
bpy.data.objects["building"].data.edges[19].select = True

# Changing object mode:
bpy.ops.object.mode_set(mode = 'EDIT')

# Applying (front - vertical) deformation itself:
bpy.ops.mesh.bevel(offset=roundingDegree, offset_pct=0, segments=numberSegments, vertex_only=False)

bpy.ops.object.mode_set(mode = 'OBJECT')

# OR

# Selecting top and bottom edges from the face (round front - horizontal):
## TO-DO

# Changing object mode:
# bpy.ops.object.mode_set(mode = 'EDIT')

# Applying (front - horizontal) deformation itself:
# bpy.ops.mesh.bevel(offset=roundingDegree, offset_pct=0, segments=numberSegments, vertex_only=False)

# OR

# Selecting left edge from the face (round left):
## TO-DO

# Changing object mode:
# bpy.ops.object.mode_set(mode = 'EDIT')

# Applying (left) deformation itself:
# bpy.ops.mesh.bevel(offset=roundingDegree, offset_pct=0, segments=numberSegments, vertex_only=False)

# OR

# Selecting right edge from the face (round right):
## TO-DO

# Changing object mode:
# bpy.ops.object.mode_set(mode = 'EDIT')

# Applying (right) deformation itself:
# bpy.ops.mesh.bevel(offset=roundingDegree, offset_pct=0, segments=numberSegments, vertex_only=False)

# OR

# Selecting top edge from the face (round top):
## TO-DO

# Changing object mode:
# bpy.ops.object.mode_set(mode = 'EDIT')

# Applying (top) deformation itself:
# bpy.ops.mesh.bevel(offset=roundingDegree, offset_pct=0, segments=numberSegments, vertex_only=False)

# OR

# Selecting bottom edge from the face (round bottom):
## TO-DO

# Changing object mode:
# bpy.ops.object.mode_set(mode = 'EDIT')

# Applying (bottom) deformation itself:
# bpy.ops.mesh.bevel(offset=roundingDegree, offset_pct=0, segments=numberSegments, vertex_only=False)