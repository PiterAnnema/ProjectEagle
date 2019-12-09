from DBConnection import DBConnection


def makeTables():
    with DBConnection() as db:
        db.execute_query(
            "CREATE TABLE IF NOT EXISTS players \
            (   id          INTEGER PRIMARY KEY, \
                pin_id      INTEGER, \
                name        VARCHAR NOT NULL UNIQUE, \
                team_id     INTEGER NOT NULL, \
                attributes  JSON\
                )"
            )

        db.execute_query(
            "CREATE TABLE IF NOT EXISTS teams \
            (   id          INTEGER PRIMARY KEY, \
                name   VARCHAR NOT NULL UNIQUE \
            )"
        )

        db.execute_query(
            "CREATE TABLE IF NOT EXISTS rounds \
            (   id          INTEGER PRIMARY KEY, \
                name        VARCHAR NOT NULL \
            )"
        )

        db.execute_query(
            "CREATE TABLE IF NOT EXISTS player_times \
            (   id          INTEGER PRIMARY KEY, \
                player_id   INTEGER NOT NULL, \
                round_id    INTEGER NOT NULL, \
                time_value  INTEGER NOT NULL, \
                points      INTEGER NOT NULL, \
                UNIQUE(player_id, round_id) \
            )"
        )

        db.execute_query(
            "CREATE TABLE IF NOT EXISTS team_times \
            (   id          INTEGER PRIMARY KEY, \
                team_id     INTEFER NOT NULL, \
                round_id    INTEGER NOT NULL, \
                time_value  INTEGER NOT NULL, \
                points      INTEGER NOT NULL, \
                UNIQUE(team_id, round_id) \
            )"
        )


# def getTeamIdByPinId(pin_id):
#     with DBConnection() as db:
#         db.execute_query("SELECT players.team_id FROM players WHERE players.pin_id = ?", (pin_id, ))
#         result = db.cur.fetchone()[0]
#     return result


# def getPinIdsByTeamId(team_id):
#     with DBConnection() as db:
#         db.execute_query("SELECT pin_id FROM players WHERE players.team_id = ?", (team_id, ))
#         result = db.cur.fetchone()

#     result = [x[0] for x in result]
#     return result


def addPinTime(pin_id, round_id, time_value, points):
    with DBConnection() as db:
        db.execute_query("\
            INSERT INTO \
                player_times(player_id, round_id, time_value, points) \
            VALUES \
                ((SELECT players.id from players WHERE players.pin_id = ?), ?, ?, ?)",\
            (pin_id, round_id, time_value, points))

        result = db.cur.lastrowid

    return result


def addTeamTime(team_id, round_id, time_value, points):
    with DBConnection() as db:
        db.execute_query("INSERT INTO team_times(team_id, round_id, time_value, points) \
            VALUES (?, ?, ?, ?)", (team_id, round_id, time_value, points))
        result = db.cur.lastrowid

    return result