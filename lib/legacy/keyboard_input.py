import sys, tty, termios, time  

def getch(): 
    import ipdb; ipdb.set_trace(); 
    fd = sys.stdin.fileno() 
    old_settings = termios.tcgetattr(fd) 
    try:
        tty.setraw(fd) 
        import ipdb; ipdb.set_trace(); 
        ch = sys.stdin.read()
    finally: 
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return ch


def get_input():
    # data = sys.stdin.read()
    time.sleep(1)
    data =  sys.stdin.fileno()
    return data


if __name__ == '__main__':
    test = True
    while test:
        print time.time()
        ch = get_input()
        print ch
        if ch =='q':
            break