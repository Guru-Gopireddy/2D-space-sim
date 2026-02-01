import pygame
import pygame_gui
import math

UNITS = { # Seconds per each unit
    "year": 31536000,
    "month": 2592000,
    "day": 86400,
    "hour": 3600,
    "minute": 60,
    "second": 1
}

# man i hate commenting code - 8/15/2025

AU = 1.495978707e11            # meters per astronomical unit
EARTH_MASS = 5.9722e24         # masses for all objects will be in terms of earth masses
G = 6.67430e-11                # constant of gravity
EPS = (0.005 * AU)**2          # epsilon so weird stuff doesn't happen
SCALE = 100                    # pixels per AU
TIME_SCALE = 1                 # seconds simulated per real second
LIGHT_GREY = 0xD3D3D3

display_velocity_vectors = True
show_graph_axises = True

pygame.init()
FONT = pygame.font.SysFont("Bahnschrift", 25)
h, w = 720, 1280
screen = pygame.display.set_mode((w, h))
manager = pygame_gui.UIManager((w, h))
clock = pygame.time.Clock()
FRAMERATE_CAP = 60


def secondsToTimeString(seconds: int, sep: str = " "):
    time: str = []
    for unit, delta in UNITS.items():
        if seconds >= delta:
            time.append(f"{seconds//delta} {unit}")
            seconds %= delta
    parsedTimeStr = ""
    i = 0
    for value in time:
        delta = value.split(" ")[0]
        if int(delta) > 1:
            value += "s"
        i += 1
        parsedTimeStr += value + sep
    if parsedTimeStr.lower() == "1 second, ":
        return "Real time"
    return parsedTimeStr[:-len(sep)] + " per second"

class SimSpeedPopup(pygame_gui.elements.UIWindow):
    active = False
    def __init__(self, rect, manager):
        super().__init__(rect, manager, window_display_title='Set simulation speed')
        self.LABELS_DATA = { # Instead of manually typing out every label property, I thought it would be nice to have a dictionary of data and use a for loop to dynamically create the labels and text entries. 
            "label": [(9, 0), (210, 30), "Enter a new simulation speed"],
            "Years": [(10, 25), (50, 30), (70, 25), (85, 30)],
            "Months": [(12, 55), (55, 30), (70, 55), (85, 30)],
            "Days": [(6, 85), (55, 30), (70, 85), (85, 30)],
            "Hours": [(10, 115), (55, 30), (70, 115), (85, 30)],
            "Minutes": [(10, 145), (60, 30), (70, 145), (85, 30)],
            "Seconds": [(10, 175), (60, 30), (70, 175), (85, 30)]
        }
        self.labels = {}
        self.text_entries = {}
        for name, data in self.LABELS_DATA.items():
            text = f"{name}: "
            if name == "label":
                text = data[2]
            self.labels[name] = pygame_gui.elements.UILabel(
                pygame.Rect(data[0], data[1]),
                text=text,
                manager=manager,
                container=self
            )
            if name == "label":
                continue
            self.text_entries[name] = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(data[2], data[3]),
                manager=manager,
                container=self
            )
        self.labels["enter"] = pygame_gui.elements.UIButton(
            pygame.Rect((0, 280), (250, 40)),
            text="Set new speed",
            manager=manager,
            container=self
        )

class AddPlanetPopup(pygame_gui.elements.UIWindow):
    active = False
    def __init__(self, rect, manager):
        super().__init__(rect, manager, window_display_title='Add new planet')
        self.LABELS_DATA = { # Same thing as SimSpeedPopup here
            "Mass": ["Mass (In Earth masses): ", (10, 5), (165, 30), (170, 5), (85, 30)],
            "Radius": ["Radius of planet (In AUs): ", (10, 35), (165, 30), (170, 35), (85, 30)],
            "X-coord": ["X-coordinate (In AUs): ", (10, 65), (165, 30), (170, 65), (85, 30)],
            "Y-coord": ["Y-coordinate (In AUs): ", (10, 95), (165, 30), (170, 95), (85, 30)],
            "Color": ["Color of the planet: ", (10, 125), (165, 30), (170, 125), (85, 30)],
            "Name": ["Name of the planet: ", (10, 155), (165, 30), (170, 155), (85, 30)],
            "Speed": ["Speed of the planet: ", (10, 185), (165, 30), (170, 185), (85, 30)],
            "Angle": ["Angle of the planet: ", (10, 215), (165, 30), (170, 215), (85, 30)]
        }
        self.labels = {}
        self.text_entries = {}
        for name, data in self.LABELS_DATA.items():
            self.labels[name]= pygame_gui.elements.UILabel(
                pygame.Rect(data[1], data[2]),
                text=data[0],
                manager=manager,
                container=self
            )
            self.text_entries[name] = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(data[3], data[4]),
                manager=manager,
                container=self
            )
        self.labels["create-planet"] = pygame_gui.elements.UIButton(
            pygame.Rect((0, 280), (300, 40)),
            text="Create Planet",
            manager=manager,
            container=self
        )

class CosmicObject:
    def __init__(self, mass, radius_au, x_au, y_au, color, name, speed=0, angle=0):
        self.mass = mass * EARTH_MASS
        self.realRadius = radius_au * AU
        self.radius = max(2, int(radius_au * SCALE))
        self.realX = x_au * AU
        self.realY = y_au * AU

        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))
        self.color = color
        self.name = name

        self.ax = 0.0
        self.ay = 0.0

    def compute_acceleration(self, bodies): 
        ax = ay = 0.0
        for other in bodies:
            if other is self:
                continue
            dx = other.realX - self.realX
            dy = other.realY - self.realY
            r2 = dx*dx + dy*dy + EPS # I don't want to type out delta_x so I wrote dx, even though they're not the same thing technically. Same with dy
            r3 = r2 * math.sqrt(r2)
            ax += G * other.mass * dx / r3
            ay += G * other.mass * dy / r3
        return ax, ay

    def update(self, bodies, dt):
        ax0, ay0 = self.compute_acceleration(bodies) # ChatGPT told me Velocity Verlet was good

        self.realX += self.vx * dt + 0.5 * ax0 * dt*dt
        self.realY += self.vy * dt + 0.5 * ay0 * dt*dt

        ax1, ay1 = self.compute_acceleration(bodies)

        self.vx += 0.5 * (ax0 + ax1) * dt
        self.vy += 0.5 * (ay0 + ay1) * dt

        self.ax = ax1
        self.ay = ay1

    def draw(self, screen):
        px = int(self.realX / AU * SCALE + w/2)
        py = int(self.realY / AU * SCALE + h/2)
        if display_velocity_vectors:
            v_x = px + self.vx/500
            v_y = py + self.vy/500
            # pygame.draw.line(screen, "red", (px, py), (v_x, v_y), width=5)
            pygame.draw.line(screen, "crimson", (px, py), (v_x, py), width=5)
            pygame.draw.line(screen, "cyan", (px, py), (px, v_y), width=5)
            if v_x < px:
                pygame.draw.polygon(screen, "crimson", ((v_x-5, py), (v_x, py-5), (v_x, py+5)), width=5)
            elif v_x > px:
                pygame.draw.polygon(screen, "crimson", ((v_x+5, py), (v_x, py-5), (v_x, py+5)), width=5)
            if v_y < py:
                pygame.draw.polygon(screen, "cyan", ((px, v_y-5), (px-5, v_y), (px+5, v_y)), width=5)
            if v_y > py:
                pygame.draw.polygon(screen, "cyan", ((px, v_y+5), (px-5, v_y), (px+5, v_y)), width=5)
            
        pygame.draw.circle(screen, self.color, (px, py), self.radius)
        

objects = [
    CosmicObject(
        mass=1,         
        radius_au=0.05,
        x_au=-1.0, y_au=0.0,
        color=pygame.Color('Green'),
        name='Earth',
        speed=29780,   
        angle=90
    ),
    CosmicObject(
        mass=0.107,
        radius_au=0.05,
        x_au=-1.5, y_au=0.0,
        color=pygame.Color('Red'),
        name='Mars',
        speed=24000,
        angle=90
    ),
    CosmicObject(
        mass=333000,     
        radius_au=0.1,
        x_au=0.0, y_au=0.0,
        color=pygame.Color('Yellow'),
        name='Sun'
    ),
]

changeSimSpeed = pygame_gui.elements.UIButton(
    pygame.Rect((20, 100), (250, 125)),
    "Change simulation speed",
    manager=manager
)

addNewPlanet = pygame_gui.elements.UIButton(
    pygame.Rect((20, 250), (250, 125)),
    "Add new planet",
    manager=manager
)

settings = pygame_gui.elements.UIButton(
    pygame.Rect((20, w-20), (50, 50)),
    "Settings",
    manager=manager
)

running = True
simSpeedPopup = None
addPlanetPopup = None
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == simSpeedPopup:
                SimSpeedPopup.active = False
                simSpeedPopup.kill()
            
            if event.ui_element == addPlanetPopup:
                AddPlanetPopup.active = False
                addPlanetPopup.kill()

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == changeSimSpeed and not SimSpeedPopup.active:
                simSpeedPopup = SimSpeedPopup(pygame.Rect((300, 200), (250, 350)), manager)
                SimSpeedPopup.active = True

            if simSpeedPopup is not None:
                if event.ui_element == simSpeedPopup.labels["enter"]:
                    newSimSpeed = 0
                    for unit, entry in simSpeedPopup.text_entries.items(): 
                        delta = entry.get_text() 
                        if delta == "":
                            continue
                        newSimSpeed += int(delta) * UNITS[unit[:-1].lower()]
                    if newSimSpeed == 0:
                        newSimSpeed = 1
                    TIME_SCALE = newSimSpeed
                    # SimSpeedPopup.active = False
                    # simSpeedPopup.kill()
            
            if event.ui_element == addNewPlanet and not AddPlanetPopup.active:
                addPlanetPopup = AddPlanetPopup(pygame.Rect((300, 200), (300, 350)), manager)
                AddPlanetPopup.active = True
            
            if addPlanetPopup is not None:
                if event.ui_element == addPlanetPopup.labels["create-planet"]:
                    objects.append(
                        CosmicObject(
                            float(addPlanetPopup.text_entries["Mass"].get_text()),
                            float(addPlanetPopup.text_entries["Radius"].get_text()),
                            float(addPlanetPopup.text_entries["X-coord"].get_text()),
                            float(addPlanetPopup.text_entries["Y-coord"].get_text()),
                            addPlanetPopup.text_entries["Color"].get_text(),
                            addPlanetPopup.text_entries["Name"].get_text(),
                            float(addPlanetPopup.text_entries["Speed"].get_text()),
                            float(addPlanetPopup.text_entries["Angle"].get_text())
                        )
                    )
                    # AddPlanetPopup.active = False
                    # addPlanetPopup.kill()

        manager.process_events(event)
    
    dt = clock.tick(FRAMERATE_CAP) / 1000.0 * TIME_SCALE # once again, should technically use delta_t but dt was short
    
    for obj in objects:
        obj.update(objects, dt)

    screen.fill((0, 0, 0))

    #DRAW LINES FOR GRAPH
    if show_graph_axises: # Weird stuff happens when pixels per AU is changed, will make sure to fix later - 9/5/2025
        pygame.draw.line(screen, "white", (0, h/2), (w, h/2))
        pygame.draw.line(screen, "white", (w/2, 0), (w/2, h))

        # from mid to right side
        for i in range(int(w/2), int(w), int(SCALE/5)):
            length = 5
            if ((i-int(w/2)) % SCALE/5 == 0):
                length = 15
            pygame.draw.line(screen, "white", (i, h/2+length), (i, h/2-length))

        # from mid to left
        for i in range(int(w/2), 0, -int(SCALE/5)):
            length = 5
            if ((int(w/2)-i) % SCALE/5 == 0):
                length = 15
            pygame.draw.line(screen, "white", (i, h/2+length), (i, h/2-length))

        # from mid to below
        for i in range(int(h/2), int(h), int(SCALE/5)):
            length = 5
            if ((i-int(h/2)) % SCALE/5 == 0):
                length = 15
            pygame.draw.line(screen, "white", (w/2+length, i), (w/2-length, i))

        # from mid to above
        for i in range(int(h/2), 0, -int(SCALE/5)):
            length = 5
            if ((int(h/2)-i) % SCALE/5 == 0):
                length = 15
            pygame.draw.line(screen, "white", (w/2+length, i), (w/2-length, i))
            
    for obj in objects:
        obj.draw(screen)
    screen.blit(
        FONT.render(f"Simulation speed: {secondsToTimeString(TIME_SCALE, ', ')}.\nSimulation Scale: {SCALE} pixels per Astronomical Unit.", True, pygame.Color("White")),
        (20, 20)
    )
    manager.update(dt)
    manager.draw_ui(screen)
    pygame.display.flip()

pygame.quit()
