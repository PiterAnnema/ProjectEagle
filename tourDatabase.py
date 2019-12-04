import sqlite3
import shutil
import os
import datetime

class DBConnector(object):
    def __init__(self):
        self._dbconn = None


    def create_connection(self):
        return sqlite3.connect('tour.db')


    def __enter__(self):
        self._dbconn = self.create_connection()
        return self._dbconn


    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dbconn.close()


class DBConnection(object):
    def __init__(self):
        self._conn = None


    @classmethod
    def get_connection(cls, new=False):
        """Creates return new Singleton database connection"""
        if new or not cls._conn:
            cls._conn = DBConnector().create_connection()
        return cls._conn


    @classmethod
    def execute_query(cls, query, params=None):
        """execute query on singleton db connection"""
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            result = cur.fetchall()
            cur.close()
        return result


class TourDatabase():
    def __init__(self):
        self._db = DBConnection()

        self._db.execute_query(
            "CREATE TABLE IF NOT EXISTS players \
            (   player_id   INTEGER PRIMARY KEY, \
                pin_id      INTEGER, \
                player_name VARCHAR NOT NULL UNIQUE, \
                team_id     INTEGER NOT NULL \
                )"
            )

        self._db.execute_query(
            "CREATE TABLE IF NOT EXISTS teams \
            (   team_id     INTEGER PRIMARY KEY, \
                team_name   VARCHAR NOT NULL UNIQUE \
            )"
        )

        self._db.execute_query(
            "CREATE TABLE IF NOT EXISTS rounds \
            (   round_id     INTEGER PRIMARY KEY, \
                round_name   VARCHAR NOT NULL \
            )"
        )

        self._db.execute_query(
            "CREATE TABLE IF NOT EXISTS times \
            (   time_id     INTEGER PRIMARY KEY, \
                player_id   INTEGER NOT NULL, \
                round_id    INTEGER NOT NULL, \
                time_value  INTEGER NOT NULL, \
                points      INTEGER NOT NULL, \
                UNIQUE(player_id, round_id) \
            )"
        )

    def populate(self):
        import json
        with open('teams.json', 'r') as f:
            teams = json.load(f)

        for team_name in teams:
            team_id = self.addTeam(team_name)
            for player in teams[team_name]:
                self.addPlayer(player, team_id)


    def getNumberOfPlayers(self):
        result = self._db.execute_query("SELECT COUNT(*) FROM players")
        n_players = result[0][0]
        return n_players

    
    def getPlayersWithoutPin(self):
        result = self._db.execute_query("SELECT player_id, player_name from players WHERE pin_id IS NULL ORDER BY team_id")
        return result


    def addPlayer(self, player_name, team_id, pin_id = None):
        result = self._db.execute_query("INSERT INTO players(pin_id, player_name, team_id) \
                    VALUES (?, ?, ?)", (pin_id, player_name, team_id))
        return result.lastrowid


    def bindPinToPlayer(self, pin_id, player_id):
        result = self._db.execute_query("UPDATE players set pin_id=? where player_id=?", (pin_id, player_id))
        return result


    def addTeam(self, team_name):
        result = self._db.execute_query("INSERT INTO teams(team_name) \
                    VALUES (?)", (team_name, ))
        return result.lastrowid


    def addRound(self, round_name):
        db = sqlite3.connect(self._db_filename)
        c = db.cursor()
        db.execute_query("INSERT INTO rounds(round_name) \
                    VALUES (?)", (round_name, ))

        db.commit()
        c.close()

        round_id = c.lastrowid
        if self.verbose:
            print('TOURDB', 'Added record for round: %s, id:%d' % (round_name, round_id))
        return round_id


    def addTime(self, pin_id, round_id, time_value, points):
        if self.verbose:
            print('TOURDB', 'Adding time record @pin: %d, round: %d, time %d' % (pin_id, round_id, time_value))
        db = sqlite3.connect(self._db_filename)
        c = db.cursor()
        db.execute_query("SELECT player_id from players where pin_id=?", (pin_id, ))
        player_id = c.fetchone()[0]
        db.execute_query("INSERT INTO times(player_id, round_id, time_value, points) \
                    VALUES (?, ?, ?, ?)", (player_id, round_id, time_value, points))

        db.commit()
        c.close()

        return c.lastrowid

    
    def backup(self, backup_dir = 'db_backups'):
        dt = datetime.datetime.now()
        dt_str = dt.strftime("%d_%m_%Y_%H_%M_%S")
        dst = os.path.join(backup_dir, dt_str + self._db_filename + '.bak')
        shutil.copyfile(self._db_filename, dst)



def main():
    tdb = TourDatabase()
    tdb.populate()


if __name__ == "__main__":
    main()