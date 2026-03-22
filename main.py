import pygame

class Snake:
    def __init__(self):
        pygame.init()

        self.window = pygame.display.set_mode((600,600))
        self.load_images()
        self.scale = self.images[0].get_width()

        icon = pygame.image.load('snake_icon.png')
        pygame.display.set_icon(icon)
        pygame.display.set_caption('Snake')

        self.clock = pygame.time.Clock()

        self.game_font = pygame.font.SysFont('Arial', 24)
        
        
        self.new_game()
        self.main_loop()

    def load_images(self):
        self.images = []
        for name in ['light_green', 'dark_green']:
            self.images.append(pygame.image.load((name + '.png')).convert())
        for name in ['apple_icon', 'snake_head', 'snake_body']:
            self.images.append(pygame.image.load((name + '.png')).convert_alpha())
    
    def grid_to_pixel(self, grid):
        return (90 + (grid[0] * 30), 127 + (grid[1] * 30))

    def pixel_to_grid(self,pixel):
        return ((pixel[0] - 75 + 13) // 30, (pixel[1] - 112 + 13) // 30)

    def new_game(self):
        self.score = 0
        self.game_state = 'playing'
        self.direction = 'right'
        self.pending_direction = None
        self.snake_speed = 2

        self.snake = [{'grid': (3,7), 'pixel': self.grid_to_pixel((3,7))},{'grid':(2,7), 'pixel': self.grid_to_pixel((2,7))}]
        self.apple = [{'grid': (12,7), 'pixel': self.grid_to_pixel((12,7))}]


    def main_loop(self):
        while True:
            self.check_events()
            self.update_game()
            self.draw_window()
            self.clock.tick(60)
        
    def check_events(self):
         for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if self.direction != 'right':
                        self.pending_direction = 'left'
                if event.key == pygame.K_RIGHT:
                    if self.direction != 'left':
                        self.pending_direction = 'right'
                if event.key == pygame.K_UP:
                    if self.direction != 'down':
                        self.pending_direction = 'up'
                if event.key == pygame.K_DOWN:
                    if self.direction != 'up':
                        self.pending_direction = 'down'
                if event.key == pygame.K_r:
                    self.new_game()
                if event.key == pygame.K_ESCAPE:
                        exit()
            if event.type == pygame.QUIT:
                exit()
    def move_snake(self):
        old_grid = self.snake[0]['grid']
        
        # CHECK FOR DIRECTION CHANGE FIRST (before moving!)
        new_grid_check = self.pixel_to_grid(self.snake[0]['pixel'])
        if old_grid != new_grid_check and self.pending_direction is not None:
            self.direction = self.pending_direction
            self.pending_direction = None
        
        # NOW move the head with the correct direction
        directions = ['right', 'left','down','up']
        moves = [(self.snake_speed,0), (-self.snake_speed,0), (0,self.snake_speed), (0,-self.snake_speed)]
        
        head = self.snake[0]['pixel']
        index = directions.index(self.direction)
        self.snake[0]['pixel'] = (head[0] + moves[index][0], head[1] + moves[index][1])
        self.snake[0]['grid'] = self.pixel_to_grid(self.snake[0]['pixel'])
        
        # Body segments follow
        for i in range(1, len(self.snake)):
            target = self.snake[i-1]['pixel']
            current = self.snake[i]['pixel']
            
            dx = target[0] - current[0]
            dy = target[1] - current[1]
            distance = (dx**2 + dy**2) ** 0.5 
            
            if distance > 0:
                move_x = (dx / distance) * self.snake_speed
                move_y = (dy / distance) * self.snake_speed
                
                self.snake[i]['pixel'] = (current[0] + move_x, current[1] + move_y)
                self.snake[i]['grid'] = self.pixel_to_grid(self.snake[i]['pixel'])

    def check_collisions(self):
        head_grid = self.snake[0]['grid']
        if head_grid[0] < 0 or head_grid[0] >= 15 or head_grid[1] < 0 or head_grid[1] >= 15:
            self.game_over()
        
        for s in self.snake[1:]:
            if head_grid == s['grid']:
                self.game_over()

    def game_over(self):
        self.game_state = 'lost'
    def game_won(self):
        self.game_state = 'won'

    def update_game(self):
        if self.game_state != 'playing':
            return
        self.move_snake()
        self.check_collisions()

    def draw_tiles(self):
        for y in range (15):
            for x in range(15):
                if (y + x) % 2 == 0:
                    self.window.blit(self.images[0], (75 + self.scale * y, 112 + self.scale * x))
                else:
                    self.window.blit(self.images[1], (75 + self.scale * y, 112 + self.scale * x))

    def draw_snake(self):
        pixel = self.snake[0]['pixel']
        pygame.draw.circle(self.window,('royal blue'), pixel, 13)
        if self.direction == 'right':
            pygame.draw.circle(self.window,('white'), (pixel[0] + 5,pixel[1]+5), 5)
            pygame.draw.circle(self.window,('white'), (pixel[0] + 5,pixel[1]-5), 5)
            pygame.draw.circle(self.window,('black'), (pixel[0] + 5,pixel[1]+5), 3)
            pygame.draw.circle(self.window,('black'), (pixel[0] + 5,pixel[1]-5), 3)
        elif self.direction == 'left':
            pygame.draw.circle(self.window,('white'), (pixel[0] - 5,pixel[1]+5), 5)
            pygame.draw.circle(self.window,('white'), (pixel[0] - 5,pixel[1]-5), 5)
            pygame.draw.circle(self.window,('black'), (pixel[0] - 5,pixel[1]+5), 3)
            pygame.draw.circle(self.window,('black'), (pixel[0] - 5,pixel[1]-5), 3)
        elif self.direction == 'up':
            pygame.draw.circle(self.window,('white'), (pixel[0] + 5,pixel[1]-5), 5)
            pygame.draw.circle(self.window,('white'), (pixel[0] - 5,pixel[1]-5), 5)
            pygame.draw.circle(self.window,('black'), (pixel[0] + 5,pixel[1]-5), 3)
            pygame.draw.circle(self.window,('black'), (pixel[0] - 5,pixel[1]-5), 3)
        elif self.direction == 'down':
            pygame.draw.circle(self.window,('white'), (pixel[0] + 5,pixel[1]+5), 5)
            pygame.draw.circle(self.window,('white'), (pixel[0] - 5,pixel[1]+5), 5)
            pygame.draw.circle(self.window,('black'), (pixel[0] + 5,pixel[1]+5), 3)
            pygame.draw.circle(self.window,('black'), (pixel[0] - 5,pixel[1]+5), 3)
        p1,p2 = 0,1
        while p2 < len(self.snake):
            pixel1, pixel2 = self.snake[p1]['pixel'], self.snake[p2]['pixel']
            pygame.draw.circle(self.window,('royal blue'), pixel2, 13)
            if pixel1[1] == pixel2[1]:
                pygame.draw.rect(self.window,('royal blue'), (min(pixel1[0],pixel2[0]),pixel1[1]-14, 30,28))
            else:
                pygame.draw.rect(self.window,('royal blue'), (pixel1[0]-14, min(pixel1[1],pixel2[1]), 28, 30))
            p1 += 1; p2 += 1
            

    def lost(self):
        self.window.fill(('white'))
        game_text = self.game_font.render('Press r to RESTART', True, ('black'))
        self.window.blit(game_text, (300-(game_text.get_width()//2), 300-(game_text.get_height()//2)))
    def won(self):
        self.window.fill(('white'))
        game_text = self.game_font.render('You won! press r to restart', True, ('black'))
        self.window.blit(game_text, (300-(game_text.get_width()//2), 300-(game_text.get_height()//2)))

    def draw_window(self):
        self.window.fill((74, 117, 44))
        pygame.draw.rect(self.window,(87, 138, 52), (0, 70, 600, 530))
        width = self.images[2].get_width(); apple = pygame.transform.scale(self.images[2], (width + 10, width+10))
        self.window.blit(apple, (25,10))
        self.draw_tiles()
        self.draw_snake()

        if self.game_state == 'lost':
            self.lost()
        if self.game_state == 'won':
            self.won()
        pygame.display.flip()


        


if __name__ == '__main__':
    snake = Snake()