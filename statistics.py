from DBConnection import DBConnection


def getPlayerTotalTimes():
    with DBConnection() as db:
        db.execute_query("SELECT player_id, players.name, sum(time_value)       \
            AS total_time FROM player_times                                     \
            LEFT JOIN players ON player_id = players.id                         \
            GROUP BY player_id                                                  \
            ORDER BY total_time DESC")

        result = db.cur.fetchall()
    for row in result:
        print(row)

def getPlayerFastestTimes(not_round_name):
    with DBConnection() as db:
        db.execute_query("SELECT MIN(time_value) AS min_times, players.name, rounds.name                            \
            FROM player_times LEFT JOIN players on player_id = players.id LEFT JOIN rounds on rounds.id = round_id  \
            WHERE time_value > 0 AND NOT rounds.name LIKE ? GROUP BY player_id ORDER BY min_times", (not_round_name, ))
                                                  
        result = db.cur.fetchall()
    for row in result:
        print(row)

def getPlayerSlowestTimes(not_round_name):
    with DBConnection() as db:
        db.execute_query("SELECT MAX(time_value) AS max_times, players.name, rounds.name                            \
            FROM player_times LEFT JOIN players on player_id = players.id LEFT JOIN rounds on rounds.id = round_id  \
            WHERE time_value > 0 AND NOT rounds.name LIKE ? GROUP BY player_id ORDER BY max_times", (not_round_name, ))
                                                  
        result = db.cur.fetchall()
    for row in result:
        print(row)

def getRoundTimes(round_name):
    with DBConnection() as db:
        db.execute_query("SELECT players.name, time_value FROM player_times LEFT JOIN players on player_id = players.id \
            LEFT JOIN rounds on rounds.id = round_id WHERE rounds.name LIKE ? ORDER BY time_value DESC", (round_name, ))

        result = db.cur.fetchall()
    for row in result:
        print(row)

def getPlayerTimes(player_name):
    with DBConnection() as db:
        db.execute_query("SELECT rounds.name, players.name, time_value FROM player_times LEFT JOIN players on player_id = players.id \
            LEFT JOIN rounds on rounds.id = round_id WHERE players.name LIKE ? AND time_value > 0 ORDER BY round_id DESC", (player_name, ))

        result = db.cur.fetchall()
    for row in result:
        print(row)

getPlayerTotalTimes()
getPlayerFastestTimes()
getPlayerSlowestTimes()