#include "Arduino.h"
#include "HardwareSerial.h"

const int VOORDRINK     = 22;
const int N_PLAYERS = 4;
const int PLAYERS[N_PLAYERS] = {46, 47, 48, 49};

bool player_gs[N_PLAYERS];
long int t_start;
bool game_state;
bool voordrink_released = true;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  for (int i = 0; i != N_PLAYERS; ++i)
  {
    pinMode(PLAYERS[i], INPUT_PULLUP);
  }

  set_all_players(false);
  
  pinMode(VOORDRINK, INPUT_PULLUP);
  game_state = false;

  pinMode(LED_BUILTIN, OUTPUT);

}

void loop() {
  if (!digitalRead(VOORDRINK))
  {
    if (voordrink_released)
    {
      if (!game_state)
        start_game();
      else
        stop_game();
    }
    
    voordrink_released = false;
    
  }
  else
    voordrink_released = true;

  if (game_state)
  {
    bool all_states = true;
    for (int i = 0; i != N_PLAYERS; ++i)
    {
      if (!digitalRead(PLAYERS[i]) && !player_gs[i])
      {
        Serial.print(i);
        Serial.print(": ");
        Serial.println(millis() - t_start);
        player_gs[i] = true;
      }

      if (all_states && !player_gs[i])
      {
        all_states = false;
      }
    }

    if (all_states)
    {
      stop_game();
    }
  }
  delay(1);        // delay in between reads for stability
}

void start_game()
{
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("START");
  game_state = true;
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
  for (int i = 0; i != N_PLAYERS; ++i)
  {
    player_gs[i] = state;
  }
}

