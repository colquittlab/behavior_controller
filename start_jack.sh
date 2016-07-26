#! /bin/sh

# Start mainserver
procs=`ps aux | grep /usr/bin/jackd`
if [ -z "$procs" ]
then
  echo "Starting main server..."
  /usr/bin/jackd -dalsa -dhw:0 -r44100 -p1024 -n2 -D -Chw:PCH
fi

#Start usb soundcards
#cards=('usbaudio_4' 'usbaudio_5')

while read sc ch
do
    pcm="hw:${sc},0"
    alsa_proc=`ps aux | grep alsa_in | grep "$sc"`
    echo -n "Starting ${sc}..."
    if [ -z "$alsa_proc" ]
	then
	alsa_in -j $pcm -d $pcm -c $ch -r 44100 >> "$sc"_alsa_in.log &
	echo "done."
    else 
	echo "${sc} already started."
    fi
done < usb_soundcards.txt
