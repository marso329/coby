export module D:B;

import <string>;
import <cassert>;
import :C;

export class B{
 public:
 B(){
    C test();

}
~B(){}
std::string print(){
    return "hello world";
}

};