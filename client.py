from serial import Serial
import threading
import time
import numpy as np
import json
import config

import Scoreboard

from DBConnection import DBConnection
import tourStoredProcedures


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
    def __init__(self, name, serial_conn):
        self.serial_conn = serial_conn
        self.name = name

        with DBConnection() as db:
            # Insert round into database
            result = db.execute_query("INSERT INTO rounds(name) \
                        VALUES (?)", (self.name, ))
            self.round_id = result.lastrowid

            # Get team_id: [pin_ids] dict
            result = db.execute_query("SELECT players.team_id, players.pin_id FROM players")
            # result = db.execute_query("SELECT players.team_id, json_group_array(players.pin_id) FROM players GROUP BY players.team_id")

            teams = dict()
            for team_id, pin_id in result.fetchall():
                if team_id not in teams:
                    teams[team_id] = []
                teams[team_id].append(pin_id)

                # self.teams[team_id] = json.loads(pin_ids)
        self.teams = teams

        
        self.n_players = len(self.pin_ids)
        self.readyState = False
        self.gameState = False



    @property
    def pin_ids(self):
        pin_ids = []
        for ids in self.teams.values():
            pin_ids += ids
        return pin_ids

    @property
    def team_ids(self):
        return self.teams.keys()


    def removePin(self, pin_id):
        for team_id in self.teams:
            if pin_id in self.teams[team_id]:
                self.teams[team_id].remove(pin_id)
                return team_id
        
        return None


    def removeTeam(self, team_id):
        del self.teams[team_id]


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
    def __init__(self, name, serial_conn):
        super().__init__(name, serial_conn)


    def recvReady(self):
        super().recvReady()


    def finishPin(self, pin_id, time_value):
        if pin_id in self.pin_ids:
            pin_points = len(self.pin_ids)
            tourStoredProcedures.addPinTime(pin_id, self.round_id, time_value, pin_points)

            team_id = self.removePin(pin_id)
            if not self.teams[team_id]:
                team_points = len(self.teams)
                tourStoredProcedures.addTeamTime(team_id, self.round_id, time_value, team_points)
                self.removeTeam(team_id)

            if not self.pin_ids:
                self.sendStop()



class SetupRound(Round):
    def __init__(self, name, serial_conn):
        super().__init__(name, serial_conn)
        self.points = 0

        self.player_name = None
        self.player_id = None


    def nextPlayer(self):
        with DBConnection() as db:
            db.execute_query("SELECT players.id, players.name from players WHERE pin_id IS NULL ORDER BY team_id LIMIT 1")
            result = db.cur.fetchone()
            if result == None:
                self.sendStop()
                return

            self.player_id, self.player_name = result

        print('Player: {}'.format(self.player_name))


    def recvReady(self):
        self.nextPlayer()
        super().recvReady()


    def finishPin(self, pin_id, time_value):
        with DBConnection() as db:
            db.execute_query("UPDATE players SET pin_id=? WHERE players.id=?", (pin_id, self.player_id))

        tourStoredProcedures.addPinTime(pin_id, self.round_id, 0, self.points)

        self.nextPlayer()

        super().finishPin(pin_id, time_value)



class TeamRound(Round):
    def __init__(self, name, serial_conn):
        super().__init__(name, serial_conn)


    def recvReady(self):
        self.points = self.n_players//4
        super().recvReady()


    def finishPin(self, pin_id, time_value):
        if pin_id in self.pin_ids:
            team_id = self.removePin(pin_id)
            
            team_points = len(self.teams)
            tourStoredProcedures.addTeamTime(team_id, self.round_id, time_value, team_points)

            self.removeTeam(team_id)

        if not self.pin_ids:
            self.sendStop()



class Tour():
    def __init__(self, name: str, mode: str):
        # Establish a serial connection
        self.serial_conn = SerialHandler(config.SERIAL_PORT, config.SERIAL_BAUD)
        self.serial_monitor = StreamMonitor(self.serial_conn.read)
        self.serial_monitor.start(self.processSerial, name='SERIAL')

        # Start a prompt monitor
        self.prompt_monitor = StreamMonitor(input)
        self.prompt_monitor.start(self.processPrompt, name='PROMPT')


        mode = mode.lower()

        if mode == 'team':
            self.round = TeamRound(name, self.serial_conn)
        elif mode == 'setup':
            self.round = SetupRound('SETUP', self.serial_conn)
        else:

            self.round = IndividualRound(name, self.serial_conn)

        timeBoard = Scoreboard.TeamTimes(self.round.round_id, self.round.name) if mode == 'team' else Scoreboard.PlayerTimes(self.round.round_id, self.round.name)
        sections = [
                [timeBoard],
                [Scoreboard.TeamCards()],
                [Scoreboard.Leaderboard('Leaderboard')],
                [Scoreboard.Leaderboard('Ladies', 'female'), Scoreboard.Leaderboard('Sjaars', 'sjaars')]
            ]

        self.sb = Scoreboard.ScoreBoard(sections)
        self.sb.updateAll(force = True)


    def processSerial(self, line: str, name = 'SERIAL'):
        data = line.split(' ')
        code = data[0]
        value = data[1] if len(data) > 1 else None

        print(name, code, value)

        if code == 'FIN':
            pin_id, time_value = value.split(':')
            self.round.finishPin(int(pin_id), int(time_value))
            self.sb.updateAll(force=True)

        elif code == 'GMT':
            pass

        elif code == 'STP':
            self.round.recvStop()
            self.stopGame()

        elif code == 'STR':
            self.round.recvStart()

        elif code == 'RDY':
            self.round.recvReady()



    def processPrompt(self, line: str, name = 'PROMPT'):
        if line == 'ready':
            self.round.sendReady()

        elif line == 'stop':
            self.round.sendStop()

        elif line == 'start':
            self.round.sendStart()



    def stopGame(self):
        self.sb.stop()
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
