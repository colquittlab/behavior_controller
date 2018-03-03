#ifndef LIVEAUDIO_H
#define LIVEAUDIO_H

#include <QWidget>

namespace Ui {
class LiveAudio;
}

class LiveAudio : public QWidget
{
    Q_OBJECT

public:
    explicit LiveAudio(QWidget *parent = 0);
    ~LiveAudio();

private:
    Ui::LiveAudio *ui;
};

#endif // LIVEAUDIO_H
