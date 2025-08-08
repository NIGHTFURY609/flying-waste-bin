/*
  Waste Bin Motor Controller
  
  This Arduino sketch receives commands from the computer via serial communication
  and controls motors to move the waste bin left, right, or keep it stationary.
  
  Hardware connections:
  - Motor Driver (L298N recommended):
    - ENA (Enable A) -> Pin 9 (PWM)
    - IN1 -> Pin 7
    - IN2 -> Pin 6
    - ENB (Enable B) -> Pin 10 (PWM)
    - IN3 -> Pin 5
    - IN4 -> Pin 4
  
  - Motors:
    - Left Motor -> Motor A terminals
    - Right Motor -> Motor B terminals
  
  Commands received:
  - 'L' = Move Left
  - 'R' = Move Right  
  - 'S' = Stay/Stop
*/

// Motor A (Left Motor) pins
const int motorA_EN = 9;   // PWM pin for speed control
const int motorA_IN1 = 7;
const int motorA_IN2 = 6;

// Motor B (Right Motor) pins  
const int motorB_EN = 10;  // PWM pin for speed control
const int motorB_IN3 = 5;
const int motorB_IN4 = 4;

// LED pin for status indication (built-in LED)
const int statusLED = 13;

// Motor speed (0-255)
const int motorSpeed = 150;  // Adjust this value based on your motors

// Movement duration (milliseconds)
const int movementDuration = 500;  // How long to move when command is received

// Variables
char receivedCommand = 'S';
unsigned long lastCommandTime = 0;
bool isMoving = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Set motor pins as outputs
  pinMode(motorA_EN, OUTPUT);
  pinMode(motorA_IN1, OUTPUT);
  pinMode(motorA_IN2, OUTPUT);
  pinMode(motorB_EN, OUTPUT);
  pinMode(motorB_IN3, OUTPUT);
  pinMode(motorB_IN4, OUTPUT);
  
  // Set LED pin as output
  pinMode(statusLED, OUTPUT);
  
  // Stop all motors initially
  stopMotors();
  
  // Blink LED to indicate ready
  for(int i = 0; i < 3; i++) {
    digitalWrite(statusLED, HIGH);
    delay(200);
    digitalWrite(statusLED, LOW);
    delay(200);
  }
  
  Serial.println("Waste Bin Controller Ready!");
  Serial.println("Commands: L=Left, R=Right, S=Stop");
}

void loop() {
  // Check for incoming serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    // Process valid commands
    if (command == 'L' || command == 'R' || command == 'S') {
      receivedCommand = command;
      lastCommandTime = millis();
      isMoving = true;
      
      // Execute the command
      executeCommand(receivedCommand);
      
      // Send confirmation back to computer
      Serial.print("Executing: ");
      Serial.println(getCommandName(receivedCommand));
      
      // Blink LED to indicate command received
      digitalWrite(statusLED, HIGH);
      delay(50);
      digitalWrite(statusLED, LOW);
    }
  }
  
  // Auto-stop after movement duration
  if (isMoving && (millis() - lastCommandTime > movementDuration)) {
    stopMotors();
    isMoving = false;
  }
  
  // Small delay to prevent overwhelming the serial buffer
  delay(10);
}

void executeCommand(char command) {
  switch(command) {
    case 'L':
      moveLeft();
      break;
    case 'R':
      moveRight();
      break;
    case 'S':
      stopMotors();
      break;
    default:
      stopMotors();
      break;
  }
}

void moveLeft() {
  // To move left, we might want to move the left motor backward and right motor forward
  // or both motors in same direction depending on your mechanical setup
  
  // Option 1: Differential steering (tank-like movement)
  // Left motor backward, right motor forward
  digitalWrite(motorA_IN1, LOW);
  digitalWrite(motorA_IN2, HIGH);
  analogWrite(motorA_EN, motorSpeed);
  
  digitalWrite(motorB_IN3, HIGH);
  digitalWrite(motorB_IN4, LOW);
  analogWrite(motorB_EN, motorSpeed);
  
  // Option 2: If you have wheels that move the bin sideways:
  // Uncomment the lines below and comment the lines above
  /*
  digitalWrite(motorA_IN1, HIGH);
  digitalWrite(motorA_IN2, LOW);
  analogWrite(motorA_EN, motorSpeed);
  
  digitalWrite(motorB_IN3, HIGH);
  digitalWrite(motorB_IN4, LOW);
  analogWrite(motorB_EN, motorSpeed);
  */
}

void moveRight() {
  // To move right, opposite of moveLeft()
  
  // Option 1: Differential steering
  // Left motor forward, right motor backward
  digitalWrite(motorA_IN1, HIGH);
  digitalWrite(motorA_IN2, LOW);
  analogWrite(motorA_EN, motorSpeed);
  
  digitalWrite(motorB_IN3, LOW);
  digitalWrite(motorB_IN4, HIGH);
  analogWrite(motorB_EN, motorSpeed);
  
  // Option 2: Sideways movement
  // Uncomment and modify as needed
  /*
  digitalWrite(motorA_IN1, LOW);
  digitalWrite(motorA_IN2, HIGH);
  analogWrite(motorA_EN, motorSpeed);
  
  digitalWrite(motorB_IN3, LOW);
  digitalWrite(motorB_IN4, HIGH);
  analogWrite(motorB_EN, motorSpeed);
  */
}

void stopMotors() {
  // Stop both motors
  digitalWrite(motorA_IN1, LOW);
  digitalWrite(motorA_IN2, LOW);
  analogWrite(motorA_EN, 0);
  
  digitalWrite(motorB_IN3, LOW);
  digitalWrite(motorB_IN4, LOW);
  analogWrite(motorB_EN, 0);
}

String getCommandName(char command) {
  switch(command) {
    case 'L': return "Move Left";
    case 'R': return "Move Right";
    case 'S': return "Stop";
    default: return "Unknown";
  }
}

// Optional: Function to test motors (call this in setup() to test)
void testMotors() {
  Serial.println("Testing motors...");
  
  Serial.println("Moving left...");
  moveLeft();
  delay(1000);
  
  Serial.println("Stopping...");
  stopMotors();
  delay(500);
  
  Serial.println("Moving right...");
  moveRight();
  delay(1000);
  
  Serial.println("Stopping...");
  stopMotors();
  delay(500);
  
  Serial.println("Motor test complete!");
}
