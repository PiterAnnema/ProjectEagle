from serial import Serial
import threading
import time
import numpy as np
import json

from tourDatabase import TourDatabase
from tableManager import tableManager

class StreamMonitor(object):
    def __init__(self, read_call):
        self._running = False
        self._monitor = None
        self._read = read_call

    def start(self, callback, *args, **kwargs):
        if isinstance(self._monitor, threading.Thread):
            return self._monitor

        self._monitor = threading.Thread(target=self._target, args=(callback,*args), kwargs=kwargs)

        self._running = True
        self._monitor.start()


    def stop(self):
        self._running = False
        # self._monitor.join()


    def _target(self, callback, *args, **kwargs):
        while self._running:
            data = self._read()
            callback(data, *args, **kwargs)


class SerialHandler(object):
    def __init__(self, port=None, baud=None):
        self.port = port
        self.baud = baud

        self.connection = None

        self.connectSerial()

    def connectSerial(self):
        while True:
            try:
                print('Connecting', self.port, self.baud)
                self.connection = Serial(self.port, self.baud)
            except Exception as e:
                print(e)
                for i in range(10, 0, -1):
                    print('Trying again in %2d' % i)
                    time.sleep(1)
            else:
                print('Serial connection established @%s - %d' % (self.port, self.baud))
                break


    def read(self):
        return self.connection.readline().decode().strip()


    def write(self, data: str):
        self.connection.write(data.encode())


class Round(object):
    def __init__(self, name, db_conn, serial_conn):
        self.db_conn = db_conn
        self.serial_conn = serial_conn
        self.name = name
        self.round_id = self.db_conn.addRound(name)
        self.n_players = self.db_conn.getNumberOfPlayers()
        self.readyState = False
        self.gameState = False


    def sendReady(self):
        self.serial_conn.write('r')


    def recvReady(self):
        self.readyState = True


    def sendStart(self):
        self.serial_conn.write('s')


    def recvStart(self):
        self.gameState = True


    def sendStop(self):
        self.serial_conn.write('s')


    def recvStop(self):
        self.gameState = False



    def finishPin(self, pin_id, time_value):
        pass



class IndividualRound(Round):
    def __init__(self, name, db_conn, serial_conn):
        super().__init__(name, db_conn, serial_conn)
        self.points = None


    def recvReady(self):
        self.points = self.n_players
        super().recvReady()


    def finishPin(self, pin_id, time_value):
        self.db_conn.addTime(pin_id, self.round_id, time_value, self.points)
        self.points -= 1



class SetupRound(Round):
    def __init__(self, name, db_conn, serial_conn):
        super().__init__(name, db_conn, serial_conn)
        self.points = 0

        self.player_name = None
        self.player_id = None

    def nextPlayer(self):
        player = self.db_conn.getPlayerWithoutPin()
        print('Nextplayer', player)
        if player != None:
            self.player_id, self.player_name = player
            print('Player: {}'.format(self.player_name))
        else:
            self.sendStop()


    def recvReady(self):
        print('Here')
        self.nextPlayer()
        super().recvReady()


    def finishPin(self, pin_id, time_value):
        self.db_conn.bindPinToPlayer(pin_id, self.player_id)
        self.db_conn.addTime(pin_id, self.round_id, time_value, self.points)

        self.nextPlayer()

        super().finishPin(pin_id, time_value)


class Tour():
    def __init__(self, name: str, mode: str):
        # Establish a serial connection
        self.serial_conn = SerialHandler('COM4', 115200)
        self.serial_monitor = StreamMonitor(self.serial_conn.read)
        self.serial_monitor.start(self.processSerial, name='SERIAL')

        # Start a prompt monitor
        self.prompt_monitor = StreamMonitor(input)
        self.prompt_monitor.start(self.processPrompt, name='PROMPT')

        # Estabslih database connection
        self.db_conn = TourDatabase(verbose=True)
        self.db_conn.backup()

        # If there are player without a pin bound to them, start setup
        if self.db_conn.getPlayerWithoutPin() != None:
            print('Players without pin detected')
            mode = 'setup'


        mode = mode.lower()
        if mode == 'individual':
            self.round = IndividualRound(name, self.db_conn, self.serial_conn)
        elif mode == 'setup':
            self.round = SetupRound('SETUP', self.db_conn, self.serial_conn)


        # Start tablemanager
        self.tm = tableManager()
        self.t_last_html_update = 0
        self.updateHtml()


    def processSerial(self, line: str, name = 'SERIAL'):
        data = line.split(' ')
        code = data[0]
        value = data[1] if len(data) > 1 else None

        print(name, code, value)

        if code == 'FIN':
            pin_id, time_value = value.split(':')
            self.round.finishPin(int(pin_id), int(time_value))
            self.updateHtml()

        elif code == 'GMT':
            pass

        elif code == 'STP':
            self.round.recvStop()
            self.stopGame()

        elif code == 'STR':
            self.round.recvStart()

        elif code == 'RDY':
            self.round.recvReady()


    def updateHtml(self, force: bool = False):
        t_now = time.time()
        if (force or t_now - self.t_last_html_update > 0.5):
            self.tm.roundTimes()
            self.tm.allPoints()
            self.tm.playerPoints()
            self.t_last_html_update = t_now



    def processPrompt(self, line: str, name = 'PROMPT'):
        if line == 'ready':
            self.round.sendReady()

        elif line == 'stop':
            self.round.sendStop()

        elif line == 'start':
            self.round.sendStart()



    def stopGame(self):
        self.updateHtml(force = True)
        print('Closing serial connection')
        self.serial_monitor.stop()
        print('Closing prompt connection')
        print('Press enter to exit prompt')
        self.prompt_monitor.stop()



def main():
    round_name = input('Enter round name: ')
    # round_name = 'setup'
    if round_name.lower() == 'setup':
        round_mode = 'setup'
    else:
        round_mode = input('Enter round mode: ')
    Tour(round_name, round_mode)


if __name__ == '__main__':
    main()
