#include <QtWidgets/QApplication>
import MainWindow;
int main(int argc, char *argv[]) {

  QApplication app(argc, argv);
  MainWindow w;
  w.show();
  return app.exec();
}
