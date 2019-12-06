#include "Arduino.h"
#include "HardwareSerial.h"

const byte pin_vd    = 8; // voordrink pin
const byte n_players = 28;
const byte players[n_players] = {22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49};

const int min_down = 10;

unsigned long player_down[n_players];
unsigned long player_times[n_players];
unsigned long t_start;
bool game_state;
bool ready_state;
unsigned long vd_down;
bool vd_up = true;

long int cycle_count;

long randnumber;


#define ready_code      "RDY"
#define start_code      "STR"
#define stop_code       "STP"
#define times_code      "TMS"
#define finish_code     "FIN"
#define gametime_code   "GMT"
#define cyclecount_code "CYC"


void setup() {
  Serial.begin(115200);

  setAllPlayers(false);

  pinMode(pin_vd, INPUT_PULLUP);
  game_state = false;
  vd_down = 0;

  pinMode(LED_BUILTIN, OUTPUT);
  randomSeed(analogRead(0));
}

void loop() {
  readSerial();

  if (!ready_state)
    return;

  if (!game_state)
    readVd();
  else
    gameCycle();
}


void gameCycle()
{
  cycle_count ++;

  for (int i = 0; i != n_players; ++i)
  {
    long int t = millis();

    randnumber = random(2000);
    if (randnumber == 1) {
      player_times[i] = t - t_start;

      Serial.print(finish_code);
      Serial.print(' ');
      Serial.print(players[i]);
      Serial.print(":");
      Serial.println(player_times[i]);
    }
  }
}


void readVd()
{
  if (!digitalRead(pin_vd))
  {
    bool vd = false;
    long int t = millis();
    if (vd_down == 0)
      vd_down = t;
    else {
      if (vd_up == true && t - vd_down > min_down) {
        vd_up = false;
        if (game_state == false)
          startGame();
      }
    }
  }
  else {
    vd_down = 0;
    vd_up = true;
  }
}

void readSerial()
{
  if (Serial.available() > 0) {
    // read the incoming byte:
    byte incomingByte = Serial.read();

    switch (incomingByte) {
      case 'r' :
        if (!ready_state)
          getReady();
        break;
      case 's' :
        if (game_state)
          stopGame();
        else if (ready_state)
          startGame();
        break;
    }
  }
}

void getReady()
{
  Serial.println(ready_code);
  ready_state = true;
}


void startGame()
{
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println(start_code);

  game_state = true;
  setAllPlayers(true);

  t_start = millis();
  cycle_count = 0;
}

void stopGame()
{
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println(stop_code);

  game_state = false;
  ready_state = false;

  long int game_time = millis() - t_start;
  Serial.print(gametime_code);   Serial.print(' '); Serial.println(game_time);
  Serial.print(cyclecount_code); Serial.print(' '); Serial.println(cycle_count);
  delay(10);
}


void setAllPlayers(bool state)
{
  for (int i = 0; i != n_players; ++i)
  {
    player_down[i] = 0;
    player_times[i] *= !state;
  }
}
