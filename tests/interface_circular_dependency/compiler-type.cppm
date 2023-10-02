// compiler-type.cc
export module compiler:type;
export class Decl; // forward declaration
export class Type {
public:
  Type();
  ~Type();
  bool isFunction();
  Decl *name; // name of the type
              // other members
};
