import os,sys,time
def main():
    if not sys.stdout.isatty() or os.environ.get('VIOLET_REDUCED_MOTION')=='1':return
    symbols=['◇','✧','✦','△','✦','✧']
    try:
        for symbol in symbols:
            sys.stdout.write('\r\033[38;2;197;180;255m   '+symbol+'  H Y R U L E  ·  Krallığa hoş geldin, Fatih\033[0m');sys.stdout.flush();time.sleep(.065)
    finally:sys.stdout.write('\r\033[2K');sys.stdout.flush()
if __name__=='__main__':main()
