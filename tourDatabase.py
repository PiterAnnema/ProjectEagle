import sqlite3
import shutil
import os
import datetime

class TourDatabase():
    def __init__(self, db_filename='tour.db', verbose=False):
        self.db_filename = db_filename
        self.verbose = verbose
        db = sqlite3.connect(self.db_filename)

        c = db.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS players \
            (   player_id   INTEGER PRIMARY KEY, \
                pin_id      INTEGER, \
                player_name VARCHAR NOT NULL UNIQUE, \
                team_id     INTEGER NOT NULL \
                )"
            )

        c.execute(
            "CREATE TABLE IF NOT EXISTS teams \
            (   team_id     INTEGER PRIMARY KEY, \
                team_name   VARCHAR NOT NULL UNIQUE \
            )"
        )

        c.execute(
            "CREATE TABLE IF NOT EXISTS rounds \
            (   round_id     INTEGER PRIMARY KEY, \
                round_name   VARCHAR NOT NULL \
            )"
        )

        c.execute(
            "CREATE TABLE IF NOT EXISTS times \
            (   time_id     INTEGER PRIMARY KEY, \
                player_id   INTEGER NOT NULL, \
                round_id    INTEGER NOT NULL, \
                time_value  INTEGER NOT NULL, \
                points      INTEGER NOT NULL, \
                UNIQUE(player_id, round_id) \
            )"
        )

        db.commit()
        c.close()

    def populate(self, autopin=False):
        import json
        with open('teams.json', 'r') as f:
            teams = json.load(f)

        i = 22
        for team_name in teams:
            team_id = self.addTeam(team_name)
            for player in teams[team_name]:
                self.addPlayer(player, team_id, i if autopin else None)
                i += 1


    def getNumberOfPlayers(self):
        db = sqlite3.connect(self.db_filename)

        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM players")
        n_players = c.fetchall()[0][0]
        c.close()
        return n_players

    
    def getPlayersWithoutPin(self):
        db = sqlite3.connect(self.db_filename)

        c = db.cursor()
        c.execute("SELECT player_id, player_name from players WHERE pin_id IS NULL ORDER BY team_id")
        result = c.fetchall()
        c.close()
        return result


    def getTeamIdByName(self, team_name):
        db = sqlite3.connect(self.db_filename)

        c = db.cursor()
        c.execute("SELECT team_id from teams WHERE team_name like ?", (team_name, ))
        team_id = c.fetchall()
        if not team_id:
            raise ValueError("No teams found with that name")
        elif len(team_id) > 1:
            raise ValueError("Multiple teams found, be more specific")

        c.close()

        return team_id[0][0]

    
    def addPlayerToTeam(self, player_name, team_name, pin_id = None):
        team_id = self.getTeamIdByName(team_name)
        return self.addPlayer(player_name, team_id, pin_id)


    def addPlayer(self, player_name, team_id, pin_id = None):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("INSERT INTO players(pin_id, player_name, team_id) \
                    VALUES (?, ?, ?)", (pin_id, player_name, team_id))

        db.commit()
        c.close()
        
        return c.lastrowid


    def bindPinToPlayer(self, pin_id, player_id):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("UPDATE players set pin_id=? where player_id=?", (pin_id, player_id))

        db.commit()
        c.close()
        
        return c.lastrowid


    def addTeam(self, team_name):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("INSERT INTO teams(team_name) \
                    VALUES (?)", (team_name, ))

        db.commit()
        c.close()

        return c.lastrowid


    def addRound(self, round_name):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("INSERT INTO rounds(round_name) \
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
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("SELECT player_id from players where pin_id=?", (pin_id, ))
        player_id = c.fetchone()[0]
        c.execute("INSERT INTO times(player_id, round_id, time_value, points) \
                    VALUES (?, ?, ?, ?)", (player_id, round_id, time_value, points))

        db.commit()
        c.close()

        return c.lastrowid

    
    def backup(self, backup_dir = 'db_backups'):
        dt = datetime.datetime.now()
        dt_str = dt.strftime("%d_%m_%Y_%H_%M_%S")
        dst = os.path.join(backup_dir, dt_str + self.db_filename + '.bak')
        shutil.copyfile(self.db_filename, dst)



def main():
    tdb = TourDatabase(verbose=True)
    tdb.populate()


if __name__ == "__main__":
    main()