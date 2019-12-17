# ProjectEagle
It's a small step for Francken

## Usage
### Initialization
To initialize the database run
```
python populateDatabase.py
```
This will import team/player names from teams.json

This json file must have the following structure:
```
{
    "team1": [
        {"name": "player1", "attributes": ["att1", "att2"] },
        {"name": "player2", ...},
        .
        .
        .
    ],
    "team2": [
    .
    .
    .
}
```
Attributes is an optional array of keywords, these keywords can be filtered on in the leaderboard display.

### Playing a round
To start a new round execute:
```console
python client.py
```
You will be promted for a round name and a gamemode.
There are three gamemodes:
- __Setup__: In this round button id's are linked with player names. Run this as the first round.
- __Individual__: In this round each player presses their button when they finish.
- __Team__: In this round only the last player to finish presses their button.

If for round name the keyword _setup_ is entered, the gamemode is automatically set to __setup__.

Gamemode keywords are case-insensitive.
If any gamemode other than _setup_ or _team_ is entered the mode is set to individual.

After entering the round name and gamemode, the round is initialized. A serial connection to the microcontroller is established. At this point the microcontroller does not accept any buttonpresses.
By entering the keyword _ready_ into the prompt the microcontroller will listen for the vd-button _or_ for the _start_ command from the prompt.

When the vd-button is pressed (or the _start_ command is sent) the game starts. From this moment the system will listen for player button presses.

When all players have finished or the _stop_ command is sent the round stops.
After completing a round you will be asked if you want to disqualify a player or team.

## Rules
### Individual round
#### Player points
When a player finishes they will be granted the following number of points:
```
points = total number of players - nth player to finish
```
an example: There are 28 players in the game, Leon finishes as the third player:
```
points = 28 - 3 = 24
```

#### Team points
When the _last_ player of a team finishes, their team is considered to be finised.
The amount of points granted to a team is similar to that of individual players:
```
points = total number of teams - nth team to finish
```

### Team round
#### Player points
Individual players are _not_ granted any points in a team round.
#### Team points
The number of points given to a team in a team round is the same a in the individual round. The main difference is that in the team round a team finishes when _any_ button belonging to said team is pressed. This is usually the last player to finish.

### Disqualification
Disqualification is done on a per-round-basis. After each round you are asked if you want to disqualify a player or a team. Alternatively this menu can be started by running:
```console
python disqualify.py
```
#### Disqualifying a player
When a player is disqualified they lose all their points in a given round. All players that finished after this player will be moved up one spot, thus gaining a point.
The team associated to the player loses one point.
#### Disqualifying a team
When a team is disqualified it loses all its points in that round. Additionally, all players in the team are disqualified from the round as described above.
#### Undo disqualification
As of yet it is not possible to undo any kind of disqualification. This _can_ be done manually in the database.
## The scoreboard
The scoreboard shows an overview of all team/player times and points.
It can be viewed through the scores.html file.