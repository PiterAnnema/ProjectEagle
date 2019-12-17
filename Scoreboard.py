import os
import threading
import time

from DBConnection import DBConnection

def pretty_time_delta(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return '{:d}d {:2d}h'.format(days, hours)

    if hours > 0:
        return '{:2d}:{:0>2d}'.format(hours, minutes)

    if minutes > 0:
        return '{:2d}:{:0>2.3f}'.format(minutes, seconds + milliseconds/1000)

    return '{:2.3f}'.format(seconds + milliseconds/1000)


class ScoreSection(object):
    def __init__(self):
        self._header = ''
        self._body = ''
        self._body_prev = ''
        self._footer = ''


    def update(self):
        pass
        # print(__name__, self.__class__.__name__)


    @property
    def updated(self):
        return self._body != self._body_prev


    @property
    def html(self):
        return self._header + self._body + self._footer

    def readHtml(self):
        self._body_prev = str(self._body)
        return self.html



class PlayerTimes(ScoreSection):
    def __init__(self, round_id, round_name):
        super().__init__()

        self.round_id = round_id
        self.round_name = round_name


        self._header =  '<div><h2>Round {:d}: {:s}</h2><div class="leaderboard-card"><table>\n'.format(self.round_id -1, self.round_name)
        self._header += '<tr><th>Player</th><th class="time">Time</th><th class="score">Points</th></tr>\n'
    
        self._footer = '</table></div></div>'

        self.update()


    @staticmethod
    def row(team_id, player_name, time_value = None, points = None):
        t_disp = pretty_time_delta(milliseconds=time_value) if time_value else ''
        
        p_disp = '{:2d}'.format(points) if points != None else '' 

        row = '<tr><td> <span class="dot team{:d}"></span> {:s}</td><td class="time">{:s}</td><td class="score">{:s}</td></tr>\n'
        return row.format(team_id, player_name, t_disp, p_disp)


    def update(self):
        
        super().update()

        body = ''
        with DBConnection() as db:
            result = db.execute_query("\
                SELECT teams.id, players.name, player_times.time_value, player_times.points \
                FROM player_times \
                LEFT JOIN players ON player_times.player_id = players.id \
                LEFT JOIN teams on players.team_id = teams.id \
                WHERE round_id = ? ORDER BY player_times.points DESC", (self.round_id, ))
            result = result.fetchall()



        for team_id, player_name, time_value, points in result:
            body += self.row(team_id, player_name, time_value, points)


        with DBConnection() as db:
            result = db.execute_query("\
                SELECT teams.id, players.name \
                FROM players \
                LEFT JOIN teams on players.team_id = teams.id \
                WHERE players.id NOT IN (SELECT player_times.player_id from player_times where player_times.round_id = ?)\
                ORDER BY teams.name", (self.round_id, ))

            result = result.fetchall()

        for team_id, player_name in result:
            body += self.row(team_id, player_name)

        self._body = body


class TeamTimes(ScoreSection):
    def __init__(self, round_id, round_name):
        super().__init__()
        self.round_id = round_id
        self.round_name = round_name


        self._header =  '<div><h2>Round {:d}: {:s}</h2><div class="leaderboard-card"><table>\n'.format(self.round_id -1, self.round_name)
        self._header += '<tr><th>Team</th><th class="time">Time</th><th class="score">Points</th></tr>\n'
    

        self._footer = '</table></div></div>'

        self.update()


    @staticmethod
    def _row(team_id, team_name, time_value = None, points = None):
        t_disp = pretty_time_delta(milliseconds=time_value) if time_value else ''
        
        p_disp = '{:2d}'.format(points) if points != None else '' 

        row = '<tr><td> <span class="dot team{:d}"></span> {:s}</td><td class="time">{:s}</td><td class="score">{:s}</td></tr>\n'
        return row.format(team_id, team_name, t_disp, p_disp)


    def update(self):
        super().update()
        body = ''
        with DBConnection() as db:
            result = db.execute_query("\
                SELECT teams.id, teams.name, team_times.time_value, team_times.points \
                FROM team_times \
                LEFT JOIN teams on team_times.team_id = teams.id \
                WHERE round_id = ? ORDER BY team_times.points DESC", (self.round_id, ))
            result = result.fetchall()



        for team_id, team_name, time_value, points in result:
            body += self._row(team_id, team_name, time_value, points)


        with DBConnection() as db:
            result = db.execute_query("\
                SELECT teams.id, teams.name \
                FROM teams \
                WHERE teams.id NOT IN (SELECT team_times.team_id FROM team_times WHERE team_times.round_id = ?)\
                ORDER BY teams.name", (self.round_id, ))

            result = result.fetchall()

        for team_id, team_name in result:
            body += self._row(team_id, team_name)

        self._body = body


class TeamCard(ScoreSection):
    def __init__(self, team_id):
        super().__init__()

        self.team_id = team_id
        self.team_points = None

        with DBConnection() as db:
            result = db.execute_query("SELECT teams.name FROM teams WHERE teams.id = ?", (self.team_id, ))
            self.team_name = result.fetchone()[0]

        self._header += '<div class="grid-item team-card team{:d}"><table>'.format(team_id)

        self._footer += '</table></div>'

        self.update()


    @staticmethod
    def _row(player_name, total_points):
        row = '<tr><td>{:s}</td><td class="score">{:3d}</td></tr>\n'
        return row.format(player_name, total_points)


    def update(self):
        super().update()
        body = ''

        with DBConnection() as db:
            result = db.execute_query("SELECT SUM(team_times.points) FROM team_times WHERE team_times.team_id = ?", (self.team_id, ))
            self.team_points = result.fetchone()[0]
            if self.team_points == None:
                self.team_points = 0

            body += '<tr><th>{:s}</th><th class="score">{:3d}</th></tr>\n'.format(self.team_name, self.team_points)


            result = db.execute_query("SELECT players.name, \
                    SUM (points)  AS total_points \
                    FROM player_times LEFT JOIN players ON players.id = player_times.player_id \
                    WHERE players.team_id = ?\
                    GROUP BY player_times.player_id ORDER BY total_points DESC", (self.team_id, ))

            result = result.fetchall()

        for player_name, total_points in result:
            body += self._row(player_name, total_points)

        
        self._body = body



class TeamCards(ScoreSection):
    def __init__(self):
        super().__init__()

        self._header += '<div><h2>Teams</h2><div class="grid-container team-container">\n'
        self._footer += '</div></div>'


        with DBConnection() as db:
            result = db.execute_query("SELECT teams.id FROM teams")
            result = result.fetchall()

            team_ids = [i[0] for i in result]

        self.team_cards = [TeamCard(team_id) for team_id in team_ids]


    def update(self):
        super().update()

        body = ''
        for card in self.team_cards:
            card.update()

        self.team_cards.sort(key=lambda c: c.team_points, reverse=True)

        for card in self.team_cards:
            body += card.html

        self._body = body


class Leaderboard(ScoreSection):
    def __init__(self, name, attribute=None):
        super().__init__()
        # # if attribute:

        #     # self._where = "'{}' IN (SELECT value FROM json_each(players.attributes))".format(attribute)
        # else:
        #     self._where = ''
        self.attribute = attribute

        self._name = name

        self._header += '<div><h2>{:s}</h2><div class="leaderboard-card">\n'.format(name)
        self._header += '<table><tr><th>Player</th><th class="score">Points</th></tr>\n'

        self._footer += '</table></div></div>'



    @staticmethod
    def _row(team_id, player_name, total_points):
        row = '<tr><td> <span class="dot team{:d}"></span> {:s}</td><td class="score">{:3d}</td></tr>\n'

        return row.format(team_id, player_name, total_points)



    def update(self):
        super().update()

        body = ''

        with DBConnection() as db:
            result = db.execute_query("SELECT players.name, players.team_id, players.attributes, \
                    SUM (points)  AS total_points \
                    FROM player_times LEFT JOIN players ON players.id = player_times.player_id \
                    GROUP BY player_times.player_id ORDER BY total_points DESC")

            result = result.fetchall()

        for player_name, team_id, attributes, total_points in result:
            if not self.attribute or self.attribute in attributes:
                body += self._row(team_id, player_name, total_points)

        self._body = body



class ScoreBoard():
    def __init__(self, sections, html_dir='scoreboard'):
        self._html_dir = html_dir
        self.sections = sections

        self._running = False
        self._t = None
        self.start()

        self._t_update = 0

    def updateAll(self, force=True):
        t_now = time.time()
        
        if not force and t_now - self._t_update < 0.5:
            return
        
        self._t_update = t_now
        for column in self.sections:
            for section in column:
                section.update()


    def start(self):
        self._running = True
        self._t = threading.Thread(target=self.sectionMonitor)
        self._t.start()


    def stop(self):
        self._running = False
        time.sleep(0.1)
        self.checkUpdate()
        self._t.join()


    def sectionMonitor(self):
        while self._running:
            self.checkUpdate()
            time.sleep(0.2)


    def checkUpdate(self):

        for c, column in enumerate(self.sections):
            for section in column:
                if section.updated:
                    self.writeColumn(c)
                    break


    def writeColumn(self, c):
        html = ''
        for section in self.sections[c]:
            html += section.readHtml()


        with open(os.path.join(self._html_dir, 'column{:d}.html'.format(c)), 'w', encoding='utf-8') as f:
            f.write(html)
