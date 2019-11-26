#include "Arduino.h"
#include "HardwareSerial.h"

const int pin_vd    = 8; // voordrink pin
const int n_players = 4;
const int players[n_players] = {46, 47, 48, 49};
const long int min_down = 10;

bool player_gs[n_players];
long int player_down[n_players];
long int t_start;
bool game_state;
long int vd_down;
bool vd_up = true;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  Serial.println("0, 1, 2, 3");
  for (int i = 0; i != n_players; ++i)
  {
    pinMode(players[i], INPUT_PULLUP);
  }

  set_all_players(false);

  pinMode(pin_vd, INPUT_PULLUP);
  game_state = false;
  vd_down = 0;

  pinMode(LED_BUILTIN, OUTPUT);

}

void loop() {
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
          start_game();
        else
          stop_game();
      }
    }
  }
  else {
    vd_down = 0;
    vd_up = true;
  }

  if (game_state)
  {
    bool all_states = true;
    
    for (int i = 0; i != n_players; ++i)
    {
      long int t = millis();
      if (!player_gs[i] && !digitalRead(players[i])){
        if (player_down[i] == 0)
          player_down[i] = t;
        else
          if (t - player_down[i] > min_down){
            Serial.print(players[i]);
            Serial.print(": ");
            Serial.println(t - t_start);
            player_gs[i] = true;
          }
      } else
        player_down[i] = 0;

      if (all_states && !player_gs[i])
        all_states = false;
    }

    if (all_states)
      stop_game();
  }
}

void start_game()
{
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("START");
  game_state = true;
  set_all_players(false);
  t_start = millis();
  delay(10);
}

void stop_game()
{
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("STOP");
  game_state = false;
  set_all_players(false);
  delay(10);
}

void set_all_players(bool state)
{
  for (int i = 0; i != n_players; ++i)
  {
    player_gs[i] = state;
    player_down[i] = 0;
  }
}
