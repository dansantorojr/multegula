# 18-842 Distributed Systems // Spring 2016.
# Multegula - A P2P block breaking game.
# Ball.py.
# Team Misfits // amahmoud. ddsantor. gmmiller. lunwenh.

# imports
import random
from enum import Enum
from components.ComponentDefs import *

# BALL class
class Ball:
    ### __init___ - initialize and return ball
    ##  @param canvas_width
    ##  @param canvas_height
    def __init__(self, canvas_width, canvas_height):
        # constant fields
        self.CANVAS_WIDTH = canvas_width;
        self.CANVAS_HEIGHT = canvas_height;
        self.BORDER_WIDTH = canvas_width // 350;
        self.COLORS = ["red", "green", "blue", "purple", "orange", "yellow"];

        # dynamic fields
        self.xCenter = canvas_width // 2;
        self.yCenter = canvas_height // 2;
        self.radius = canvas_width // 50;
        self.color = "green";
        self.xVelocity = 0;
        self.yVelocity = canvas_width // 100;

    ### reset - reset dynamic ball location/speed properties 
    def reset(self):
        self.randomXVelocity();
        self.yVelocity = random.choice([-1, 1])*self.CANVAS_WIDTH // 100;
        self.xCenter = self.CANVAS_WIDTH // 2;
        self.yCenter = self.CANVAS_HEIGHT // 2;
        self.randomColor();

    ### get/set CENTER methods
    def setCenter(self, xCenter, yCenter):
        self.xCenter = xCenter;
        self.yCenter = yCenter;

    def getCenter(self):
        return(self.xCenter, self.yCenter);

    ### get/set RADIUS methods
    def setRadius(self, radius):
        self.radius = radius;

    def increaseRadius(self):
        self.radius *= 1.1;

    def decreaseRadius(self):
        self.radius /= 0.9;

    def getRadius(self):
        return self.radius;

    ### get/set VELOCITY methods
    def setVelocity(self, xVelocity, yVelocity):
        self.xVelocity = xVelocity;
        self.yVelocity = yVelocity;

    def increaseVelocity(self):
        self.xVelocity *= 1.1;
        self.yVelocity *= 1.1;

    def decreaseVelocity(self):
        self.xVelocity *= 0.9;
        self.yVelocity *= 0.9;

    def randomXVelocity(self):
        speed = self.CANVAS_WIDTH // 100
        factor = random.random();
        factor *= random.randint(-2, 2);
        self.xVelocity = speed*factor;

    def randomYVelocity(self):
        speed = self.CANVAS_WIDTH // 100
        factor = random.random();
        factor *= random.randint(-2, 2);
        self.yVelocity = speed*factor;  

    def getVelocity(self):
        return (self.xVelocity, self.yVelocity); 

    ### get/set COLOR methods
    def setColor(self, color):
        self.color = color;

    def randomColor(self):
        currentColor = self.color;
        newColor = currentColor;

        # loop until a new color has been chosen
        while (currentColor == newColor):
            newColor = random.choice(self.COLORS);

        # set new color
        self.color = newColor;

    def getColor(self):
        return self.color;     

    ### moveMenu - 
    ##  The method moves the ball around the screen and bounces it off of walls. This mode
    ##  is meant for use on menu screens only.
    def moveMenu(self):
        # constants
        CANVAS_WIDTH = self.CANVAS_WIDTH;
        CANVAS_HEIGHT = self.CANVAS_HEIGHT;

        # dynamic variables
        xCenter = self.xCenter;
        yCenter = self.yCenter;
        radius = self.radius;
        xVelocity = self.xVelocity;
        yVelocity = self.yVelocity;

        # UPDATE Y VELOCITY - 
        # Bounce ball off of bottom wall...
        if (((yCenter + radius) >= CANVAS_HEIGHT) and (yVelocity > 0)):
            self.randomXVelocity();
            self.randomColor();
            self.yVelocity -= (2*yVelocity);
        # Bounce ball off of top wall...
        elif (((yCenter - radius) <= 0) and (yVelocity < 0)):
            self.randomColor();
            self.yVelocity -= (2*yVelocity);
        # Move the ball
        else: 
            self.yCenter += yVelocity

        # UPDATE X VELOCITY -
        # Bounce ball off left wall
        if (((xCenter - radius) <= 0) and (xVelocity < 0)):
            self.randomColor();
            self.xVelocity -= (xVelocity*2);
        # Bounce ball off right wall
        elif(((xCenter + radius) >= CANVAS_WIDTH) and (xVelocity > 0)):
            self.randomColor();
            self.xVelocity -= (xVelocity*2);
        # Move ball
        else: 
            self.xCenter += xVelocity; 

    ### moveGame -
    ##  This method moves the ball during gameplay.
    def moveGame(self):
        self.xCenter += self.xVelocity; 
        self.yCenter += self.yVelocity   

    ### draw - draw the ball
    def draw(self, canvas):
        BORDER_WIDTH = self.BORDER_WIDTH;
        color   = self.color;
        xCenter = self.xCenter;
        yCenter = self.yCenter;
        radius  = self.radius;

        canvas.create_oval(xCenter - radius,
                            yCenter - radius,
                            xCenter + radius,
                            yCenter + radius,
                            fill = color, width = BORDER_WIDTH)

    ### updateMenu - general purpose menu update function
    def updateMenu(self, canvas): 
        self.moveMenu(); 
        self.draw(canvas);

    ### updateGame - general purpose game update function
    def updateGame(self, canvas):
        self.moveGame();
        self.draw(canvas);

    ### getInfo - get ball info
    def getInfo(self): 
        return(self.xCenter, self.yCenter, self.radius);


