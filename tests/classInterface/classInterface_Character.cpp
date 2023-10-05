// Character.cpp
module classInterface.Character;
import <string>;
import <iostream>;

Character::Character(std::string Name)
    : Name{Name} {}

void Character::SayHello() {
  std::cout << "Hello there!  The name is "
            << Name<<std::endl;
}

std::string Character::GetName() {
  return Name;
}