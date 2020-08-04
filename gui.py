import sys
import random
import lp_generator
from lp_generator import Problem
import PyQt5
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class GUI(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.problem = Problem(50)
        self.initUI()

    def initUI(self):
        self.mainFrame = MainFrame(self, self.problem)
        self.setCentralWidget(self.mainFrame)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        self.agentsMenu = menubar.addMenu('&Agents')
        self.agentsActions = []

        openMenu = QMenu('Open..', self)
        openProblem = QAction('Problem', self)
        openAgents = QAction('Agents', self)
        openMap = QAction('Map', self)

        openProblem.triggered.connect(self.openProblemFile)
        openAgents.triggered.connect(self.openAgentsFile)
        openMap.triggered.connect(self.openMapFile)

        openMenu.addAction(openProblem)
        openMenu.addAction(openAgents)
        openMenu.addAction(openMap)

        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)

        fileMenu.addMenu(openMenu)
        fileMenu.addAction(exitAct)
        
        self.resize(900, 650)
        self.setWindowTitle('MAPF')    
        self.show()

    def openAgentsFile(self):
        file = QFileDialog.getOpenFileName(self, 'Open file', '')
        if len(file[0]) == 0:
            return
        self.problem.read_agents(file[0])
        self.addAgentsMenu()
        self.mainFrame.redefineProblem(self.problem)

    def openMapFile(self):
        file = QFileDialog.getOpenFileName(self, 'Open file', '')
        if len(file[0]) == 0:
            return
        self.problem.read_map(file[0])
        self.mainFrame.redefineProblem(self.problem)

    def openProblemFile(self):
        file = QFileDialog.getOpenFileName(self, 'Open file', '')
        if len(file[0]) == 0:
            return
        self.problem = Problem(50)
        self.problem.read_instance(file[0])
        self.addAgentsMenu()
        self.mainFrame.redefineProblem(self.problem)

    def makeCheckAgent(self, agent_id):
        def checkAgent():
            self.mainFrame.switchCheckAgent(agent_id)
        return checkAgent

    def addAgentsMenu(self):


        self.agentsMenu.clear()
        self.agentsActions = []

        for ag in range(self.problem.num_agents):
            agAction = QAction('agent {0}'.format(ag), self, checkable=True)
            agAction.setChecked(True)
            agAction.triggered.connect(self.makeCheckAgent(ag))
            self.agentsActions.append(agAction)
            self.agentsMenu.addAction(agAction)


        agAllAction = QAction('Select all', self)
        agAllAction.triggered.connect(self.selectAgents)
        self.agentsMenu.addAction(agAllAction)

        agDesAction = QAction('Deselect all', self)
        agDesAction.triggered.connect(self.deselectAgents)
        self.agentsMenu.addAction(agDesAction)

    def selectAgents(self):
        
        for ag in range(self.problem.num_agents):
            self.agentsActions[ag].setChecked(True)
            self.mainFrame.changeCheckAgent(ag, True)
        
    
    def deselectAgents(self):
        for ag in range(self.problem.num_agents):
            self.agentsActions[ag].setChecked(False)
            self.mainFrame.changeCheckAgent(ag, False)




class MainFrame(QFrame):
    def __init__(self, parent, problem):
        super().__init__(parent)
        self.initFrame(problem)  
        
    def initFrame(self, problem):
             
        '''initiates board'''
        #self.setMinimumSize(600, 600)
        self.problem = problem
        grid = QGridLayout()
        self.setLayout(grid)
        self.textEditor = QPlainTextEdit()
        self.textEditor.setPlainText('...')
        self.textEditor.setMaximumWidth(300)
        self.textEditor.setMinimumWidth(300)
        grid.addWidget(self.textEditor, 0, 0, 1, 2)

        self.mapDraw = MapDraw(self, self.problem)
        grid.addWidget(self.mapDraw, 0, 2, 1, -1)

        genButton = QPushButton('Generate')
        genButton.clicked.connect(self.generateClingo)
        grid.addWidget(genButton, 1, 0, 1, 1)

        solveButton = QPushButton('Solve')
        solveButton.clicked.connect(self.solveClingo)
        grid.addWidget(solveButton, 1, 1, 1, 1)

        self.timeSlider = QSlider(Qt.Horizontal)
        self.timeSlider.setTickInterval(1)
        self.timeSlider.setMinimum(0)
        self.timeSlider.setMaximum(self.problem.time)
        self.timeSlider.setTickPosition(QSlider.TicksBothSides)
        self.timeSlider.valueChanged.connect(self.changeTime)
        grid.addWidget(self.timeSlider,1,2,1,-1)

        self.update()

    def redefineProblem(self, problem):
        self.problem = problem
        self.mapDraw.initMap(problem)

    def generateClingo(self):
        self.problem.gen_solution()
        self.changeMaxTime(self.problem.max_time)
        self.problem.write_to_lp('buffer.lp')
        with open('buffer.lp', 'r') as bufferFile:
            self.textEditor.setPlainText(bufferFile.read())

    def solveClingo(self):
        print('clingo esta resolviendo')
        self.problem.clingo_solve('buffer.lp')
        self.changeMaxTime(self.problem.sol_time)
        self.mapDraw.update()

    def switchCheckAgent(self, agent_id):
        self.mapDraw.switchCheckAgent(agent_id)

    def changeCheckAgent(self, agent_id, change):
        self.mapDraw.changeCheckAgent(agent_id, change)

    def changeTime(self):
        self.mapDraw.setTime(self.timeSlider.value())

    def changeMaxTime(self, time):
        self.timeSlider.setMaximum(time)



class MapDraw(QWidget):

    SquareSize = 30
    CircleSize = 25
    GoalSize = 20
    Margin = 0

    def __init__(self, parent, problem):
        super().__init__(parent)
        self.initMap(problem)
        
    def initMap(self, problem):
             
        '''initiates board'''
        self.setMinimumSize(300, 300)
        self.problem = problem
        #self.setFocusPolicy(Qt.StrongFocus)
        self.defineAgents()
        self.update()
        self.time = 0

        height = (self.problem.height + 1) * MapDraw.SquareSize
        width =(self.problem.width + 1) * MapDraw.SquareSize

    def defineAgents(self):
        self.colorTable = []
        self.agChecked = []
        for ag in range(self.problem.num_agents):
            self.colorTable.append(generate_new_color(self.colorTable,pastel_factor = 0.4))
            self.agChecked.append(True)

    def switchCheckAgent(self, agent_id):
        self.agChecked[agent_id] = not self.agChecked[agent_id]
        print(agent_id)
        self.update()

    def changeCheckAgent(self, agent_id, change):
        self.agChecked[agent_id] = change
        self.update()

    def setTime(self, time):
        self.time = time
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for y in range(self.problem.height):
            for x in range(self.problem.width):
                posX = x * MapDraw.SquareSize
                posY = y * MapDraw.SquareSize
                if self.problem.map[y][x] == 1:
                    self.drawBlackSquare(painter,posX + MapDraw.Margin, posY + MapDraw.Margin)
                else:
                    self.drawEmptySquare(painter,posX + MapDraw.Margin, posY + MapDraw.Margin)



        for ag in range(self.problem.num_agents):
            if self.agChecked[ag]:
                goalX = self.problem.agents_pos[ag][3] * MapDraw.SquareSize
                goalY = self.problem.agents_pos[ag][2] * MapDraw.SquareSize
                self.drawGoal(painter, goalX + MapDraw.Margin, goalY + MapDraw.Margin, ag)

        for ag in range(self.problem.num_agents):
            if self.agChecked[ag]:
                if self.problem.solved:
                    t = min(self.time, len(self.problem.sol[ag]) - 1)
                    posX = self.problem.sol[ag][t][0] * MapDraw.SquareSize
                    posY = self.problem.sol[ag][t][1] * MapDraw.SquareSize

                else:
                    posX = self.problem.agents_pos[ag][1] * MapDraw.SquareSize
                    posY = self.problem.agents_pos[ag][0] * MapDraw.SquareSize



                self.drawAgent(painter, posX + MapDraw.Margin, posY + MapDraw.Margin, ag)



    def drawEmptySquare(self, painter, x, y):
        painter.setPen(QColor(0,0,0))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(x, y, MapDraw.SquareSize, MapDraw.SquareSize)
        #painter.drawRect(x + 2, y + 2, Map.SquareSize-4, Map.SquareSize-4)

    def drawBlackSquare(self, painter, x, y):
        painter.setPen(QColor(0,0,0))
        painter.setBrush(QColor(0,0,0))
        painter.drawRect(x, y, MapDraw.SquareSize, MapDraw.SquareSize)

    def drawAgent(self, painter, x, y, agent_id):
        dif = (MapDraw.SquareSize - MapDraw.CircleSize) / 2
        color = self.colorTable[agent_id]
        color = QColor(color[0],color[1],color[2])
        brush = QBrush(color)
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        painter.setPen(color)
        painter.drawEllipse(x + dif, y + dif, MapDraw.CircleSize, MapDraw.CircleSize)


        center = MapDraw.SquareSize/2
        fontSize = MapDraw.CircleSize/2
        sqSize = MapDraw.SquareSize/3

        
        painter.setBrush(Qt.black)
        painter.setPen(Qt.black)
  

        font = QFont()
        font.setPointSize(fontSize)


        painter.setFont(font)
        painter.setBrush(Qt.white)
        painter.setPen(Qt.white)
        painter.drawText(QRectF(x + dif, y + dif, MapDraw.CircleSize, MapDraw.CircleSize), Qt.AlignCenter|Qt.AlignCenter, 'a{0}'.format(agent_id))

        pen = QPen(QColor(0,0,0))
        pen.setWidth(3);
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(x + dif, y + dif, MapDraw.CircleSize, MapDraw.CircleSize)

        



    def drawGoal(self, painter, x, y, agent_id):
        dif = (MapDraw.SquareSize - MapDraw.GoalSize) / 2
        color = self.colorTable[agent_id]
        color = QColor(color[0],color[1],color[2])
        brush = QBrush(color)
        brush.setStyle(Qt.DiagCrossPattern)
        painter.setBrush(brush)
        painter.setPen(color)
        painter.drawRect(x + dif, y + dif, MapDraw.GoalSize, MapDraw.GoalSize)



def get_random_color(pastel_factor = 0.5):
    return [(x+pastel_factor)/(1.0+pastel_factor) for x in [int(random.uniform(0,1.0) * 255) for i in [1,2,3]]]

def color_distance(c1,c2):
    return sum([abs(x[0]-x[1]) for x in zip(c1,c2)])

def generate_new_color(existing_colors,pastel_factor = 0.5):
    max_distance = None
    best_color = None
    for i in range(0,100):
        color = get_random_color(pastel_factor = pastel_factor)
        if not existing_colors:
            return color
        best_distance = min([color_distance(color,c) for c in existing_colors])
        if not max_distance or best_distance > max_distance:
            max_distance = best_distance
            best_color = color
    return best_color


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = GUI()
    sys.exit(app.exec_())