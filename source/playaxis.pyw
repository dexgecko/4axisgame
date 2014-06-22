from extend import array
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msg
import configparser

rawConfigPath = "config.ini"

## read configuration file and set game properties
parser = configparser.ConfigParser()
parser.read(rawConfigPath)
available = parser.sections()
gameatr = parser['GAME']

# set/extract game properties
CANVAS_ADJUST = 6
CELL_SPAN = int(gameatr['CELL_SPAN'])
CELL_SIZE = int(gameatr['CELL_SIZE'])
CELL_MARGIN = int(gameatr['CELL_MARGIN'])
GAME_WRAP = True
WINDOW_TITLE = gameatr['WINDOW_TITLE']
ENDGAME_TITLE = gameatr['ENDGAME_TITLE']
ENDGAME_MESSG = gameatr['ENDGAME_MESSG']
BOARD_WIDTH = CELL_SPAN*CELL_SIZE - CANVAS_ADJUST

PLAYER_BASE = (0,1,2)
PLAYER_OTHER = (0,2,1)
PLAYER_COLOR = eval(gameatr['PLAYER_COLOR'])
PLAYER_TURN_LBL = gameatr['PLAYER_TURN_LBL']
CELL_CLOSE = ((0, 1), (0, -1), (1, 0), (1, 1),
              (1, -1), (-1, 0), (-1, 1), (-1, -1))
CELL_CRAXES = ((0,1),(2,5),(3,7),(4,6))
G_WINCNT = 2

# set tags
T_PL = 'player'
T_GR = 'gridline'

# strip base configurations
for i in ('GAME','TYPES'): available.remove(i)
# extract and process remaining configurations
typeset = parser['TYPES']
DCONFIG = {}
for c in available:
    target = DCONFIG[c] = {}
    for a in parser[c]:
        target[a] = eval(typeset[a])(parser[c][a])

class board:

    def __init__(self, cell_span, cell_size,\
                 reference_canvas=None, config=None,\
                 wrap=True):
        self.cellSpan = cell_span
        self.cellSize = cell_size
        self.boardWidth = cell_span*cell_size

        self.wrap = wrap
        self.plCnfg = {1:config["Player 1"],2:config["Player 2"]}
        self.grCnfg = config["Grid Lines"]

        self.canv = reference_canvas
        self.currentPlayer = 1

        # create board as array full of 0 (neutral)
        self.buildGrid()

    def buildGrid(self):
        self.grid = array(self.cellSpan, self.cellSpan, build=0)

    def switchPlayer(self):
        if self.currentPlayer in (1,2):
            self.currentPlayer = PLAYER_OTHER[self.currentPlayer]
        else: raise ValueError("current player value, {} not valid".\
                               format(self.currentPlayer))

    def checkCoord(self, x, y, base='canv'):
        #print("checkCoord",x,y,base)
        if base=='canv': limit = self.boardWidth
        elif base=='grid': limit = self.cellSpan-1
        else: raise ValueError("invalid argument for base, {}".\
                               format(base))

        return 0<=x<=limit and 0<=y<=limit

    def canvToGrid(self, cx, cy):
        #print("canvToGrid",cx,cy)
        if self.checkCoord(cx, cy, base='canv'):
            return tuple([ i//self.cellSize for i in (cx, cy)])
        else:
            raise ValueError("canvas coordinates {} out of bounds".\
                             format((cx,cy)))

    def gridToCanv(self, gx, gy, center=True):
        if self.checkCoord(gx, gy, base='grid'):
            return tuple([ (i+(0.5*int(center)))*self.cellSize\
                            for i in (gx, gy)])
        else:
            raise ValueError("grid coordinates {} out of bounds".\
                             format((cx,cy)))
        
    def getCellPlayer(self, gx, gy):
        player = self.grid[gx,gy]
        if player in PLAYER_BASE:
            return player
        else:
            raise ValueError("current player value, {} not valid".\
                             format(self.player))
        
    def markCell(self, player, gx, gy):
        #print("markCell",player,gx,gy)
        if self.getCellPlayer(gx, gy) == 0:
            #print("markCell>","valid play")
            self.grid[gx,gy] = player
            return True
        else:
            #print("markCell>","invalid play")
            return False

    def drawPlay(self, player, gx, gy):
        #print("drawPlay",player,gx,gy)
        # calculate marker radius from cell size and default margin
        r = (self.cellSize//2)-CELL_MARGIN
        # marker center coordinates
        x, y = self.gridToCanv(gx, gy, center=True)
        self.canv.create_oval(x-r,y-r,x+r,y+r,\
                              tags=[T_PL],**self.plCnfg[player])

    def drawGrid(self):
        
        #print("drawGrid")
        for n in range(self.cellSize,self.boardWidth,self.cellSize):
            # horizontal lines
            self.canv.create_line(0,n,self.boardWidth,n,\
                                  tags=[T_GR],**self.grCnfg)
            # vertical lines
            self.canv.create_line(n,0,n,self.boardWidth,\
                                  tags=[T_GR], **self.grCnfg)

    def wrapCoord(self, v):
        limit = self.cellSpan-1
        if v<0 or v>limit:
            return max(limit-v, v-limit)-1
        else:
            return v 

    def getAdjacent(self, gx, gy, wrap=True):
        if wrap: wf = self.wrapCoord
        else: wf = lambda x:x
        
        return [ (wf(gx+dx),wf(gy+dy)) for dx,dy in CELL_CLOSE ]
            

    def scoreCell(self, gx, gy, wrap=True):
        if self.getCellPlayer(gx,gy) in (1,2):
            border = [ self.getCellPlayer(x,y) for x,y\
                       in self.getAdjacent(gx,gy,wrap) ]

            cellPlayer = self.getCellPlayer(gx, gy)
            cellEnemy = PLAYER_OTHER[cellPlayer]

            # check for opposite cells in a single axis with the same
            # state (player entered)

            boundCount = 0

            for i1, i2 in CELL_CRAXES:
                if border[i1] == cellEnemy and border[i2] == cellEnemy:
                    boundCount += 1

            if boundCount >= G_WINCNT: return cellEnemy
        return 0

    def clearBoard(self):
        #print("clearBoard")
        self.canv.delete(T_PL)

    def scoreAllCells(self):
        #print("scoreAllCells")
        pl_current = self.currentPlayer
        pl_enemy = PLAYER_OTHER[pl_current]
        #print(">",pl_current,pl_enemy)
        
        cellStates = set()
        # get all possible win scenarios on board into cellStates
        for gx, gy in self.grid.itercoords():
            cellStates.add(self.scoreCell(gx,gy,self.wrap))

        #print(">",cellStates)

        # current player gets first pick on win, otherwise
        # enemy player wins if current player put themselves into
        # a loss scenario
        if pl_current in cellStates: return pl_current
        elif pl_enemy in cellStates: return pl_enemy
        else: return 0

    
    def runVictory(self, winner):
        #print("runVictory",winner)
        self.currentPlayer = 0
        msg.showinfo(title=ENDGAME_TITLE,message=ENDGAME_MESSG.format(winner))
        self.currentPlayer = 1
        self.clearBoard()
        self.buildGrid()
        pass

    def play(self, cx, cy):
        #print(">>>>\n","play",cx,cy)
        try:
            gx, gy = self.canvToGrid(cx, cy)
        except ValueError:
            return False

        #print("play>",gx,gy)

        if self.markCell(self.currentPlayer, gx, gy):
            #print("play>","cell marked")
            self.drawPlay(self.currentPlayer, gx, gy)
            #print("play>","cell drawn")

            checkWinner = self.scoreAllCells()
            if checkWinner != 0:
                #print("play>","victory condition satisfied")
                self.runVictory(checkWinner)
            else:
                #print("play>","no victory, next play")
                self.switchPlayer()
      
root =  tk.Tk()
root.title(WINDOW_TITLE)
root.resizable(0,0)

main = ttk.Frame(root, relief=tk.SUNKEN,borderwidth=1)
main.grid(padx=5,pady=5)
canvas = tk.Canvas(main, width=BOARD_WIDTH, height=BOARD_WIDTH)
canvas.grid()

var_turn = tk.StringVar()
lbl_turn = tk.Label(root, textvariable=var_turn)
lbl_turn.grid(pady=4)

game = board(CELL_SPAN, CELL_SIZE, canvas, DCONFIG, GAME_WRAP)
game.drawGrid()

def updateTurn():
    player = game.currentPlayer
    var_turn.set(PLAYER_TURN_LBL.format(player, PLAYER_COLOR[player]))

def makePlay(event):
    game.play(event.x, event.y)
    updateTurn()

canvas.bind('<Button-1>', makePlay)
updateTurn()
root.mainloop()
