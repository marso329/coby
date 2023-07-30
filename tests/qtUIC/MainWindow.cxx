module;

#include  <QtCore/QObject>
#include <QtWidgets/QMainWindow>
import ui_mainwindow;

export module MainWindow;

export class MainWindow : public QMainWindow {
  Q_OBJECT
public:
  MainWindow(QWidget *parent = nullptr)
      : QMainWindow(parent) , ui( new Ui::MainWindow){
    ui->setupUi(this);
  }

  virtual ~MainWindow() {}

private:
  Ui::MainWindow *ui=nullptr;

protected:
Q_SIGNALS:

public Q_SLOTS:
};
