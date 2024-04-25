import math

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3




from player import Player

from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, GeomNode, Vec3, Vec4, TextureStage, Texture, SamplerState, CullFaceAttrib
import os
import random
import copy

from direct.stdpy import threading
from pandac.PandaModules import WindowProperties


import noise



def n_gonal_prism(engine, x, y, z, n, radius, height):
    #the prism will have its basis centered at x, y,z

    format = GeomVertexFormat.getV3n3c4t2()
    vdata = GeomVertexData("vertex_data", format, Geom.UHStatic)

    vertex_writer = GeomVertexWriter(vdata, "vertex")
    #color_writer = GeomVertexWriter(vdata, "color")
    #normal_writer = GeomVertexWriter(vdata, "normal")
    texcoord_writer = GeomVertexWriter(vdata, "texcoord")
    #r = random.random(), random.random(), random.random()

    angle_dist = 2*math.pi/n 
    for i in range(n):
        angle = angle_dist * i

        vx, vy = x + math.cos(angle) * radius, y + math.sin(angle) * radius

        vertex_writer.addData3f(vx, vy, z)
        vertex_writer.addData3f(vx, vy, z + height)
        #add random color
        
        #color_writer.addData4f(*r, 1)

        #color_writer.addData4f(*r, 1)

        #text_x, text_y = (math.cos(angle) + 1)/2, (math.sin(angle) + 1)/2 
        #texcoord_writer.addData2f(text_x, text_y)

    
    #vertex_writer.addData3f(x, y, z)
    vertex_writer.addData3f(x, y, z + height)
    #color_writer.addData4f(*r, 1)

    #color_writer.addData4f(*r, 1)

    
    tris = GeomTriangles(Geom.UHStatic)


    n2 = 2*n
    for i in range(n - 1):
        vertex_index = i * 2

        tris.addVertex((vertex_index + 2) )
        tris.addVertex((vertex_index + 1))
        tris.addVertex(vertex_index)   
        tris.closePrimitive()

        tris.addVertex((vertex_index + 1))
        tris.addVertex((vertex_index + 2))  
        tris.addVertex((vertex_index + 3))
        tris.closePrimitive()



    
    #ultima iteraz
    tris.addVertex(0)
    tris.addVertex(n2-1)
    tris.addVertex(n2-2)   
    tris.closePrimitive()

    tris.addVertex(n2-1)
    tris.addVertex(0)  
    tris.addVertex(1)
    tris.closePrimitive()

    #texture mapping
    for i in range(n):
        for h in range(2):
            for k in range(2):
                texcoord_writer.addData2f(k, h)

    """
    #base and roof
    for i in range(n - 1):
        even = i * 2

        tris.addVertex(even)
        tris.addVertex(n2)
        tris.addVertex((even + 2) )
        tris.closePrimitive()

        even += 1 #now odd lol
        tris.addVertex(n2 + 1)
        tris.addVertex(even)
        tris.addVertex((even + 2))
        
        tris.closePrimitive()
    
    #ultima iteraz
    tris.addVertex(n2 - 2)
    tris.addVertex(n2)
    tris.addVertex(0)
    tris.closePrimitive()

    tris.addVertex(n2 + 1)
    tris.addVertex(n2 - 1)
    tris.addVertex(1)
    
    tris.closePrimitive()
    """

    for i in range(n - 1):
        vertex = i * 2 + 1
        tris.addVertex(n2)
        tris.addVertex(vertex)
        tris.addVertex(vertex + 2)
        tris.closePrimitive()
    
    tris.addVertex(n2)
    tris.addVertex(n2 - 1)
    tris.addVertex(1)
    tris.closePrimitive()



    geom = Geom(vdata)
    geom.addPrimitive(tris)

    # Create a GeomNode to hold the geometry
    terrain_node = GeomNode("prism")
    terrain_node.addGeom(geom)


    

    np = engine.render.attachNewNode(terrain_node)

    # Apply the texture to the geometry
    for i in range(n):
        tex_stage = TextureStage("texture_stage")
        np.setTexture(tex_stage, engine.textures["building (modern)1w"])
        #np.setTexScale(tex_stage, 1, 1)


    #np.setTexture(tex_stage, engine.textures["road" + "0"])

    # Set texture coordinates for the texture stage
    #np.setTexScale(tex_stage, 1, 1)  # Set texture scale to match the geometry size



    
    #np.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MNone))

    return [np]



def is_buildingFunc(chunk_x, chunk_y, W, H, x, y, w ,h):
    X = chunk_x % W
    Y = chunk_y % H

    if x <= X < x + w and y <= Y < y + h:
        return True
    return False

def is_buildingFunc2(chunk_x, chunk_y, W, H, x, y, w ,h):
    X = chunk_x % W
    Y = chunk_y % H

    if x <= X * Y < x + w and y <= X * Y < y + h:
        return True
    

    X = W - X
    Y = H - Y

    if x <= X * Y < x + w and y <= X * Y < y + h:
        return True

    return False


def _couple_to_index(x, y):
    return int( (x+y)*(x+y+1)/2 + x )

def g(n):
    if n > 0:
        return 2*n - 1
    return -2 * n

def couple_to_index(x, y):
    return _couple_to_index(g(x), g(y))


class ChunkManager:
    def __init__(self, engine, chunk_size, chunk_grid_n):
        self.engine = engine
        self.chunk_size = chunk_size
        self.chunk_grid_n = chunk_grid_n

        self.loaded_chunks = {}
    
    def load_chunk_at(self, start_x, start_y): #start_x, start_y is the upper left corner of the chunk
        format = GeomVertexFormat.getV3c4t2()
        vdata = GeomVertexData("vertex_data", format, Geom.UHStatic)

        


        chunk_x = start_x // self.chunk_size
        chunk_y = start_y // self.chunk_size

        is_building = chunk_x % 2 == 0 and chunk_y % 2 == 0
        #is_building = is_buildingFunc2(chunk_x, chunk_y, 10, 10, 2, 2, 8, 8)

        if is_building:
            random.seed(couple_to_index(chunk_x, chunk_y))

            perlin = (noise.pnoise2(start_x/500,start_y/500, octaves = 8) + 1)**4 * 200

            assert not (perlin < 0)
            
            return n_gonal_prism(self.engine, start_x + self.chunk_size/2, start_y + self.chunk_size/2, 0, random.randint(4, 6), self.chunk_size/3, random.randint(50, 500))

        else:
            vertex_writer = GeomVertexWriter(vdata, "vertex")
            #color_writer = GeomVertexWriter(vdata, "color")
            texcoord_writer = GeomVertexWriter(vdata, "texcoord")

            SIDE_SIZE = 2

            #create a chunk_size * chunk_size plane with 16 vertices
            for y in range(SIDE_SIZE):
                for x in range(SIDE_SIZE):
                    vertex_x = start_x + x * self.chunk_size/float(SIDE_SIZE - 1)
                    vertex_y = start_y + y * self.chunk_size/float(SIDE_SIZE - 1)
                    elevation = noise.pnoise2(vertex_x/50,vertex_y/50, 1, 1) * 100

                    vertex_writer.addData3f(vertex_x, vertex_y, 0)
                    #color_writer.addData4f(0, 1, 0, 1)
                    texcoord_writer.addData2f(x / float(SIDE_SIZE - 1), y / float(SIDE_SIZE - 1))
            
            #connect vertices
            tris = GeomTriangles(Geom.UHStatic)

            for y in range(SIDE_SIZE - 1):
                for x in range(SIDE_SIZE - 1):
                    # Define the indices of the vertices for each triangle
                    vertex_index = y * SIDE_SIZE + x
                    tris.addVertex(vertex_index)
                    tris.addVertex(vertex_index + 1)
                    tris.addVertex(vertex_index + SIDE_SIZE)
                    tris.closePrimitive()

                    tris.addVertex(vertex_index + 1)
                    tris.addVertex(vertex_index + SIDE_SIZE + 1)
                    tris.addVertex(vertex_index + SIDE_SIZE)
                    tris.closePrimitive()
            
            #shapes: 0 -> |; 1 -> -; 2 -> +
            if chunk_y % 2 == 0:
                shape = 0
            else:
                if chunk_x % 2 == 0:
                    shape = 1
                else: shape = 2
            
            


            # Create a Geom and attach the triangles to it
            geom = Geom(vdata)
            geom.addPrimitive(tris)

            # Create a GeomNode to hold the geometry
            terrain_node = GeomNode("terrain")
            terrain_node.addGeom(geom)


            # Apply the texture to the geometry
            tex_stage = TextureStage("texture_stage")
            np = self.engine.render.attachNewNode(terrain_node)
            np.setTexture(tex_stage, self.engine.textures["road" + str(shape)])

            # Set texture coordinates for the texture stage
            np.setTexScale(tex_stage, 1, 1)  # Set texture scale to match the geometry size

            return [np]
    

    def update(self):
        player_chunk_x = self.engine.player.x // self.chunk_size
        player_chunk_y = self.engine.player.y // self.chunk_size

        #TODO iterazione a serpentina
        this_iteration_chunks = []
        for grid_y in range(self.chunk_grid_n):
            for grid_x in range(self.chunk_grid_n):
                new_chunk_x = player_chunk_x - self.chunk_grid_n // 2 + grid_x
                new_chunk_y = player_chunk_y - self.chunk_grid_n // 2 + grid_y

                this_iteration_chunks.append((new_chunk_x, new_chunk_y))

                if (new_chunk_x, new_chunk_y) not in self.loaded_chunks:
                    self.loaded_chunks[(new_chunk_x, new_chunk_y)] = self.load_chunk_at(new_chunk_x * self.chunk_size, new_chunk_y * self.chunk_size)
        
        for key in copy.copy(self.loaded_chunks):
            if not key in this_iteration_chunks:
                try:
                    for np in self.loaded_chunks[key]:
                        np.removeNode()

                    self.loaded_chunks.pop(key)
                except:
                    print("could not delete chunk")




class Engine(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        

        # Disable the camera trackball controls.
        self.disableMouse()
        self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)

        self.is_paused = False

        # Accept key events
        self.accept('w', self.keyPressed, ['w'])
        self.accept('a', self.keyPressed, ['a'])
        self.accept('s', self.keyPressed, ['s'])
        self.accept('d', self.keyPressed, ['d'])
        self.accept('space', self.keyPressed, ['space'])
        self.accept('shift', self.keyPressed, ['shift'])
        self.accept('escape', self.keyPressed, ['escape'])

        self.accept('w-up', self.keyReleased, ['w'])
        self.accept('a-up', self.keyReleased, ['a'])
        self.accept('s-up', self.keyReleased, ['s'])
        self.accept('d-up', self.keyReleased, ['d'])
        self.accept('space-up', self.keyReleased, ['space'])
        self.accept('shift-up', self.keyReleased, ['shift'])
        self.accept('escape-up', self.keyReleased, ['escape'])

        self.key_states = {
            'w': False,
            'a': False,
            's': False,
            'd': False,
            'space': False,
            'shift': False,
            'escape': False
        }


        #load textures
        self.textures = {}

        for foldername in os.listdir("textures"):
            for filename in os.listdir("textures/" + foldername):
                if filename.endswith(".png"):
                    texture = self.loader.loadTexture("textures/" + foldername + "/" + filename)
                    self.textures[foldername + filename.replace(".png", "")] = texture
                    # Apply nearest neighbor filtering to the texture
                    texture.setMagfilter(SamplerState.FT_nearest)
                    texture.setMinfilter(SamplerState.FT_nearest)

        
        print(self.textures)

        self.player = Player(0, 0, 10, (0, 0, 0))

        self.chunk_manager = ChunkManager(self, 100, 30)

        #start thread for chunk updates
        self.chunk_update_thread = threading.Thread(target=self.chunk_update_thread)
        self.chunk_update_thread.start()

        self.taskMgr.add(self.update, "Update")

    # Define a procedure to move the camera.
    def update(self, task):
        if self.is_paused:
            return Task.cont
        # Calculate the time elapsed since the last frame.
        delta_time = self.taskMgr.globalClock.get_dt()

        #get mouse position
        md = self.win.getPointer(0)
        mouse_x = md.getX()
        mouse_y = md.getY()
        self.player.input_process(self.key_states, delta_time = delta_time * 600 * 10)
        self.player.hpr = (self.player.hpr[0] - (mouse_x - self.win.getXSize() // 2) * 0.1,  self.player.hpr[1] - (mouse_y - self.win.getYSize() // 2) * 0.1,0)


        self.camera.setPos(self.player.x, self.player.y, self.player.z + 2)
        self.camera.setHpr(self.player.hpr[0], self.player.hpr[1], self.player.hpr[2])

        self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)


        #update fps on window title
        props = WindowProperties()
        props.setTitle(f"FPS: {round(self.taskMgr.globalClock.get_average_frame_rate())}")
        self.win.requestProperties(props)

        return Task.cont


    def keyPressed(self, key):
        # Update key state on key press
        self.key_states[key] = True

    def keyReleased(self, key):
        # Update key state on key release
        if key == "escape":
            self.is_paused = not self.is_paused
            self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)

        self.key_states[key] = False

    def chunk_update_thread(self):
        while True:
            self.chunk_manager.update()
            threading.Event().wait(0.1)

app = Engine()
app.run()