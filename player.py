import math

class Player:
    def __init__(self, x ,y , z, hpr):
        self.x = x
        self.y = y
        self.z = z
        self.hpr = hpr
        self.speed = 0.1

    def move(self, x, y, z):
        self.x += x
        self.y += y
        self.z += z
    
    def rotated_vec(self, x, y, z):
        # Get vector rotated by hpr
        rot_mat = [
            [math.cos(math.radians(self.hpr[0])), -math.sin(math.radians(self.hpr[0]))],
            [math.sin(math.radians(self.hpr[0])), math.cos(math.radians(self.hpr[0]))]
        ]
        return (rot_mat[0][0] * x + rot_mat[0][1] * y, rot_mat[1][0] * x + rot_mat[1][1] * y, z)

    def input_process(self, key_states, delta_time):
        xaxis = int(key_states['d']) - int(key_states['a'])
        yaxis = int(key_states['w']) - int(key_states['s'])
        zaxis = int(key_states['space']) - int(key_states['shift'])
        # Normalize the vector
        n = math.sqrt(xaxis ** 2 + yaxis ** 2 + zaxis ** 2)
        if n == 0:
            return
        norm = self.speed / n
        xaxis *= norm
        yaxis *= norm
        zaxis *= norm
        # Z axis later
        # Rotate axes based on hpr
        xaxis, yaxis, zaxis = self.rotated_vec(xaxis, yaxis, zaxis)
        # Move the player
        self.move(xaxis * delta_time, yaxis * delta_time, zaxis * delta_time)


    def forward(self, step):
        #move the player forward by step units in its hpr direction
        self.x += step * math.sin(math.radians(self.hpr[0]))
        self.y += step * math.cos(math.radians(self.hpr[0]))
