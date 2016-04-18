# 18-842 Distributed Systems // Spring 2016.
# Multegula - A P2P block breaking game.
# Player.py.
# Team Misfits // amahmoud. ddsantor. gmmiller. lunwenh.

# imports
from enum import Enum
import random
from UI.typedefs import *
from UI.components.gameplay.Paddle import *

# PLAYER class
class Player :
    ### __init__  - initialize and return Player
    ##  @param orientation - location on the screen of this padde (DIR_NORTH/DIR_SOUTH/...)
    ##  @param state - current control state of the player (USER/AI/COMP)
    def __init__(self, orientation, state, name, gameType) :
        self.ORIENTATION = orientation
        self.state = state
        self.score = 0
        self.lives = 5
        self.power = PowerUps.PWR_NONE
        self.paddle = Paddle(orientation, state, gameType)
        self.first = True
        self.statusUpdate = False
        self.name = name
        self.gameType = gameType

    ### AI method -
    ##  This method moves the paddles automatically to contact the ball. There are some
    ##  non-idealities built in so the computer is not perfect
    def AI(self, canvas) :
        # get ball/paddle information
        (ballCenterX, ballCenterY, ballRadius) = canvas.data['ball'].getInfo()
        (paddleCenter, paddleWidth, paddleDir, paddleOrientation) = self.paddle.getInfo()

        # calcualte an offset and a random number - used to create a delay in the paddle response
        offset = paddleWidth // 5
        chance = random.randint(0, 4)

        # determine which direction the ball in from the center of the paddle based on the
        #   current orientation.
        if paddleOrientation == Orientation.DIR_NORTH or paddleOrientation == Orientation.DIR_SOUTH :
            direction = paddleCenter - ballCenterX
        elif paddleOrientation == Orientation.DIR_WEST or paddleOrientation == Orientation.DIR_EAST :
            direction = paddleCenter - ballCenterY

        # MOVE the paddle -
        ## if the ball has moved at least 'offset' distance from the center of the paddle, 
        ##  the paddle is currently stopped, and it's your lucky day -> move the paddle
        if((abs(direction) > offset) and (paddleDir == Direction.DIR_STOP) and (chance == 1)) : 
            if(direction < offset) :
                self.paddle.direction = Direction.DIR_RIGHT
            elif direction > offset :
                self.paddle.direction = Direction.DIR_LEFT
        ## otherwise, if it's your lucky day -> stop the paddle
        elif chance == 0 :
            self.paddle.direction = Direction.DIR_STOP

    ### breakBlock --
    ##  handles the breaking of blocks
    def breakBlock(self, canvas) :
        (ballLeft, ballRight, ballTop, ballBottom) = canvas.data['ball'].getEdges()
        (ballCenterX, ballCenterY, ballRadius) = canvas.data['ball'].getInfo()
        (xVelocity, yVelocity) = canvas.data['ball'].getVelocity()
        blocks = canvas.data['level'].blocks;
        broken = False;
        returnInfo = []

        # ball moving NORTH WEST
        if xVelocity < 0 and yVelocity <= 0 :
            for blockIndex, block in enumerate(blocks) :
                if(block.enabled == True) :
                    (blkLeft, blkRight, blkTop, blkBottom) = block.getEdges()
                    # hit bottom of the block
                    if (ballTop <= blkBottom) and (ballBottom > blkBottom) and (blkLeft <= ballRight) and (ballLeft <= blkRight) :
                        returnInfo = [xVelocity, (-yVelocity), blockIndex]
                        broken =True;
                        break
                    # hit right side of the block
                    elif (ballLeft <= blkRight) and (ballRight > blkRight) and (blkTop <= ballBottom) and (ballTop <= blkBottom) :
                        returnInfo = [(-xVelocity), yVelocity, blockIndex]
                        broken = True;
                        break                                     

        # ball moving NORTH EAST
        elif(xVelocity >= 0) and (yVelocity <= 0) :
            for blockIndex, block in enumerate(blocks) :
                if(block.enabled == True) :
                    # hit bottom of the block
                    (blkLeft, blkRight, blkTop, blkBottom) = block.getEdges()
                    if (ballTop <= blkBottom) and (ballBottom > blkBottom) and (blkLeft <= ballRight) and (ballLeft <= blkRight) :
                        returnInfo = [xVelocity, (-yVelocity), blockIndex]
                        broken = True
                        break
                    # hit left side of the block
                    elif (ballRight >= blkLeft) and (ballLeft < blkRight) and (blkTop <= ballBottom) and (ballTop <= blkBottom) :
                        returnInfo = [(-xVelocity), yVelocity, blockIndex]
                        broken = True;
                        break                                   
          
        # ball moving SOUTH WEST
        elif(xVelocity < 0) and (yVelocity > 0) :
            for blockIndex, block in enumerate(blocks) :
                if(block.enabled == True) :
                    # hit top of the block
                    (blkLeft, blkRight, blkTop, blkBottom) = block.getEdges()
                    if (ballBottom >= blkTop) and (ballTop < blkTop) and (blkLeft <= ballRight) and (ballLeft <= blkRight) :
                        returnInfo = [xVelocity, (-yVelocity), blockIndex]
                        broken = True;
                        break
                    # hit right of the block
                    elif (ballLeft <= blkRight) and (ballRight > blkRight) and (blkTop <= ballBottom) and (ballTop <= blkBottom) :
                        returnInfo = [(-xVelocity), yVelocity, blockIndex]
                        broken = True;
                        break

        # ball moving SOUTH EAST
        elif(xVelocity >= 0) and (yVelocity > 0) :
            for blockIndex, block in enumerate(blocks) :
                if(block.enabled == True) :
                    (blkLeft, blkRight, blkTop, blkBottom) = block.getEdges()
                    # hit top of the block
                    if (ballBottom >= blkTop) and (ballTop < blkTop) and (blkLeft <= ballRight) and (ballLeft <= blkRight) :
                        returnInfo = [xVelocity, (-yVelocity), blockIndex]
                        broken = True;
                        break
                    # hit left side of the block
                    elif (ballRight >= blkLeft) and (ballLeft < blkRight) and (blkTop <= ballBottom) and (ballTop <= blkBottom) :
                        returnInfo = [(-xVelocity), yVelocity, blockIndex]
                        broken = True;
                        break

        # if there was a broken block - return appropriate information
        if broken == True :
            return (PlayerReturnStatus.BLOCK_BROKEN, returnInfo)
        return (PlayerReturnStatus.NO_STATUS, [])


    ### deflectBall method - 
    ##  Check to see if the ball is off the playing field or is being deflected by the player's paddle.
    def deflectBall(self, canvas) :
        # get canvas/paddle/ball info
        ORIENTATION = self.ORIENTATION
        (ballCenterX, ballCenterY, ballRadius) = canvas.data['ball'].getInfo()
        (leftEdge, rightEdge, topEdge, bottomEdge) = self.paddle.getEdges()
        (paddleCenter, paddleWidth, paddleDir, paddleOrientation) = self.paddle.getInfo()

        # initialize flags
        ballMissed = False
        ballDeflected = False

        # ball out of bounds/deflected on NORTH edge/paddle
        if(ORIENTATION == Orientation.DIR_NORTH) :
            if((ballCenterY - ballRadius) <= 0) :
                ballMissed = True
            elif(((leftEdge <= (ballCenterX + ballRadius) < rightEdge) and (topEdge <= (ballCenterY - ballRadius) < bottomEdge)) or 
                    (leftEdge < ((ballCenterX - ballRadius) <= rightEdge) and (topEdge <= (ballCenterY - ballRadius) < bottomEdge))) :
                ballDeflected = True

        # ball out of bounds/deflected on the SOUTH edge/paddle
        elif(ORIENTATION == Orientation.DIR_SOUTH) :
            if((ballCenterY + ballRadius) >= CANVAS_HEIGHT) : 
                ballMissed = True
            elif(((leftEdge <= (ballCenterX + ballRadius) < rightEdge) and (topEdge <= (ballCenterY + ballRadius) < bottomEdge)) or 
                    (leftEdge < ((ballCenterX - ballRadius) <= rightEdge) and (topEdge <= (ballCenterY + ballRadius) < bottomEdge))) :
                ballDeflected = True

        # ball out of bounds/deflected on the EAST edge/paddle
        elif(ORIENTATION == Orientation.DIR_EAST) :
            if((ballCenterX + ballRadius) >= CANVAS_WIDTH) :
                ballMissed = True
            elif(((topEdge <= (ballCenterY + ballRadius) < bottomEdge) and (leftEdge <= (ballCenterX + ballRadius) < rightEdge)) or
                    (topEdge < ((ballCenterX - ballRadius) <= bottomEdge) and (leftEdge <= (ballCenterX + ballRadius) < rightEdge))) :
                ballDeflected = True

        # ball out of bounds/deflected on the WEST edge/paddle
        elif(ORIENTATION == Orientation.DIR_WEST) :
            # out of play
            if((ballCenterX - ballRadius) <= 0) :
                ballMissed = True
            elif(((topEdge <= (ballCenterY + ballRadius) < bottomEdge) and (leftEdge <= (ballCenterX - ballRadius) < rightEdge)) or
                    (topEdge < ((ballCenterX - ballRadius) <= bottomEdge) and (leftEdge <= (ballCenterX - ballRadius) < rightEdge))) :
                ballDeflected = True

        # # reset ball, apply appropriate scoring
        if ballMissed and self.state != PlayerState.WALL:
            return (PlayerReturnStatus.BALL_MISSED, [])
        elif ballDeflected and self.state != PlayerState.WALL:
            return (PlayerReturnStatus.BALL_DEFLECTED, self.deflectBallVelocity(canvas))
        elif ballDeflected and self.state == PlayerState.WALL:
            return (PlayerReturnStatus.WALL_BALL_DEFLECTED, self.deflectBallVelocity(canvas))
        elif self.state == PlayerState.WALL:
            return (PlayerReturnStatus.WALL_NO_STATUS, [])
        return (PlayerReturnStatus.NO_STATUS, [])

    ### deflectBallVelocity - 
    ##  Deflect ball off of a paddle and determine the new direction off the ball
    def deflectBallVelocity(self, canvas) :
        # initialize speed and random offset variables
        speed = BALL_SPEED_INIT
        offsetFactor = random.uniform(1, 1.1)
        offset = random.uniform(-0.1, 0.1)

        # get ball/paddle info
        (paddleCenter, paddleWidth, paddleDir, paddleOrientation) = self.paddle.getInfo()
        (ballCenterX, ballCenterY, ballRadius) = canvas.data['ball'].getInfo()
        (xVelocity, yVelocity) = canvas.data['ball'].getVelocity()

        # deflect off NORTH paddle
        if(paddleOrientation == Orientation.DIR_NORTH) :
            if self.state == PlayerState.WALL :
                yVelocity = (-yVelocity)
            else :
                speedFactor = (ballCenterX - paddleCenter) / paddleWidth
                xVelocity = round(speed * speedFactor * offsetFactor + offset, RD_FACT)
                yVelocity = speed        

        # deflect off SOUTH paddle
        elif(paddleOrientation == Orientation.DIR_SOUTH) :
            if self.state == PlayerState.WALL :
                yVelocity = (-yVelocity)
            else :
                speedFactor = (ballCenterX - paddleCenter) / paddleWidth
                xVelocity = round(speed * speedFactor * offsetFactor + offset, RD_FACT)
                yVelocity = (-speed)

        # deflect off EAST paddle
        elif(paddleOrientation == Orientation.DIR_EAST) :
            if self.state == PlayerState.WALL :
                xVelocity = (-xVelocity)
            else :
                speedFactor = (ballCenterY - paddleCenter) / paddleWidth
                xVelocity = (-speed)
                yVelocity = round(speed * speedFactor * offsetFactor + offset, RD_FACT)
        
        # deflect off WEST paddle
        elif(paddleOrientation == Orientation.DIR_WEST) :
            if self.state == PlayerState.WALL :
                xVelocity = (-xVelocity)
            else : 
                speedFactor = (ballCenterY - paddleCenter) / paddleWidth
                xVelocity = speed
                yVelocity = round(speed * speedFactor * offsetFactor + offset, RD_FACT)

        return [xVelocity, yVelocity]
 
    ### setStatus method -
    ##  Place the status text for the player on the canvas
    def setStatus(self, canvas) :
        # get canvas info
        ORIENTATION = self.ORIENTATION
        X_MARGIN = CANVAS_WIDTH // 60
        Y_MARGIN = CANVAS_HEIGHT // 60

        # initilize status message
        statusMsg = self.name + ' : '

        # determin X_LOC, Y_LOC, and NAME based on orientation
        if(ORIENTATION == Orientation.DIR_NORTH) :
            X_LOC = CANVAS_WIDTH*0.25
            Y_LOC = Y_MARGIN
        elif(ORIENTATION == Orientation.DIR_SOUTH) :
            X_LOC = CANVAS_WIDTH*0.75
            Y_LOC = CANVAS_HEIGHT - Y_MARGIN
        elif(ORIENTATION == Orientation.DIR_EAST) :
            X_LOC = CANVAS_WIDTH*0.75
            Y_LOC = Y_MARGIN    
        elif(ORIENTATION == Orientation.DIR_WEST) :
            X_LOC = CANVAS_WIDTH*0.25
            Y_LOC = CANVAS_HEIGHT - Y_MARGIN

        # finish status message and display
        statusMsg += 'P/' + str(self.score) + '.  L/' + str(self.lives) + '.'
        self.t = canvas.create_text(X_LOC, Y_LOC, text = statusMsg,
                                    font = ('Courier', S_TEXT_SIZE), fill = 'white')
        
    ### displayStatus method -
    ##  Display the text for the player indicating the current score and number of lives remaining
    def displayStatus(self, canvas) :
        if not(self.first) and self.statusUpdate :
            canvas.delete(self.t)
            self.setStatus(canvas)
            self.statusUpdate = False
        elif(self.first) :
            self.setStatus(canvas)
            self.first = False

    ### general purpose update
    def update(self, canvas) :
        # initialze return status to NONE
        returnStatus = PlayerReturnStatus.NO_STATUS

        if self.state != PlayerState.WALL :
            self.displayStatus(canvas)

        # if this is an AI, then updae the motion of the paddles via the AI routine
        if self.state == PlayerState.AI :
            self.AI(canvas)

        # update player for motion and deflection
        if self.state == PlayerState.USER or self.state == PlayerState.AI or self.state == PlayerState.WALL:

            # update the paddle
            self.paddle.update(canvas)
            (status, payload) = self.deflectBall(canvas)

            # if the ball hasn't been deflected or missed, determine if a block has been broken
            if status == PlayerReturnStatus.NO_STATUS and canvas.data['ball'].lastToTouch == self.name :
                (status, payload) = self.breakBlock(canvas)

            # return information to the UI
            return (status, payload)

        # if this player is a competitor, just draw it
        elif(self.state == PlayerState.COMP) :
            self.paddle.draw(canvas)
            return (PlayerReturnStatus.NO_STATUS, [])


