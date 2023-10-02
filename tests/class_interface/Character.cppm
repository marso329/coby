// Character.cppm
export module Character;
import <string>;
import <iostream>;

// Definition
export class Character {
 public:
  Character(std::string Name);
  void SayHello();
  std::string GetName();

 private:
  std::string Name;
};