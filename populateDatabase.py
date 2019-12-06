from DBConnection import DBConnection
import tourStoredProcedures

def main():
    import json
    with open('teams.json', 'r') as f:
        teams = json.load(f)

    tourStoredProcedures.makeTables()

    with DBConnection() as db:
        for team_name in teams:
            db.execute_query("INSERT INTO teams(name) \
                            VALUES (?)", (team_name, ))
            team_id = db.cur.lastrowid

            for player in teams[team_name]:
                db.execute_query("INSERT INTO players(name, team_id, female, sub_21) \
                                VALUES (?, ?, ?, ?)", (player['name'], team_id, player['female'], player['sub_21']))


if __name__ == "__main__":
    main()