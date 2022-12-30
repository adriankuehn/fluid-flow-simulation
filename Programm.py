import imageio
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def import_voxelkoerper(datei):
    # Eckpunktkoordinaten und eine Kante aus der Datei übernehmen
    with open(datei) as datei:
        koordinaten = []
        kante = None
        for zeile in datei:
            zeile = zeile.rstrip().split(' ')
            if zeile[0] == 'v':
                koordinaten += [ [float(zeile[1]), -float(zeile[3]), float(zeile[2])] ]
            elif zeile[0] == 'f':
                a = zeile[1].split('//')
                b = zeile[2].split('//')
                kante = [int(a[0]) - 1, int(b[0]) - 1]
    del datei, a, b
    # die Kantenlänge ermitteln
    kantenlaenge = ((koordinaten[kante[0]][0] - koordinaten[kante[1]][0]) ** 2 + \
                    (koordinaten[kante[0]][1] - koordinaten[kante[1]][1]) ** 2 + \
                    (koordinaten[kante[0]][2] - koordinaten[kante[1]][2]) ** 2) ** (1/2)
    del kante
    # alle verschiedenen X, Y und Z - Koordinaten ermitteln
    x = []
    y = []
    z = []
    for p in koordinaten:
        if round(p[0], 4) not in x:
            x += [round(p[0], 4)]
        if round(p[1], 4) not in y:
            y += [round(p[1], 4)]
        if round(p[2], 4) not in z:
            z += [round(p[2], 4)]
    Hinderniss = np.zeros((len(x), len(y), len(z)), bool)

    x_ = min(x)
    y_ = min(y)
    z_ = min(z)
    for i in range(len(koordinaten)):
        koordinaten[i] = [koordinaten[i][0] - x_, koordinaten[i][1] - y_, koordinaten[i][2] - z_]
        a = int((koordinaten[i][0] + kantenlaenge / 2) / kantenlaenge)
        b = int((koordinaten[i][1] + kantenlaenge / 2) / kantenlaenge)
        c = int((koordinaten[i][2] + kantenlaenge / 2) / kantenlaenge)
        Hinderniss[a][b][c] = True
    # Variablen löschen und den Array zurückgeben
    del kantenlaenge, x, y, z, a, b, c, x_, y_, z_, koordinaten, p
    return Hinderniss


def matrixraum_erweitern(matrix, alt, neu, faktormodus, faktormodus_alt, shape):
    # alte Erweiterung entfernen
    if faktormodus_alt:
        bisx = int(alt[0] * shape[0])
        bisyv = int(alt[1][0] * shape[1])
        bisyh = int(alt[1][1] * shape[1])
        biszu = int(alt[2][0] * shape[2])
        biszo = int(alt[2][1] * shape[2])
    else:
        bisx = int(alt[0])
        bisyv = int(alt[1][0])
        bisyh = int(alt[1][1])
        biszu = int(alt[2][0])
        biszo = int(alt[2][1])

    matrix = np.delete(matrix, np.s_[:bisx], 0)
    matrix = np.delete(matrix, np.s_[:bisyv], 1)
    matrix = np.delete(matrix, np.s_[:biszo], 2)
    
    matrix = np.delete(matrix, np.s_[matrix.shape[0] - bisx:], 0)
    matrix = np.delete(matrix, np.s_[matrix.shape[1] - bisyh:], 1)
    matrix = np.delete(matrix, np.s_[matrix.shape[2] - biszu:], 2)
    # den Raum um den Körper ergänzen
    if faktormodus:
        raumX = int(neu[0] * matrix.shape[0])
        raumYv = int(neu[1][0] * matrix.shape[1])
        raumYh = int(neu[1][1] * matrix.shape[1])
        raumZu = int(neu[2][0] * matrix.shape[2])
        raumZo = int(neu[2][1] * matrix.shape[2])
    else:
        raumX = int(neu[0])
        raumYv = int(neu[1][0])
        raumYh = int(neu[1][1])
        raumZu = int(neu[2][0])
        raumZo = int(neu[2][1])

    x_raum = np.zeros( (raumX, matrix.shape[1], matrix.shape[2]), bool )
    matrix = np.append(matrix, x_raum, axis = 0)
    matrix = np.append(x_raum, matrix, axis = 0)

    y_raumv = np.zeros( (matrix.shape[0], raumYv, matrix.shape[2]), bool )
    matrix = np.append(y_raumv, matrix, axis = 1)
    y_raumh = np.zeros( (matrix.shape[0], raumYh, matrix.shape[2]), bool )
    matrix = np.append(matrix, y_raumh, axis = 1)

    z_raumu = np.zeros( (matrix.shape[0], matrix.shape[1], raumZu), bool )
    matrix = np.append(matrix, z_raumu, axis = 2)
    z_raumo = np.zeros( (matrix.shape[0], matrix.shape[1], raumZo), bool )
    matrix = np.append(z_raumo, matrix, axis = 2)
    return matrix



class Programm(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.grid_rowconfigure(self, 0, weight = 1)
        tk.Tk.grid_columnconfigure(self, 0, weight = 1)
        tk.Tk.geometry(self, '1000x620')
        tk.Tk.title(self, 'Simulationsprogramm')

        # Projektmanagement:
        self.projektmanagement = ttk.Notebook(self)
        self.projektmanagement.grid(row = 0, column = 0, sticky = 'nsew')
                # Projektmanagement - Buttons
        self.projekt_loeschen = tk.Button(self.projektmanagement, text ='-')
        self.projekt_loeschen.place(relx = 1, x = -2, y = -2, anchor ='ne', width = 20, height = 20)
        self.projekt_loeschen['command'] = lambda: self._projekt_schliessen()

        self.projekt_hinzufuegen = tk.Button(self.projektmanagement, text ='+')
        self.projekt_hinzufuegen.place(relx = 1, x = -22, y = -2, anchor ='ne', width = 20, height = 20)
        self.projekt_hinzufuegen['command'] = lambda: self._neues_projekt()
        
        self.projektzahl = 1
        self.projekte = {}
        self.projektnamen = []

        #self._neues_projekt()

    def _neues_projekt(self):
        name = 'Projekt ' + str(self.projektzahl) 
        projekt = Projekt(self.projektmanagement, self, name)
        self.projekte[name] = projekt
        self.projektnamen += [name]
        self.projektmanagement.add(projekt, text = name)
        self.projektzahl += 1

    def _projekt_schliessen(self):
        name = self.projektmanagement.tab(self.projektmanagement.select(), "text")
        self.projektmanagement.forget(self.projektmanagement.select())
        del self.projekte[name]
        self.projektnamen.remove(name)



class Projekt(tk.Frame):
    def __init__(self, parent, controller, name):
        tk.Frame.__init__(self, parent)
        tk.Frame.grid_rowconfigure(self, 0, weight = 1)
        tk.Frame.grid_columnconfigure(self, 0, weight = 0)
        tk.Frame.grid_columnconfigure(self, 1, weight = 1)
        
        self.controller = controller
        self.name = name
        self.Koerper = None
        self.shape = None
        self.matrixraum = [0, [0, 0], [0, 0]]
        self.faktormodus = False
        self.images = []
    
        # Einstellungen
        self.einstellungen = tk.Frame(self, width = 300)
        self.einstellungen.grid(row = 0, column = 0, sticky = 'nsew')
        # Voxelkoerpereingabe
        # Button-Import
        self.importbutton = tk.Button(self.einstellungen, text = 'Körper importieren')
        self.importbutton.place(x = 5, y = 5, width = 285, height = 20)
        self.importbutton['command'] = lambda: self.koerperuebernahme()
        # Raumerweiterung
        self.xr = tk.Entry(self.einstellungen, justify = 'center')
        self.xr.place(x = 5, y = 50, width = 50, height = 20)
        self.xr.insert(0, '1')
        self.yh = tk.Entry(self.einstellungen, justify = 'center')
        self.yh.place(x = 85, y = 50, width = 25, height = 20)
        self.yh.insert(0, '6')
        self.yv = tk.Entry(self.einstellungen, justify = 'center')
        self.yv.place(x = 60, y = 50, width = 25, height = 20)
        self.yv.insert(0, '1')
        self.zu = tk.Entry(self.einstellungen, justify = 'center')
        self.zu.place(x = 115, y = 50, width = 25, height = 20)
        self.zu.insert(0, '1')
        self.zo = tk.Entry(self.einstellungen, justify = 'center')
        self.zo.place(x = 140, y = 50, width = 25, height = 20)
        self.zo.insert(0, '1')
        tk.Label(self.einstellungen, text = 'X').place(x = 5, y = 30, width = 50, height = 20)
        tk.Label(self.einstellungen, text = 'v Y h').place(x = 60, y = 30, width = 50, height = 20)
        tk.Label(self.einstellungen, text = 'o Z u').place(x = 115, y = 30, width = 50, height = 20)
        # Button Uebernahmen
        self.normal = tk.Button(self.einstellungen, text = 'übernehmen')
        self.normal.place(x = 170, y = 30, width = 120, height = 20)
        self.normal['command'] = lambda: self.matrixerweiterung(False)
        self.faktor = tk.Button(self.einstellungen, text = 'faktor übernehmen')
        self.faktor.place(x = 170, y = 50, width = 120, height = 20)
        self.faktor['command'] = lambda: self.matrixerweiterung(True)
        # Visualisierung
        self.voxelansicht = plt.figure()
        plt.subplots_adjust(left = 0.01, right = 0.99, bottom = 0.01, top = 0.99)
        plt.close()
        plt.ion()
        self.voxeldarstellung = FigureCanvasTkAgg(self.voxelansicht, master = self.einstellungen)
        self.voxeldarstellung.get_tk_widget().place(x = 5, y = 75, width = 285, height = 285)
        self.voxelgraph = self.voxelansicht.add_subplot(111, projection = '3d')
        
        # Fließgeschwindigkeit und Viskosität
        tk.Label(self.einstellungen, text = 'Fließgeschwindigkeit').place(x = 5, y = 370, width = 120, height = 20)
        self.speed_eingabe = tk.Entry(self.einstellungen, justify = 'center')
        self.speed_eingabe.place(x = 170, y = 370, width = 120, height = 20)
        self.speed_eingabe.insert(0, '0.18')
        tk.Label(self.einstellungen, text = 'Viskosität').place(x = 5, y = 390, width = 120, height = 20)
        self.vi_eingabe = tk.Entry(self.einstellungen, justify = 'center')
        self.vi_eingabe.place(x = 170, y = 390, width = 120, height = 20)
        self.vi_eingabe.insert(0, '0.01')
        # Simulationszyklen
        tk.Label(self.einstellungen, text = 'Simulationszyklen').place(x = 5, y = 420, width = 120, height = 20)
        self.zyklen = tk.Entry(self.einstellungen, justify = 'center')
        self.zyklen.place(x = 170, y = 420, width = 120, height = 20)
        self.zyklen.insert(0, '10')
        tk.Label(self.einstellungen, text = 'Darstellungszyklen').place(x = 5, y = 440, width = 120, height = 20)
        self.darste = tk.Entry(self.einstellungen, justify = 'center')
        self.darste.place(x = 170, y = 440, width = 120, height = 20)
        self.darste.insert(0, '50')
        # Visualisierungen
        self.untergrund = tk.Frame(self, bg = 'white')
        self.untergrund.grid(row = 0, column = 1, sticky = 'nsew')
        self.untergrund.grid_rowconfigure(0, weight = 1)
        self.untergrund.grid_columnconfigure(0, weight = 1)
        # Startbutton
        self.startb = tk.Button(self.einstellungen, text = 'Start')
        self.startb.place(x = 5, y = 510, width = 100, height = 20)
        self.startb['command'] = lambda: self.start()
        #self.startb['command'] = lambda: self.makethegif()
        # Cw Buttons
        self.cw_14 = tk.BooleanVar()
        self.cw_20 = tk.BooleanVar()
        self.cw14 = tk.Checkbutton(self.einstellungen, text = 'Cw-14', variable = self.cw_14)
        self.cw14['command'] = lambda: self.change_cw20()
        self.cw14.place(x = 5, y = 470, width = 100, height = 20)
        self.cw20 = tk.Checkbutton(self.einstellungen, text = 'Cw-20', variable = self.cw_20)
        self.cw20['command'] = lambda: self.change_cw14()
        self.cw20.place(x = 5, y = 490, width = 100, height = 20)
        
        self.figure = plt.figure(figsize = (1, 1))
        plt.subplots_adjust(left = 0.04, right = 0.96, bottom = 0.04, top = 0.96)
        plt.ion()
        plt.close()
        self.canvas = FigureCanvasTkAgg(self.figure, master = self.untergrund)
        self.canvas.get_tk_widget().grid(row = 0, column = 0, sticky = 'nsew')
        self.canvas.get_tk_widget().configure(relief = 'groove', borderwidth = 2)
        self.graph = self.figure.add_subplot(221, projection = '3d')
        self.flowgraph = self.figure.add_subplot(222, projection = '3d')
        self.forcegraph = self.figure.add_subplot(223)
        self.forcegraph.set_title('Kraft')
        self.lastgraph = self.figure.add_subplot(223, frame_on = False)
        self.lastgraph.xaxis.tick_top()
        self.lastgraph.yaxis.tick_right()
        self.cwgraph = self.figure.add_subplot(224)

        # Strömungsbild erstellen
        self.makeflowpicture = tk.BooleanVar()
        self.frontbild = tk.BooleanVar()
        self.seitenbild = tk.BooleanVar()
        self.draufbild = tk.BooleanVar()
        self.schraegbild = tk.BooleanVar()
        self.check_flow = tk.Checkbutton(self.einstellungen, text = 'Strömungsbild erstellen', variable = self.makeflowpicture, anchor = 'w')
        self.check_flow['command'] = lambda: self.change_stroemungsbild()
        self.check_flow.place(x = 150, y = 470, width = 150, height = 20)

        self.check_front = tk.Checkbutton(self.einstellungen, text = 'Frontansicht', variable = self.frontbild, anchor = 'w', state = 'disabled')
        self.check_front.place(x = 160, y = 490, width = 150, height = 20)
        self.check_side = tk.Checkbutton(self.einstellungen, text = 'Seitenansicht', variable = self.seitenbild, anchor = 'w', state = 'disabled')
        self.check_side.place(x = 160, y = 510, width = 150, height = 20)
        self.check_top = tk.Checkbutton(self.einstellungen, text = 'Draufsicht', variable = self.draufbild, anchor = 'w', state = 'disabled')
        self.check_top.place(x = 160, y = 530, width = 150, height = 20)
        self.check_3d = tk.Checkbutton(self.einstellungen, text = '3D-Ansicht', variable = self.schraegbild, anchor ='w', state ='disabled')
        self.check_3d.place(x = 160, y = 550, width = 150, height = 20)

        tk.Label(self.einstellungen, text = 'Sieb:').place(x = 170, y = 570, width = 50, height = 20)
        self.siebfaktor = tk.Entry(self.einstellungen)
        self.siebfaktor.place(x = 225, y = 570, width = 40, height = 20)
        self.siebfaktor.insert(0, '2')
        # Cw Label
        self.cw_label = tk.Label(self.einstellungen, bg = 'lightgrey')
        self.cw_label.place(x = 5, y = 530, width = 100, height = 20)


    def change_stroemungsbild(self):
        if self.makeflowpicture.get() == True:
            self.check_front.configure(state = 'normal')
            self.check_side.configure(state = 'normal')
            self.check_top.configure(state = 'normal')
            self.check_3d.configure(state = 'normal')
        else:
            self.check_front.configure(state = 'disabled')
            self.check_side.configure(state = 'disabled')
            self.check_top.configure(state = 'disabled')
            self.check_3d.configure(state = 'disabled')


    def change_cw14(self):
        self.speed_eingabe.delete(0, 'end')
        self.speed_eingabe.insert(0, '0.18')
        self.vi_eingabe.delete(0, 'end')
        self.vi_eingabe.insert(0, '0.022')
        self.cw14.deselect()


    def change_cw20(self):
        self.speed_eingabe.delete(0, 'end')
        self.speed_eingabe.insert(0, '0.18')
        self.vi_eingabe.delete(0, 'end')
        self.vi_eingabe.insert(0, '0.012')
        self.cw20.deselect()


    def start(self):
        try:
            if type(self.Koerper) != type(None):
                self.graph.clear()
                self.flowgraph.clear()
                self.forcegraph.clear()
                self.lastgraph.clear()
                self.cwgraph.clear()

                self.images = []
                if self.makeflowpicture.get():
                    giffig = plt.figure()
                    plt.subplots_adjust(left = 0.01, right = 0.99, bottom = 0.01, top = 0.99)
                    plt.ion()
                    plt.close()
                    gifaxis = giffig.add_subplot(111, projection = '3d')
                    

                self.Hinderniss = self.Koerper
                self.aufloesung = self.Hinderniss.shape
                # Barriere -> Hinderniswand
                self.Hinderniswand_mN = np.roll(self.Hinderniss,         1, axis = 0)
                self.Hinderniswand_mS = np.roll(self.Hinderniss,        -1, axis = 0)
                self.Hinderniswand_mE = np.roll(self.Hinderniss,         1, axis = 1)
                self.Hinderniswand_mW = np.roll(self.Hinderniss,        -1, axis = 1)
                self.Hinderniswand_mNE = np.roll(self.Hinderniswand_mN,   1, axis = 1)
                self.Hinderniswand_mNW = np.roll(self.Hinderniswand_mN,  -1, axis = 1)
                self.Hinderniswand_mSE = np.roll(self.Hinderniswand_mS,   1, axis = 1)
                self.Hinderniswand_mSW = np.roll(self.Hinderniswand_mS,  -1, axis = 1)

                self.Hinderniswand_oN = np.roll(self.Hinderniswand_mN, 1, axis = 2)
                self.Hinderniswand_oS = np.roll(self.Hinderniswand_mS, 1, axis = 2)
                self.Hinderniswand_oE = np.roll(self.Hinderniswand_mE, 1, axis = 2)
                self.Hinderniswand_oW = np.roll(self.Hinderniswand_mW, 1, axis = 2)
                self.Hinderniswand_oO = np.roll(self.Hinderniss, 1, axis = 2)

                self.Hinderniswand_uN = np.roll(self.Hinderniswand_mN, -1, axis = 2)
                self.Hinderniswand_uS = np.roll(self.Hinderniswand_mS, -1, axis = 2)
                self.Hinderniswand_uE = np.roll(self.Hinderniswand_mE, -1, axis = 2)
                self.Hinderniswand_uW = np.roll(self.Hinderniswand_mW, -1, axis = 2)
                self.Hinderniswand_uU = np.roll(self.Hinderniss, -1, axis = 2)

                self.durch3  = 1 /  3.001
                self.durch18 = 1 / 18.0
                self.durch36 = 1 / 36.0

                self.viskositaet = float(self.vi_eingabe.get())
                self.F_visk = 1 / (3 * self.viskositaet + 0.5)
                self.speed = float(self.speed_eingabe.get())
                self.Re = self.speed / self.viskositaet
                # n -> Pfeile
                self.Pfeile_0     = self.durch3    * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)

                self.Pfeile_uU    = self.durch18   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_uN    = self.durch36   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_uS    = self.durch36   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_uE    = self.durch36   * (np.ones(self.aufloesung) + 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_uW    = self.durch36   * (np.ones(self.aufloesung) - 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)

                self.Pfeile_mN    = self.durch18   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_mS    = self.durch18   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_mE    = self.durch18   * (np.ones(self.aufloesung) + 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_mW    = self.durch18   * (np.ones(self.aufloesung) - 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_mNE   = self.durch36   * (np.ones(self.aufloesung) + 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_mSE   = self.durch36   * (np.ones(self.aufloesung) + 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_mNW   = self.durch36   * (np.ones(self.aufloesung) - 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_mSW   = self.durch36   * (np.ones(self.aufloesung) - 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)

                self.Pfeile_oN    = self.durch36   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_oS    = self.durch36   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)
                self.Pfeile_oE    = self.durch36   * (np.ones(self.aufloesung) + 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_oW    = self.durch36   * (np.ones(self.aufloesung) - 3 * self.speed + 4.5 * self.speed ** 2 - 1.5 * self.speed ** 2)
                self.Pfeile_oO    = self.durch18   * (np.ones(self.aufloesung) - 1.5 * self.speed ** 2)

                self.Sum    = self.Pfeile_0 + self.Pfeile_uN + self.Pfeile_uS + self.Pfeile_uE + self.Pfeile_uW +  self.Pfeile_mN + self.Pfeile_mS + \
                              self.Pfeile_mE + self.Pfeile_mW + self.Pfeile_mNE + self.Pfeile_mSE + self.Pfeile_mNW + self.Pfeile_mSW+ self.Pfeile_oN + \
                              self.Pfeile_oS + self.Pfeile_oE + self.Pfeile_oW + self.Pfeile_oO + self.Pfeile_uU 
                self.vx     = (self.Pfeile_uE + self.Pfeile_mE + self.Pfeile_mNE + self.Pfeile_mSE + self.Pfeile_oE \
                               - self.Pfeile_uW - self.Pfeile_mW - self.Pfeile_mNW - self.Pfeile_mSW - self.Pfeile_oW) / self.Sum				
                self.vy     = (self.Pfeile_uN + self.Pfeile_mN + self.Pfeile_mNE + self.Pfeile_mNW + self.Pfeile_oN \
                               - self.Pfeile_uS - self.Pfeile_mS - self.Pfeile_mSE - self.Pfeile_mSW - self.Pfeile_oS) / self.Sum				
                self.vz     = (self.Pfeile_oN + self.Pfeile_oE + self.Pfeile_oS  + self.Pfeile_oW  + self.Pfeile_oO \
                               - self.Pfeile_uN - self.Pfeile_uE - self.Pfeile_uS - self.Pfeile_uW - self.Pfeile_uU) / self.Sum # neu komplett abends


                self.hauptachsen = [int(self.Hinderniss.shape[0] / 2),
                                    int(self.Hinderniss.shape[1] / 2),
                                    int(self.Hinderniss.shape[2] / 2)]

                feine = int(self.siebfaktor.get())
                self.sieb = [np.zeros((1, self.Hinderniss.shape[1], self.Hinderniss.shape[2]), bool),
                             np.zeros((self.Hinderniss.shape[0], 1, self.Hinderniss.shape[2]), bool),
                             np.zeros((self.Hinderniss.shape[0], self.Hinderniss.shape[1], 1), bool)]
                for x in range(self.Hinderniss.shape[0]):
                    for y in range(self.Hinderniss.shape[1]):
                        for z in range(self.Hinderniss.shape[2]):
                            if y % feine == 0 and z % feine == 0:
                                self.sieb[0][0][y][z] = True
                            if x % feine == 0 and z % feine == 0:
                                self.sieb[1][x][0][z] = True
                            if x % feine == 0 and y % feine == 0:
                                self.sieb[2][x][y][0] = True

                zaehler_flaeche = 0
                groesse = self.Hinderniss.shape
                for Xx in range(0, groesse[0], 1):
                    for Zz in range(0, groesse[2], 1):
                        for Yy in range(0, groesse[1], 1):
                            if self.Hinderniss[Xx][Yy][Zz]:
                                zaehler_flaeche += 1
                                break
                self.flaeche = zaehler_flaeche
                self.cw_werte = []
                
                i = 0
                j = int(self.zyklen.get())
                k = int(self.darste.get())
                while i < j:
                    self.Stroemungsschrit()
                    self.Kollisionsschrit()
                    f = self.force()
                    self.forcegraph.scatter([i], [f], color = 'blue', s = 2)
                    self.cwgraph.scatter([i], [f / self.flaeche], color ='blue', s = 2)
                    if i >= (j - 100):
                        self.lastgraph.scatter([i], [f], color = 'red', s = 2)
                    if i % k == 0 and i > 0:
                        self.show()
                    if i % 10 == 0:
                        self.multipicture(gifaxis, giffig, i)
                        self.images += ['multipic' + str(i) + '.png']
                        print('{} / '.format(i) + str(j))
                    if j - i <= 400:
                        self.cw_werte += [f / self.flaeche]
                    i += 1
                    print(i)
                if self.makeflowpicture.get():
                    self.makeflowlines(gifaxis, giffig, -i)
                    self.makepicture(gifaxis, giffig, i)
                self.forcegraph.set_title('Kraft')
                self.cwgraph.set_title('Cw-Wert')
                self.flowshow()
                # cw-wert ausgeben
                if self.cw_14.get():
                    ergebnis_cw = (564.7 * self.cw_durchschnitt() * 10000 - 767) * self.cw_durchschnitt()
                elif self.cw_20.get():
                    ergebnis_cw = (639.6 * self.cw_durchschnitt() * 10000 - 1206.7) * self.cw_durchschnitt()
                else:
                    ergebnis_cw = 0.0
                self.cw_label.configure(text = str(round(ergebnis_cw, 6)))
                self.makethegif()
                
        except NameError:
            print('Exception')
            pass


    def cw_durchschnitt(self):
        summe = 0
        for c in self.cw_werte:
            summe += c
        return summe / len(self.cw_werte)


    def multipicture(self, axis, fig, i):
        axis.clear()
        axis.voxels(self.Hinderniss, color = 'white', edgecolor = 'black')
        a, b, c = np.meshgrid(np.linspace(0.5, (self.Hinderniss.shape[1] - 0.5), self.Hinderniss.shape[1]),
                              np.linspace(0.5, (self.Hinderniss.shape[0] - 0.5), self.Hinderniss.shape[0]),
                              np.linspace(0.5, (self.Hinderniss.shape[2] - 0.5), self.Hinderniss.shape[2]) )
        for d in [0]:
            l = list(range(self.Hinderniss.shape[d]))
            l = l[0 : int(self.Hinderniss.shape[d] / 2)] + l[int(self.Hinderniss.shape[d] / 2) + 1 : ]
            pb = np.delete(b, l, d)[self.sieb[d]]
            pa = np.delete(a, l, d)[self.sieb[d]]
            pc = np.delete(c, l, d)[self.sieb[d]]
            rx = np.delete(self.vx, l, d)[self.sieb[d]] * 25
            ry = np.delete(self.vy, l, d)[self.sieb[d]] * 25
            rz = np.delete(self.vz, l, d)[self.sieb[d]] * 25
            axis.quiver(pb, pa, pc, ry, rx, rz, cmap = 'prism', normalize = False, alpha = 1, linewidth = rx.reshape(-1) / 5)

        self.daten = self.vx * 4
        colors = plt.cm.hsv(self.daten)
        colors[self.Hinderniss] = [0, 0, 0, 1]
        # Axis 0
        y, z = np.meshgrid(np.linspace(0, self.daten.shape[1], self.daten.shape[1] + 1),
                           np.linspace(0 + self.daten.shape[2] + 5, self.daten.shape[2] + self.daten.shape[2] + 5, self.daten.shape[2] + 1) )
        x = (self.hauptachsen[0] + 0.5) * np.ones(z.shape)
        matrix = self._zugriff(colors, 0, self.hauptachsen[0])
        axis.plot_surface(x, y, z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.5)
        
        axis.set_xlim(max(self.Hinderniss.shape) * 0.25, max(self.Hinderniss.shape) * 0.75)
        axis.set_ylim(max(self.Hinderniss.shape) * 0.25, max(self.Hinderniss.shape) * 0.75)
        axis.set_zlim(max(self.Hinderniss.shape) * 0.25, max(self.Hinderniss.shape) * 0.75)
        axis.set_axis_off()
        axis.set_facecolor((1, 1, 1, 1))
        axis.view_init(0, 0)
        fig.savefig('multipic' + str(i) + '.png', dpi = 150)


    def makeflowlines(self, axis, fig, i):
        axis.clear()
        axis.voxels(self.Hinderniss, color = 'white', edgecolor = 'black')
        a, b, c = np.meshgrid(np.linspace(0.5, (self.Hinderniss.shape[1] - 0.5), self.Hinderniss.shape[1]),
                              np.linspace(0.5, (self.Hinderniss.shape[0] - 0.5), self.Hinderniss.shape[0]),
                              np.linspace(0.5, (self.Hinderniss.shape[2] - 0.5), self.Hinderniss.shape[2]) )
        for d in [0]:
            l = list(range(self.Hinderniss.shape[d]))
            l = l[0 : int(self.Hinderniss.shape[d] / 2)] + l[int(self.Hinderniss.shape[d] / 2) + 1 : ]
            pb = np.delete(b, l, d)[self.sieb[d]]
            pa = np.delete(a, l, d)[self.sieb[d]]
            pc = np.delete(c, l, d)[self.sieb[d]]
            rx = np.delete(self.vx, l, d)[self.sieb[d]] * 25
            ry = np.delete(self.vy, l, d)[self.sieb[d]] * 25
            rz = np.delete(self.vz, l, d)[self.sieb[d]] * 25
            axis.quiver(pb, pa, pc, ry, rx, rz, cmap = 'prism', normalize = False, alpha = 1, linewidth = rx.reshape(-1) / 5)#26)

        axis.set_xlim(max(self.Hinderniss.shape) * 0.2, max(self.Hinderniss.shape) * 0.8)
        axis.set_ylim(max(self.Hinderniss.shape) * 0.2, max(self.Hinderniss.shape) * 0.8)
        axis.set_zlim(max(self.Hinderniss.shape) * 0.2, max(self.Hinderniss.shape) * 0.8)
        axis.set_axis_off()
        axis.set_facecolor((1, 1, 1, 1))
        if self.seitenbild.get():
            axis.view_init(0, 0)
            fig.savefig('s bild' + str(i) + '.png', dpi = 1000)
        if self.draufbild.get():
            axis.view_init(-90, 0)
            fig.savefig('o bild' + str(i) + '.png', dpi = 1000)
        if self.schraegbild.get():
            axis.view_init(45, -45)
            fig.savefig('d bild' + str(i) + '.png', dpi = 1000)
        if self.frontbild.get():
            axis.view_init(0, -90)
            fig.savefig('f bild' + str(i) + '.png', dpi = 1000)


    def makepicture(self, axis, fig, i):
        axis.clear()
        axis.voxels(self.Hinderniss, color = 'white', edgecolor = 'white')
        self.daten = self.vx * 4
        colors = plt.cm.hsv(self.daten)
        colors[self.Hinderniss] = [0, 0, 0, 1]
        # Axis 0
        y, z = np.meshgrid(np.linspace(0, self.daten.shape[1], self.daten.shape[1] + 1),
                           np.linspace(0, self.daten.shape[2], self.daten.shape[2] + 1) )
        x = (self.hauptachsen[0] + 0.5) * np.ones(z.shape)
        matrix = self._zugriff(colors, 0, self.hauptachsen[0])
        axis.plot_surface(x, y, z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.3)
        # Axis 1
        x, z = np.meshgrid(np.linspace(0, self.daten.shape[0], self.daten.shape[0] + 1),
                           np.linspace(0, self.daten.shape[2], self.daten.shape[2] + 1) )
        y = (self.hauptachsen[1] + 0.5) * np.ones(z.shape)
        matrix = self._zugriff(colors, 1, self.hauptachsen[1])
        axis.plot_surface(x, y, z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.3)
        # Axis 2
        x, y = np.meshgrid(np.linspace(0, self.daten.shape[0], self.daten.shape[0] + 1),
                           np.linspace(0, self.daten.shape[1], self.daten.shape[1] + 1) )
        z = (self.hauptachsen[2] + 0.5) * np.ones(x.shape)
        matrix = self._zugriff(colors, 2, self.hauptachsen[2])
        axis.plot_surface(x, y, z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.3)
        axis.set_xlim(0, max(self.Hinderniss.shape) * 1)
        axis.set_ylim(0, max(self.Hinderniss.shape) * 1)
        axis.set_zlim(0, max(self.Hinderniss.shape) * 1)
        axis.set_axis_off()
        axis.set_facecolor((0, 0, 0, 1))

        if self.frontbild.get():
            axis.view_init(0, -90)
            fig.savefig('f bild a' + str(i) + '.png', dpi = 1000)
        if self.seitenbild.get():
            axis.view_init(0, 0)
            fig.savefig('s bild a' + str(i) + '.png', dpi = 1000)
        if self.draufbild.get():
            axis.view_init(-90, 0)
            fig.savefig('o bild a' + str(i) + '.png', dpi = 1000)
        if self.schraegbild.get():
            axis.view_init(45, -45)
            fig.savefig('d bild a' + str(i) + '.png', dpi = 1000)


    def makethegif(self):
        with imageio.get_writer('multigif.gif', mode = 'I') as writer:
            for i in range(0, len(self.images), 1):
                filename = self.images[i]
                image = imageio.imread(filename)
                writer.append_data(image)


    def Stroemungsschrit(self):
        self.Pfeile_mN  = np.roll(self.Pfeile_mN,   1, axis=0)	
        self.Pfeile_mNE = np.roll(self.Pfeile_mNE,  1, axis=0)
        self.Pfeile_mNW = np.roll(self.Pfeile_mNW,  1, axis=0)
        self.Pfeile_mS  = np.roll(self.Pfeile_mS,  -1, axis=0)
        self.Pfeile_mSE = np.roll(self.Pfeile_mSE, -1, axis=0)
        self.Pfeile_mSW = np.roll(self.Pfeile_mSW, -1, axis=0)
        self.Pfeile_mE  = np.roll(self.Pfeile_mE,   1, axis=1)	
        self.Pfeile_mNE = np.roll(self.Pfeile_mNE,  1, axis=1)
        self.Pfeile_mSE = np.roll(self.Pfeile_mSE,  1, axis=1)
        self.Pfeile_mW  = np.roll(self.Pfeile_mW,  -1, axis=1)
        self.Pfeile_mNW = np.roll(self.Pfeile_mNW, -1, axis=1)
        self.Pfeile_mSW = np.roll(self.Pfeile_mSW, -1, axis=1)

        self.Pfeile_uU  = np.roll(self.Pfeile_uU,          -1, axis=2)
        self.Pfeile_uN  = np.roll(np.roll(self.Pfeile_uN,  -1, axis=2),   1, axis=0)	
        self.Pfeile_uS  = np.roll(np.roll(self.Pfeile_uS,  -1, axis=2),  -1, axis=0)
        self.Pfeile_uE  = np.roll(np.roll(self.Pfeile_uE,  -1, axis=2),   1, axis=1)	
        self.Pfeile_uW  = np.roll(np.roll(self.Pfeile_uW,  -1, axis=2),  -1, axis=1)

        self.Pfeile_oN  = np.roll(np.roll(self.Pfeile_oN,   1, axis=2),   1, axis=0)	
        self.Pfeile_oS  = np.roll(np.roll(self.Pfeile_oS,   1, axis=2),  -1, axis=0)
        self.Pfeile_oE  = np.roll(np.roll(self.Pfeile_oE,   1, axis=2),   1, axis=1)	
        self.Pfeile_oW  = np.roll(np.roll(self.Pfeile_oW,   1, axis=2),  -1, axis=1)
        self.Pfeile_oO  = np.roll(self.Pfeile_oO,           1, axis=2)

        self.Pfeile_mN[self.Hinderniswand_mN]   = self.Pfeile_mS[self.Hinderniss]
        self.Pfeile_mS[self.Hinderniswand_mS]   = self.Pfeile_mN[self.Hinderniss]
        self.Pfeile_mE[self.Hinderniswand_mE]   = self.Pfeile_mW[self.Hinderniss]
        self.Pfeile_mW[self.Hinderniswand_mW]   = self.Pfeile_mE[self.Hinderniss]
        
        self.Pfeile_mNE[self.Hinderniswand_mNE] = self.Pfeile_mSW[self.Hinderniss]
        self.Pfeile_mNW[self.Hinderniswand_mNW] = self.Pfeile_mSE[self.Hinderniss]
        self.Pfeile_mSE[self.Hinderniswand_mSE] = self.Pfeile_mNW[self.Hinderniss]
        self.Pfeile_mSW[self.Hinderniswand_mSW] = self.Pfeile_mNE[self.Hinderniss]


        self.Pfeile_oN[self.Hinderniswand_oN] = self.Pfeile_uS[self.Hinderniss]
        self.Pfeile_oS[self.Hinderniswand_oS] = self.Pfeile_uN[self.Hinderniss]
        self.Pfeile_oE[self.Hinderniswand_oE] = self.Pfeile_uW[self.Hinderniss]
        self.Pfeile_oW[self.Hinderniswand_oW] = self.Pfeile_uE[self.Hinderniss]
        self.Pfeile_oO[self.Hinderniswand_oO] = self.Pfeile_uU[self.Hinderniss]

        self.Pfeile_uN[self.Hinderniswand_uN] = self.Pfeile_oS[self.Hinderniss]
        self.Pfeile_uS[self.Hinderniswand_uS] = self.Pfeile_oN[self.Hinderniss]
        self.Pfeile_uE[self.Hinderniswand_uE] = self.Pfeile_oW[self.Hinderniss]
        # self.Pfeile_uW[self.Hinderniswand_uW] = self.Pfeile_oE[self.Hinderniss]
        self.Pfeile_uU[self.Hinderniswand_uU] = self.Pfeile_oO[self.Hinderniss]
        """ If you want to see vortex drag behind the body you have to comment out one of the last lines of the streaming step (Strömungsschritt) in order to
         create a imbalance in the system, otherwise the fluid flow will stay straight. If you choose a theoretigal Reynold Number of
         above 20 (e.g.: Velocity = 0.24, Viscosity = 0.01) you can see the vortices after roughly 2000 simulation steps (3-5 min calculation time).
         However, keep in mind that as soon as the vortices appear in the simulation the determination of the drag coefficient does not work anymore. """


    def Kollisionsschrit(self):
        self.Sum = self.Pfeile_0   + self.Pfeile_uN  + self.Pfeile_uS + self.Pfeile_uE + self.Pfeile_uW  + self.Pfeile_uU  + \
                   self.Pfeile_mN  + self.Pfeile_mS  + self.Pfeile_mE + self.Pfeile_mW + self.Pfeile_mNE + self.Pfeile_mNW + \
                   self.Pfeile_mSE + self.Pfeile_mSW + self.Pfeile_oN + self.Pfeile_oS + self.Pfeile_oE  + self.Pfeile_oW  + self.Pfeile_oO 
        self.vx = (self.Pfeile_mE + self.Pfeile_mNE + self.Pfeile_mSE + self.Pfeile_uE + self.Pfeile_oE -
                   self.Pfeile_mW - self.Pfeile_mNW - self.Pfeile_mSW - self.Pfeile_uW - self.Pfeile_oW) / self.Sum    
        self.vy = (self.Pfeile_mN + self.Pfeile_mNE + self.Pfeile_mNW + self.Pfeile_uN + self.Pfeile_oN -
                   self.Pfeile_mS - self.Pfeile_mSE - self.Pfeile_mSW - self.Pfeile_uS - self.Pfeile_oS) / self.Sum 
        self.vz = (self.Pfeile_oN + self.Pfeile_oE  + self.Pfeile_oS  + self.Pfeile_oW + self.Pfeile_oO -
                   self.Pfeile_uN - self.Pfeile_uE  - self.Pfeile_uS  - self.Pfeile_uW - self.Pfeile_uU) / self.Sum

        vx2     = self.vx * self.vx				
        vy2     = self.vy * self.vy
        vz2     = self.vz * self.vz
        v3      = vx2 + vy2 + vz2
        vxvy2   = self.vx * self.vy * 2
        vzvy2   = self.vz * self.vy * 2
        vzvx2   = self.vz * self.vx * 2
        F_v3  = 1 - 1.5*v3

        self.Pfeile_0 = (1 - self.F_visk) * self.Pfeile_0 + self.F_visk * self.durch3 * self.Sum * F_v3     
        
        self.Pfeile_mN  = (1 - self.F_visk) * self.Pfeile_mN  + self.F_visk * self.durch18 * self.Sum * (F_v3 + 3 * self.vy + 4.5 * vy2)
        self.Pfeile_mS  = (1 - self.F_visk) * self.Pfeile_mS  + self.F_visk * self.durch18 * self.Sum * (F_v3 - 3 * self.vy + 4.5 * vy2)
        self.Pfeile_mE  = (1 - self.F_visk) * self.Pfeile_mE  + self.F_visk * self.durch18 * self.Sum * (F_v3 + 3 * self.vx + 4.5 * vx2)
        self.Pfeile_mW  = (1 - self.F_visk) * self.Pfeile_mW  + self.F_visk * self.durch18 * self.Sum * (F_v3 - 3 * self.vx + 4.5 * vx2)
        self.Pfeile_mNE = (1 - self.F_visk) * self.Pfeile_mNE + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * ( self.vx+self.vy) + 4.5 * (vx2+vxvy2+vy2))
        self.Pfeile_mNW = (1 - self.F_visk) * self.Pfeile_mNW + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * (-self.vx+self.vy) + 4.5 * (vx2-vxvy2+vy2))  
        self.Pfeile_mSE = (1 - self.F_visk) * self.Pfeile_mSE + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * ( self.vx-self.vy) + 4.5 * (vx2-vxvy2+vy2))    
        self.Pfeile_mSW = (1 - self.F_visk) * self.Pfeile_mSW + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * (-self.vx-self.vy) + 4.5 * (vx2+vxvy2+vy2))     

        self.Pfeile_uN  = (1 - self.F_visk) * self.Pfeile_uN  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * ( self.vy-self.vz) + 4.5 * (vy2-vzvy2+vz2))
        self.Pfeile_uS  = (1 - self.F_visk) * self.Pfeile_uS  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * (-self.vy-self.vz) + 4.5 * (vy2+vzvy2+vz2))
        self.Pfeile_uE  = (1 - self.F_visk) * self.Pfeile_uE  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * ( self.vx-self.vz) + 4.5 * (vx2-vzvx2+vz2))
        self.Pfeile_uW  = (1 - self.F_visk) * self.Pfeile_uW  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * (-self.vx-self.vz) + 4.5 * (vx2+vzvx2+vz2))
        self.Pfeile_uU  = (1 - self.F_visk) * self.Pfeile_uU  + self.F_visk * self.durch18 * self.Sum * (F_v3 - 3 * self.vz + 4.5*vz2)
        
        self.Pfeile_oN  = (1 - self.F_visk) * self.Pfeile_oN  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * ( self.vy+self.vz) + 4.5 * (vy2+vzvy2+vz2))
        self.Pfeile_oS  = (1 - self.F_visk) * self.Pfeile_oS  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * (-self.vy+self.vz) + 4.5 * (vy2-vzvy2+vz2))
        self.Pfeile_oE  = (1 - self.F_visk) * self.Pfeile_oE  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * ( self.vx+self.vz) + 4.5 * (vx2+vzvx2+vz2))
        self.Pfeile_oW  = (1 - self.F_visk) * self.Pfeile_oW  + self.F_visk * self.durch36 * self.Sum * (F_v3 + 3 * (-self.vx+self.vz) + 4.5 * (vx2-vzvx2+vz2))
        self.Pfeile_oO  = (1 - self.F_visk) * self.Pfeile_oO  + self.F_visk * self.durch18 * self.Sum * (F_v3 + 3 * self.vz + 4.5 * vz2)

        
        self.Pfeile_mE[:,0] = self.durch18 * (1 + 3*self.speed + 4.5*self.speed**2 - 1.5*self.speed**2) 
        self.Pfeile_mW[:,0] = self.durch18 * (1 - 3*self.speed + 4.5*self.speed**2 - 1.5*self.speed**2)


    def force(self):
        x_kraft = self.Pfeile_mE[self.Hinderniss] * self.durch18 + self.Pfeile_mNE[self.Hinderniss] * self.durch36 + \
                  self.Pfeile_mSE[self.Hinderniss] * self.durch36 + self.Pfeile_uE[self.Hinderniss] * self.durch36 + self.Pfeile_oE[self.Hinderniss] * self.durch36 \
                 - self.Pfeile_mW[self.Hinderniss] * self.durch18 - self.Pfeile_mNW[self.Hinderniss] * self.durch36 - \
                 self.Pfeile_mSW[self.Hinderniss] * self.durch36 - self.Pfeile_uW[self.Hinderniss] * self.durch36 - self.Pfeile_oW[self.Hinderniss] * self.durch36
        return x_kraft.sum()


    def show(self):
        self.graph.clear()
        self.graph.voxels(self.Hinderniss, color = 'white', edgecolor = 'white')
        self.daten = self.vx * 4
        colors = plt.cm.hsv(self.daten)
        colors[self.Hinderniss] = [1, 1, 1, 0]
        # Axis 0
        Y, Z = np.meshgrid(np.linspace(0, self.daten.shape[1], self.daten.shape[1] + 1),
                           np.linspace(0, self.daten.shape[2], self.daten.shape[2] + 1) )
        X = (self.hauptachsen[0] + 0.5) * np.ones(Z.shape)
        matrix = self._zugriff(colors, 0, self.hauptachsen[0])
        self.graph.plot_surface(X, Y, Z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.3)
        # Axis 1
        X, Z = np.meshgrid(np.linspace(0, self.daten.shape[0], self.daten.shape[0] + 1),
                           np.linspace(0, self.daten.shape[2], self.daten.shape[2] + 1) )
        Y = (self.hauptachsen[1] + 0.5) * np.ones(Z.shape)
        matrix = self._zugriff(colors, 1, self.hauptachsen[1])
        self.graph.plot_surface(X, Y, Z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.3)
        # Axis 2
        X, Y = np.meshgrid(np.linspace(0, self.daten.shape[0], self.daten.shape[0] + 1),
                           np.linspace(0, self.daten.shape[1], self.daten.shape[1] + 1) )
        Z = (self.hauptachsen[2] + 0.5) * np.ones(X.shape)
        matrix = self._zugriff(colors, 2, self.hauptachsen[2])
        self.graph.plot_surface(X, Y, Z, rstride = 1, cstride = 1, facecolors = matrix,
                          linewidth = 0, shade = False, alpha = 0.3)
        self.graph.set_xlim(0, max(self.Hinderniss.shape))
        self.graph.set_ylim(0, max(self.Hinderniss.shape))
        self.graph.set_zlim(0, max(self.Hinderniss.shape))
        self.graph.set_axis_off()
        self.graph.set_facecolor((0, 0, 0, 0.8))
        self.canvas.flush_events()


    def flowshow(self):
        self.flowgraph.clear()
        a, b, c = np.meshgrid(np.linspace(0.5, (self.Hinderniss.shape[1] - 0.5), self.Hinderniss.shape[1]),
                              np.linspace(0.5, (self.Hinderniss.shape[0] - 0.5), self.Hinderniss.shape[0]),
                              np.linspace(0.5, (self.Hinderniss.shape[2] - 0.5), self.Hinderniss.shape[2]) )
        self.flowgraph.voxels(self.Hinderniss, color = 'white', edgecolor = 'white')
        
        for d in [0, 1, 2]:
            l = list(range(self.Hinderniss.shape[d]))
            l = l[0 : int(self.Hinderniss.shape[d] / 2)] + l[int(self.Hinderniss.shape[d] / 2) + 1 :]
            pb = np.delete(b, l, d)
            pa = np.delete(a, l, d)
            pc = np.delete(c, l, d)
            rx = np.delete(self.vx, l, d) * 10
            ry = np.delete(self.vy, l, d) * 10
            rz = np.delete(self.vz, l, d) * 10
            self.flowgraph.quiver(pb, pa, pc, ry, rx, rz, cmap = 'prism', normalize = False, alpha = 0.8, linewidth = rx.reshape(-1) / 7)

        self.flowgraph.set_xlim(0, max(self.Hinderniss.shape))
        self.flowgraph.set_ylim(0, max(self.Hinderniss.shape))
        self.flowgraph.set_zlim(0, max(self.Hinderniss.shape))
        self.flowgraph.set_axis_off()
        self.flowgraph.set_facecolor((0, 0, 0, 1))
        self.canvas.flush_events()


    def _zugriff(self, data, dimension, dimensions_index):
        if dimension == 0:
            m = np.zeros((data.shape[2], data.shape[1]), list)
            for i in range(data.shape[2]):
                n = np.zeros(data.shape[1], list)
                for j in range(data.shape[1]):
                    n[j] = data[dimensions_index][j][i]
                m[i] = n
            return m
        elif dimension == 1:
            m = np.zeros((data.shape[2], data.shape[0]), list)
            for i in range(data.shape[2]):
                n = np.zeros(data.shape[0], list)
                for j in range(data.shape[0]):
                    n[j] = data[j][dimensions_index][i]
                m[i] = n
            return m
        else:
            m = np.zeros((data.shape[1], data.shape[0]), list)
            for i in range(data.shape[1]):
                n = np.zeros(data.shape[0], list)
                for j in range(data.shape[0]):
                    n[j] = data[j][i][dimensions_index]
                m[i] = n
            return m


    def koerperuebernahme(self):
        datei = askopenfilename(title = 'Körperobjekt auswählen', filetypes = [('Obj Datei', '*.obj')])
        name = datei.split('/')[-1].split('.')[0]
        if name not in self.controller.projektnamen:
            self.name = name
            self.Koerper = import_voxelkoerper(datei)
            self.shape = self.Koerper.shape
            self.matrixerweiterung(False)
            alter_name = self.controller.projektmanagement.tab(self.controller.projektmanagement.select(), 'text')
            self.controller.projektmanagement.tab(self.controller.projektmanagement.select(), text = self.name)
            self.controller.projekte[self.name] = self.controller.projekte.pop(alter_name)
            self.controller.projektnamen[self.controller.projektnamen.index(alter_name)] = self.name
            self.importbutton.configure(state = 'disable')
        else:
            print('Der gewählte Körper ist bereits geöffnet!')


    def matrixerweiterung(self, faktormodus):
        if type(self.Koerper) != type(None):
            alt = self.matrixraum
            try:
                neu = [float(self.xr.get()), [float(self.yv.get()), float(self.yh.get())], [float(self.zu.get()), float(self.zo.get())]]
            except:
                pass
            if alt != neu or self.faktormodus != faktormodus:
                self.Koerper = matrixraum_erweitern(self.Koerper, alt, neu, faktormodus, self.faktormodus, self.shape)
                self.matrixraum = neu
                self.faktormodus = faktormodus
                self.darstellen_matrix()


    def darstellen_matrix(self):
        self.voxelgraph.clear()
        self.voxelgraph.voxels(self.Koerper, color = [0, 1, 0, 0.7], edgecolor ='k')
        x = self.Koerper.shape[0]
        y = self.Koerper.shape[1]
        z = self.Koerper.shape[2]

        self.voxelgraph.plot([0, 0], [0, 0], [0, z], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([0, 0], [0, y], [0, 0], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([0, x], [0, 0], [0, 0], color = [1, 0, 0, 1], linewidth = 1)

        self.voxelgraph.plot([x, x], [0, 0], [z, 0], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([x, 0], [0, 0], [z, z], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([x, x], [0, y], [z, z], color = [1, 0, 0, 1], linewidth = 1)

        self.voxelgraph.plot([0, 0], [y, 0], [z, z], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([0, x], [y, y], [z, z], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([0, 0], [y, y], [z, 0], color = [1, 0, 0, 1], linewidth = 1)

        self.voxelgraph.plot([x, x], [y, 0], [0, 0], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([x, 0], [y, y], [0, 0], color = [1, 0, 0, 1], linewidth = 1)
        self.voxelgraph.plot([x, x], [y, y], [0, z], color = [1, 0, 0, 1], linewidth = 1)

        d = [x, y, z]
        self.voxelgraph.set_xlim(0, max(d))
        self.voxelgraph.set_ylim(0, max(d))
        self.voxelgraph.set_zlim(0, max(d))
        self.voxelgraph.set_axis_off()
        self.voxeldarstellung.flush_events()



Programm()
