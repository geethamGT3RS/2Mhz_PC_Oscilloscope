//////////////////////////////////////////////////////////////////////////////////////////////////
/*
Copyright 2021 Google LLC
Use of this source code is governed by an MIT-style
license that can be found in the LICENSE file or at
https://opensource.org/licenses/MIT.
*/
//////////////////////////////////////////////////////////////////////////////////////////////////


#include <wiringPi.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <signal.h>
#include <sys/time.h>
#include <time.h>

#define SCLK 0
#define SDATA 2
#define CS 3

volatile sig_atomic_t timer_expired = 0;

float t_sleep=100000;

    //  ADDED BY Geetham.GT3RS  //
    //     SET DELAY HERE       //

float TIME = 1;

void timer_handler(int signum) {
    timer_expired = 1;
}

void usleep_timer(unsigned int microseconds) {
    struct itimerval timer;
    struct sigaction sa;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sa.sa_handler = timer_handler;
    sigaction(SIGALRM, &sa, NULL);
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 0;
    timer.it_value.tv_sec = microseconds / 100000000000;
    timer.it_value.tv_usec = microseconds % 100000000000;
    setitimer(ITIMER_REAL, &timer, NULL);
    while (!timer_expired);
    timer_expired = 0;
}

void sleep_ns(long ns)
{
    struct timespec ts;
    ts.tv_sec = 0;
    ts.tv_nsec = ns;
    nanosleep(&ts, NULL);
}

int main(void) 
{
    
    if (wiringPiSetup() == -1) 
    {
        printf("Failed to initialize WiringPi\n");
        return 1;
    }
    //  ADDED BY Geetham.GT3RS  //
    //   SETUP GPIO PINS MODE   //

    pinMode(SCLK, OUTPUT);
    pinMode(SDATA, INPUT);
    pinMode(CS, OUTPUT);
    digitalWrite(CS, HIGH);

    //  ADDED BY Geetham.GT3RS  //
    //  SETUP PIPE FOR DATA TRANSFER TO SERVER   //
    
    const char *pipe_name = "/tmp/adc_data_pipe";
    mkfifo(pipe_name, 0666);
    int pipe_fd = open(pipe_name, O_WRONLY);
    if (pipe_fd == -1) 
    {
        printf("Failed to open the pipe for writing\n");
        return 1;
    }
    
    //  ADDED BY Geetham.GT3RS  //
    //  SET ADC TO NORMAL MODE  //
    
    for (int i = 0; i < 20; i++)
    {
        digitalWrite(CS, LOW);
        digitalWrite(SCLK, HIGH); 
        delayMicroseconds(TIME);
        digitalWrite(SCLK, LOW);
        delayMicroseconds(TIME);
    }
    
    //  ADDED BY Geetham.GT3RS  //
    //    START READING DATA    //
    
    while (1)
    {
        digitalWrite(CS, LOW);
        uint16_t data = 0;
        for (int i = 0; i < 14; i++) 
        {
            digitalWrite(SCLK, HIGH); 
            delayMicroseconds(TIME);
            
            
            digitalWrite(SCLK, LOW);
            delayMicroseconds(TIME);
            if (i > 2) 
            {
                data = data << 1;
                data = data | digitalRead(SDATA);
            } 
            else 
            {
                continue;
            }
        }
        digitalWrite(CS, HIGH);
        write(pipe_fd, &data, sizeof(uint16_t));
        delayMicroseconds(TIME);
    }

    close(pipe_fd);

    return 0;
}

