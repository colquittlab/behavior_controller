#include "liveaudio.h"
#include "ui_liveaudio.h"

LiveAudio::LiveAudio(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::LiveAudio)
{
    ui->setupUi(this);
}

LiveAudio::~LiveAudio()
{
    delete ui;
}
