#include "Arduino.h"

const int VOORDRINK     = 22;
const int N_PLAYERS = 4;
const int PLAYERS[N_PLAYERS] = {46, 47, 48, 49};

bool player_gs[N_PLAYERS];
long int t_start;
bool game_state;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  for (int i = 0; i != N_PLAYERS; ++i)
  {
    pinMode(PLAYERS[i], INPUT_PULLUP);
    player_gs[i] = false;
  }
  
  pinMode(VOORDRINK, INPUT_PULLUP);
  game_state = false;

}

void loop() {
  // put your main code here, to run repeatedly:
  int bsVD = digitalRead(VOORDRINK);

  if (!game_state && !bsVD)
  {
    Serial.println("START");
    game_state = true;
    t_start = millis();
  }

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
      game_state = false;
      for (int i = 0; i != N_PLAYERS; ++i)
      {
        player_gs[i] = false;
      }
    }
  }
  delay(1);        // delay in between reads for stability
}
