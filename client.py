from serial import Serial
import threading
import time
import numpy as np
import json

from tourDatabase import TourDatabase
from tableManager import tableManager

class SerialHandler():
    def __init__(self, port=None, baud=None):
        self.port = port
        self.baud = baud

        self.connection = None

        self.connectSerial()

        self._running = False


    def connectSerial(self):
        while True:
            try:
                print('Connecting', self.port, self.baud)
                # raise ValueError
                self.connection = Serial(self.port, self.baud)
            except Exception as e:
                print(e)
                for i in range(10, 0, -1):
                    print('Trying again in %2d' % i)
                    time.sleep(1)
            else:
                print('Serial connection established @%s - %d' % (self.port, self.baud))
                break


    def startMonitor(self, callback, *args, **kwargs):
        self.monitor = threading.Thread(target=self.serialMonitor, args=(callback,*args), kwargs=kwargs)

        self._running = True
        self.monitor.start()

    def stopMonitor(self):
        self._running = False


    def serialMonitor(self, callback, *args, **kwargs):
        while self._running:
            line = self.connection.readline().decode().strip()
            callback(line, *args, **kwargs)
            time.sleep(0.1)

    def write(self, data: str):
        print('writing ', data)
        self.connection.write(data.encode())


class PromptHandler():
    def __init__(self):
        self._running = False


    def startMonitor(self, callback, *args, **kwargs):
        self.monitor = threading.Thread(target=self.promptMonitor, args=(callback,*args), kwargs=kwargs)

        self._running = True
        self.monitor.start()

    def stopMonitor(self):
        self._running = False


    def promptMonitor(self, callback, *args, **kwargs):
        while self._running:
            line = input()
            callback(line, *args, **kwargs)


class TourRound():
    def __init__(self, name, setup=False, verbose = False):
        self.name = name
        self.setup = setup
        self.verbose = verbose

        # Establish a serial connection
        self.serial_conn = SerialHandler('/dev/cu.usbmodem14601', 115200)
        self.serial_conn.startMonitor(self.processSerial)


        # Estabslih database connection
        self.tdb = TourDatabase(verbose=True)
        self.tdb.backup()
        self.round_id = self.tdb.addRound(self.name)

        self.n_players = self.tdb.getNumberOfPlayers()

        self.prompt_conn = PromptHandler()
        self.prompt_conn.startMonitor(self.processPrompt)
        self.tm = tableManager()

        self.tm.roundTimes()
        self.tm.allPoints()
        self.tm.playerPoints()

        self.t_last_html_update = time.time()

        if setup:
            print('SETUP')

            players = self.tdb.getPlayersWithoutPin()
            for player_id, player_name in players:
                self.bind_pin = -1
                print(player_name)
                while self.bind_pin == -1:
                    # print("Waiting")
                    # time.sleep(1)
                    pass
                self.tdb.bindPinToPlayer(self.bind_pin, player_id)
                self.tdb.addTime(self.bind_pin, self.round_id, 0, 0)
                self.tm.roundTimes()
                self.tm.allPoints()
                self.tm.playerPoints()
            self.stopGame()


    def processSerial(self, line: str, name = 'SERIAL'):
        print(line)
        data = line.split(' ')
        code = data[0]
        value = None
        if len(data) > 1:
            value = data[1]

        if code == 'FIN':
            pin_id, time_value = value.split(':')

            if self.setup:
                print('Got pin', pin_id)
                self.bind_pin = int(pin_id)

            else:
                self.finishPlayer(int(pin_id), int(time_value))
                t_now = time.time()
                if (t_now - self.t_last_html_update> 0.2):
                    self.tm.roundTimes()
                    self.tm.allPoints()
                    self.tm.playerPoints()
                    self.t_last_html_update = t_now

        elif code == 'GMT':
            pass
            # print('gametime', value)
        elif code == 'STP':
            self.stopGame()
        elif code == 'STR':
            self.points = self.n_players
            
        if self.verbose:
            print(name, code, value)


    def processPrompt(self, line: str, name = 'PROMPT'):
        if line == 'ready':
            self.readyGame()

        elif line == 'stop':
            self.serial_conn.write('s')
            self.stopGame()

        elif line == 'start':
            self.startGame()


    def readyGame(self):
        self.serial_conn.write('r')

    def startGame(self):
        self.serial_conn.write('s')


    def stopGame(self):
        print('Stopped')
        print('Closing serial connection')
        self.serial_conn.stopMonitor()
        print('Closing prompt connection')
        print('Press enter to exit prompt')
        self.prompt_conn.stopMonitor()
        self.tm.roundTimes()
        self.tm.allPoints()
        self.tm.playerPoints()


    def finishPlayer(self, pin_id, time_value):
        self.tdb.addTime(pin_id, self.round_id, time_value, self.points)
        self.points -= 1



def main():
    round_name = input('Enter round name: ')
    TourRound(round_name, setup=(round_name == 'setup'), verbose=False)


if __name__ == '__main__':
    main()
