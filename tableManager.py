import sqlite3
import os

def pretty_time_delta(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    t_str = ''
    if days > 0:
        t_str += '%dd ' % days
    if hours > 0:
        t_str += '%2d:' % (hours, )
    if minutes > 0:
        t_str += '%2d:' % (minutes, )

    if milliseconds < 100:
        milliseconds *= 10
    return t_str + '%2d.%2d' % (seconds, milliseconds)


class tableManager():
    def __init__(self, db_filename='tour.db', html_dir='scoreboard'):
        self.db_filename = db_filename
        self.html_dir = html_dir

    def roundTimes(self):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("SELECT round_id, round_name FROM rounds ORDER BY round_id DESC LIMIT 1")
        round_id, round_name = c.fetchall()[0]

        c.execute("SELECT teams.team_id, teams.team_name, players.player_name, times.time_value, times.points \
            from times \
                LEFT JOIN players ON times.player_id = players.player_id \
                LEFT JOIN teams on players.team_id = teams.team_id \
            WHERE round_id = ? ORDER BY times.time_value", (round_id, ))
        
        result = c.fetchall()

        html = "<div><h2>Round %d: %s</h2><div class=\"leaderboard-card\"><table>\n" % (round_id -1, round_name)
        html += "<tr><th>Player</th><th class=\"time\">Time</th><th class=\"score\">Points</th></tr>\n"
        # html += "<tr><th>Team</th><th>Player</th><th class=\"time\">Time</th><th class=\"score\">Points</th></tr>\n"


        for team_id, team_name, player_name, time_value, points in result:
            td = pretty_time_delta(milliseconds=time_value)
            html += "<tr><td> <span class=\"dot team%d\"></span> %s</td><td class=\"time\">%s</td><td class=\"score\">%2d</td></tr>\n" % (team_id, player_name, td, points)
            # html += "<tr><td class=\"team%d\">%s</td><td>%s</td><td class=\"time\">%s</td><td class=\"score\">%2d</td></tr>\n" % (team_id, team_name, player_name, td, points)


        c.execute("SELECT teams.team_id, teams.team_name, players.player_name from players \
            LEFT JOIN teams on players.team_id = teams.team_id \
                WHERE players.player_id NOT IN (SELECT times.player_id from times where times.round_id = ?)\
                ORDER BY teams.team_name", (round_id, ))

        result = c.fetchall()

        for team_id, team_name, player_name in result:
            html += "<tr><td> <span class=\"dot team%d\"></span> %s</td><td class=\"time\"></td><td class=\"score\"></td></tr>\n" % (team_id, player_name)
        c.close()


        html += "</table></div></div>"

        with open(os.path.join(self.html_dir, 'roundTimes.html'), 'w') as f:
            f.write(html)


    def teamPoints(self, team_id):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("SELECT players.player_name, \
                    SUM (points)  AS total_points \
                    FROM times LEFT JOIN players ON players.player_id = times.player_id \
                    WHERE players.team_id = ?\
                    GROUP BY times.player_id ORDER BY total_points DESC", (team_id, ))

        result = c.fetchall()
        c.close()

        html = ""
        for player_name, total_points in result:
            html += "<tr><td>%s</td><td class=\"score\">%3d</td></tr>\n" % (player_name, total_points)

        return html


    def allPoints(self):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute("SELECT players.team_id, teams.team_name, SUM(times.points) AS team_points \
                FROM times \
                LEFT JOIN players ON players.player_id = times.player_id \
                LEFT JOIN teams on players.team_id = teams.team_id \
                GROUP BY players.team_id \
                ORDER BY team_points DESC")
        result = c.fetchall()
        c.close()

        html = "<div><h2>Teams</h2><div class=\"grid-container team-container\">\n"
        for team_id, team_name, team_points in result:
            html += "<div class=\"grid-item team-card team%d\"><table>" % (team_id, )
            html += "<tr><th>%s</th><th class=\"score\">%3d</th></tr>\n" % (team_name, team_points)
            html += self.teamPoints(team_id)
            html += "</table></div>"
        html += "</div></div>"

        with open(os.path.join(self.html_dir, 'teamPoints.html'), 'w') as f:
            f.write(html)

    
    def playerPoints(self):
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()
        c.execute("SELECT players.player_name, players.team_id, \
                    SUM (points)  AS total_points \
                    FROM times LEFT JOIN players ON players.player_id = times.player_id \
                    GROUP BY times.player_id ORDER BY total_points DESC")

        result = c.fetchall()
        c.close()

        html = "<div><h2>Leaderboard</h2><div class=\"leaderboard-card\">\n<table><tr><th>Player</th><th class=\"score\">Points</th></tr>\n"
        for player_name, team_id, total_points in result:
            html += "<tr><td> <span class=\"dot team%d\"></span> %s</td><td class=\"score\">%3d</td></tr>\n" % (team_id, player_name, total_points)
        html += "</table></div></div>"
        with open(os.path.join(self.html_dir, 'playerPoints.html'), 'w') as f:
            f.write(html)



def main():
    tm = tableManager()
    tm.playerPoints()
    tm.roundTimes()
    tm.allPoints()


if __name__ == "__main__":
    main()