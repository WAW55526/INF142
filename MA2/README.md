# How to run

1. In a terminal inside the MA2 folder run:   python tracker.py

2. In another terminal inside the MA2 folder run:   python peer.py [IP adress] [Local files]     (repeat for every peer)
For every new peer you add you need to give it a unique address and unique folder for It's local files.
I have already made 5 folders with some text files that can be used as local files.
If you want more than 5 peers running at the same time you need to create more folders.

--Example--
First peer: python peer.py "127.0.0.1" "Files1"
Second peer: python peer.py "127.0.0.2" "Files2"
Third peer: python peer.py "127.0.0.3" "Files3"
etc.
