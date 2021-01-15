
const int programPin = 3; //VppHigh to eprom GVpp
const int readPin = 5;    //VppLow to eprom GVpp
const int enablePin = 34; //eprom E

const unsigned long romSize = 512 * 1024UL;

/*                  
 *Regular eprom pinout, uncommnet this one and comment the above                   
 *to burn regular eproms for use with other systems.
 *You may have to actually edit this for use with your console/8bit computer
 *The pinout from the eprom is different from the snes pinout
 */
int adrPins[16] = {
    33, //eprom A0
    35, //eprom A1
    37, //eprom A2
    39, //eprom A3
    41, //eprom A4
    43, //eprom A5
    45, //eprom A6
    47, //eprom A7
    44, //eprom A8
    42, //eprom A9
    36, //eprom A10
    40, //eprom A11
    49, //eprom A12
    46, //eprom A13
    48, //eprom A14
    51  //eprom A15
};

char dataPins[8] = {
    31, //eprom Q0
    29, //eprom Q1
    27, //eprom Q2
    24, //eprom Q3
    26, //eprom Q4
    28, //eprom Q5
    30, //eprom Q6
    32  //eprom Q7
};

byte inByte = 0;
unsigned int secH = 0, secL = 0;

void setup()
{
  pinMode(programPin, OUTPUT);
  pinMode(readPin, OUTPUT);
  pinMode(enablePin, OUTPUT);
  for (int i = 0; i < 20; i++)
  {
    pinMode(adrPins[i], OUTPUT);
  }
  digitalWrite(programPin, LOW);
  digitalWrite(readPin, LOW);
  digitalWrite(enablePin, HIGH);
  Serial.begin(250000);
  delay(1000);
  programMode();
}
int index = 0;
void loop()
{
  if (Serial.available())
  {
    inByte = Serial.read();
    if (inByte == 0x55)
    {
      while (Serial.available() == 0)
        ;
      inByte = Serial.read();
      switch (inByte)
      {
      case 'w':
        programMode();
        while (Serial.available() < 2)
          ;
        secH = Serial.read();
        secL = Serial.read();
        writeSector(secH, secL);
        break;
      case 'r':
        readMode();
        readROM();
        break;
      }
    }
  }
}

//low level functions, direct ccontact with hardware pins
void programMode()
{
  //data as output
  for (int i = 0; i < 8; i++)
  {
    pinMode(dataPins[i], OUTPUT);
  }
  digitalWrite(readPin, LOW);
  digitalWrite(programPin, HIGH);
}
void readMode()
{
  //data as input
  for (int i = 0; i < 8; i++)
  {
    pinMode(dataPins[i], INPUT);
  }
  digitalWrite(programPin, LOW);
  digitalWrite(readPin, LOW);
}
void setAddress(uint32_t Addr)
{
  for (int i = 0; i < 8; i++)
  {
    digitalWrite(adrPins[i], Addr & (1 << i));
  }
  Addr = Addr >> 8;
  for (int i = 0; i < 8; i++)
  {
    digitalWrite(adrPins[i + 8], Addr & (1 << i));
  }
  Addr = Addr >> 8;
  for (int i = 0; i < 4; i++)
  {
    digitalWrite(adrPins[i + 16], Addr & (1 << i));
  }
}
byte readByte(unsigned long adr)
{
  byte data;
  setAddress(adr);
  digitalWrite(enablePin, LOW);
  delayMicroseconds(1);
  for (int i = 7; i >= 0; i--)
  {
    data = data << 1;
    data |= digitalRead(dataPins[i]) & 1;
  }
  digitalWrite(enablePin, HIGH);
  return data;
}
void setData(char Data)
{
  for (int i = 0; i < 8; i++)
  {
    digitalWrite(dataPins[i], Data & (1 << i));
  }
}
void programByte(byte Data)
{
  setData(Data);
  //Vpp pulse
  delayMicroseconds(4);
  digitalWrite(enablePin, LOW);
  delayMicroseconds(60);
  digitalWrite(enablePin, HIGH);
}

void writeSector(unsigned char sectorH, unsigned char sectorL)
{
  byte dataBuffer[128];
  unsigned long address = 0;
  byte CHK = sectorH, CHKreceived;
  CHK ^= sectorL;

  address = sectorH;
  address = (address << 8) | sectorL;
  address *= 128;

  for (int i = 0; i < 128; i++)
  {
    while (Serial.available() == 0)
      ;
    dataBuffer[i] = Serial.read();
    CHK ^= dataBuffer[i];
  }
  while (Serial.available() == 0)
    ;
  CHKreceived = Serial.read();
  programMode();
  //only program the bytes if the checksum is equal to the one received
  if (CHKreceived == CHK)
  {
    for (int i = 0; i < 128; i++)
    {
      setAddress(address++);
      programByte(dataBuffer[i]);
    }
    Serial.write(CHK);
  }
  readMode();
}
int readROM()
{
  unsigned long num = 1024 * 1024UL;
  unsigned long address;
  byte data, checksum = 0;
  address = 0;
  //read mode
  readMode();
  //start frame
  digitalWrite(readPin, LOW);
  digitalWrite(programPin, LOW);
  for (long i; i < 1048576; i++)
  { //1048576
    data = readByte(address++);
    Serial.write(data);
    //checksum^=data;
  }
  digitalWrite(readPin, HIGH);

  //Serial.write(checksum);
  //Serial.write(0xAA);
}
