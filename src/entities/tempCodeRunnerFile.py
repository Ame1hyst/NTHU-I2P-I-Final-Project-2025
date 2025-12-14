    def update(self, dt: float) -> None:
        #Input walk
        dis = Position(0, 0)
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1
        
        #Normalize
        length = (dis.x**2 + dis.y**2)**(0.5)
        if length:
            dis.x, dis.y = dis.x/length, dis.y/length

        #Calculate
        self.x += dis.x*self.speed*dt
        if Map.check_collision():
            Entity._snap_to_grid()