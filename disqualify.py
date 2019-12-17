from DBConnection import DBConnection

def disqualifyPlayer(player_id, round_id):
    print('Disqualifying player {:s} from round {:s}'.format(getNameById('players', player_id), getNameById('rounds', round_id)))
    with DBConnection() as db:
        db.execute_query("SELECT points FROM player_times WHERE player_id = ? AND round_id = ?", (player_id, round_id))
        result = db.cur.fetchone()
        if result == None:
            print('player_id = {:d}, round_id = {:d} combination not found'.format(player_id, round_id))
            return
        player_points = result[0]


        db.execute_query("UPDATE player_times SET points = 0, dsq = 1 WHERE player_id = ? AND round_id = ?", (player_id, round_id))

        db.execute_query("UPDATE player_times SET points = points + 1 WHERE points < ? AND dsq = 0 AND round_id = ?", (player_points, round_id))


def disqualifyTeam(team_id, round_id):
    print('Disqualifying team {:s} from round {:s}'.format(getNameById('teams', team_id), getNameById('rounds', round_id)))
    with DBConnection() as db:
        db.execute_query("SELECT points FROM team_times WHERE team_id = ? AND round_id = ?", (team_id, round_id))
        result = db.cur.fetchone()
        if result == None:
            print('team_id = {:d}, round_id = {:d} combination not found'.format(team_id, round_id))
            return
        team_points = result[0]


        db.execute_query("UPDATE team_times SET points = 0, dsq = 1 WHERE team_id = ? AND round_id = ?", (team_id, round_id))

        db.execute_query("UPDATE team_times SET points = points + 1 WHERE points < ? AND dsq = 0 AND round_id = ?", (team_points, round_id))

        db.execute_query("SELECT players.id FROM players WHERE players.team_id = ?", (team_id,))

        result = db.cur.fetchall()

    for row in result:
        player_id = row[0]
        disqualifyPlayer(player_id, round_id)



def getIdByName(table, player_name):
    with DBConnection() as db:
        db.execute_query("SELECT id, name FROM {:s} WHERE name LIKE ?".format(table), (player_name, ))
        result = db.cur.fetchall()
    if len(result) == 0:
        print('{:s} name = {:s} not found'.format(table[:-1], player_name))
        return None

    if len(result) > 1:
        print('Multiple {:s} found. Result: {}'.format(table, result))
        return None

    return result[0][0]


def getLastRoundId():
    with DBConnection() as db:
        db.execute_query("SELECT id FROM rounds ORDER BY id DESC LIMIT 1")

        result = db.cur.fetchone()

    return result[0]


def getNameById(table, round_id):
    with DBConnection() as db:
        db.execute_query("SELECT name FROM {:s} WHERE id = ?".format(table), (round_id, ))
        result = db.cur.fetchone()

    return result[0]


def subtractTeamPoint(player_id, round_id):
    with DBConnection() as db:
        db.execute_query("UPDATE team_times SET points = points - 1 WHERE team_id = (SELECT team_id FROM players WHERE players.id = ?) AND round_id = ?", (player_id, round_id))


def disqualifyPlayerMenu():
    player_id = None

    while player_id == None:
        player_input = input('Who do you want to disqualify?\n')
        try:
            player_id = int(player_input)
        except ValueError:
            player_id = getIdByName('players', player_input)
    
    round_id = None
    while round_id == None:
        round_input = input('From which round? (type last for the last round)\n')
        if round_input.lower() == 'last':
            round_id = getLastRoundId()
            continue
        try:
            round_id = int(round_input)
        except ValueError:
            round_id = getIdByName('rounds', round_input)

    player_name = getNameById('players', player_id)
    round_name = getNameById('rounds', round_id)

    while True:
        response = input('Are you sure you want to disqualify {:s}, from round {:s}? yes/no\n'.format(player_name, round_name)).lower()
        if response == 'yes':
            print('Disqualifying')
            disqualifyPlayer(player_id, round_id)
            subtractTeamPoint(player_id, round_id)
            break
        elif response == 'no':
            print('Ok then ill exit')
            break


def disqualifyTeamMenu():
    team_id = None

    while team_id == None:
        team_input = input('Which team do you want to disqualify?\n')
        try:
            team_id = int(team_input)
        except ValueError:
            team_id = getIdByName('teams', team_input)
    
    round_id = None
    while round_id == None:
        round_input = input('From which round? (type last for the last round)\n')
        if round_input.lower() == 'last':
            round_id = getLastRoundId()
            continue
        try:
            round_id = int(round_input)
        except ValueError:
            round_id = getIdByName('rounds', round_input)

    team_name = getNameById('teams', team_id)
    round_name = getNameById('rounds', round_id)

    while True:
        response = input('Are you sure you want to disqualify team {:s}, from round {:s}? yes/no\n'.format(team_name, round_name)).lower()
        if response == 'yes':
            disqualifyTeam(team_id, round_id)
            break
        elif response == 'no':
            print('Ok then ill exit')
            break


def disqualifyMenu():
    response = input('Do you want to disqualify a player or a team? team/player/no\n').lower()
    if response == 'no':
        return False

    DBConnection.backup()

    if response == 'team':
        disqualifyTeamMenu()
    elif response == 'player':
        disqualifyPlayerMenu()

    return True

if __name__ == "__main__":
    disqualifyMenu()