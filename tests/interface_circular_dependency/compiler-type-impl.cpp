// compiler-type-impl.cc
module compiler:type;
import :decl;
Type::Type() {}
Type::~Type() {}
bool Type::IsFunction() { return true; }
