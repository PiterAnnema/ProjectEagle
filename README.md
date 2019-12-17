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
